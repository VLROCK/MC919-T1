"""Feathering/multibanda e deghosting por seleção coerente de fonte."""
import cv2
import numpy as np


def distance(mask, wrap=False):
    src = mask.astype(np.uint8)
    if wrap:
        w = src.shape[1]
        src = np.tile(src, (1, 3))
    # Padding garante distância finita mesmo com máscara toda válida.
    d = cv2.distanceTransform(np.pad(src, 1), cv2.DIST_L2, 3)[1:-1, 1:-1]
    return d[:, w:2*w] if wrap else d


def multiband(a, b, alpha, levels):
    ga, gb, gm = [a], [b], [alpha]
    for _ in range(levels-1):
        if min(ga[-1].shape[:2]) < 8:
            break
        ga.append(cv2.pyrDown(ga[-1]))
        gb.append(cv2.pyrDown(gb[-1]))
        gm.append(cv2.pyrDown(gm[-1]))
    result = ga[-1]*gm[-1][..., None] + gb[-1]*(1-gm[-1][..., None])
    for k in range(len(ga)-2, -1, -1):
        size = ga[k].shape[1], ga[k].shape[0]
        la = ga[k]-cv2.pyrUp(ga[k+1], dstsize=size)
        lb = gb[k]-cv2.pyrUp(gb[k+1], dstsize=size)
        result = cv2.pyrUp(result, dstsize=size) + la*gm[k][..., None]+lb*(1-gm[k][..., None])
    return result


def blend_pair(a, b, ma, mb, args, deghost):
    overlap = ma & mb
    da, db = distance(ma, args.full_360), distance(mb, args.full_360)
    alpha = da/np.maximum(da+db, 1e-6)
    changed = np.zeros(ma.shape, np.uint8)
    ownership = np.zeros(ma.shape, bool)
    diff = np.mean(np.abs(a-b), axis=2)
    if deghost and overlap.any():
        suspect = ((diff > args.ghost_threshold) & overlap).astype(np.uint8)
        kernel = np.ones((args.ghost_dilate*2+1, args.ghost_dilate*2+1), np.uint8)
        suspect = cv2.dilate(suspect, kernel) * overlap.astype(np.uint8)
        count, labels, stats, _ = cv2.connectedComponentsWithStats(suspect)
        for label in range(1, count):
            if stats[label, cv2.CC_STAT_AREA] < args.ghost_min_area:
                continue
            region = labels == label
            # Uma fonte para todo o componente, não uma mediana translúcida de duas vistas.
            use_old = float(da[region].mean()) >= float(db[region].mean())
            alpha[region] = float(use_old)
            ownership[region] = use_old
            changed[region] = 255
    if args.blend == "multiband":
        # Preenche pixels inválidos com a outra fonte antes de construir pirâmides.
        aa, bb = a.copy(), b.copy()
        aa[~ma], bb[~mb] = b[~ma], a[~mb]
        if args.full_360:
            pad = min(a.shape[1], 2**(args.bands+1))
            result = multiband(np.pad(aa, ((0, 0), (pad, pad), (0, 0)), mode="wrap"),
                               np.pad(bb, ((0, 0), (pad, pad), (0, 0)), mode="wrap"),
                               np.pad(alpha, ((0, 0), (pad, pad)), mode="wrap"), args.bands)[:, pad:-pad]
        else:
            result = multiband(aa, bb, alpha, args.bands)
    else:
        result = a*alpha[..., None] + b*(1-alpha[..., None])
    if deghost:
        # Nem as baixas frequências voltam a misturar conteúdo incompatível.
        selected = changed > 0
        result[selected & ownership] = a[selected & ownership]
        result[selected & ~ownership] = b[selected & ~ownership]
    result[ma & ~mb], result[mb & ~ma] = a[ma & ~mb], b[mb & ~ma]
    result[~(ma | mb)] = 0
    return result, changed, diff, overlap
