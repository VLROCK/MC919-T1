"""Ganhos escalares globais em log, ancorados em uma câmera."""
import cv2
import numpy as np


def compensate(frames, ids, edges, root):
    lookup = {i: k for k, i in enumerate(ids)}
    rows, targets = [], []
    for e in edges:
        # Médias locais são menos sensíveis ao deslocamento subpixel do keypoint.
        values = []
        for i, pts in ((e.i, e.a), (e.j, e.b)):
            gray = cv2.cvtColor(frames[i].image, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (9, 9), 0).astype(np.float32)
            values.append(cv2.remap(gray, pts[:, 0].astype(np.float32).reshape(-1, 1),
                                    pts[:, 1].astype(np.float32).reshape(-1, 1),
                                    cv2.INTER_LINEAR).ravel())
        a, b = values
        good = (a > 15) & (b > 15) & (a < 240) & (b < 240)
        if good.sum() < 8:
            continue
        row = np.zeros(len(ids))
        row[lookup[e.i]], row[lookup[e.j]] = 1, -1
        rows.append(row)
        targets.append(float(np.median(np.log(b[good]/a[good]))))
    anchor = np.zeros(len(ids))
    anchor[lookup[root]] = 1
    rows.append(anchor)
    targets.append(0.)
    gains = np.exp(np.linalg.lstsq(np.array(rows), targets, rcond=None)[0])
    return {i: float(np.clip(gains[k], .4, 2.5)) for i, k in lookup.items()}
