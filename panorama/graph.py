"""Componente dominante, árvore máxima e ordem espacial independente dos nomes."""
import numpy as np
from .geometry import intrinsic, project, rotation_from_homography


def component(n, edges):
    adjacency = {i: set() for i in range(n)}
    for e in edges:
        adjacency[e.i].add(e.j)
        adjacency[e.j].add(e.i)
    groups, unseen = [], set(range(n))
    while unseen:
        todo, group = [min(unseen)], set()
        while todo:
            i = todo.pop()
            if i not in group:
                group.add(i)
                todo.extend(adjacency[i] - group)
        unseen -= group
        groups.append(sorted(group))
    groups.sort(key=lambda g: (len(g), sum(len(adjacency[i]) for i in g)), reverse=True)
    if len(groups[0]) < 2:
        raise ValueError("Nenhum par confiável. Confira textura/sobreposição ou os limiares.")
    if len(groups) > 1 and len(groups[0]) == len(groups[1]):
        raise ValueError("Duas cenas têm o mesmo número de imagens; separe as cenas em pastas.")
    return groups[0], [i for group in groups[1:] for i in group]


def initialize(ids, edges, frames, projection, focal_factor):
    # Raiz de maior conectividade, reduzindo a profundidade do encadeamento.
    root = max(ids, key=lambda i: sum(e.stats["inliers"] for e in edges if i in (e.i, e.j)))
    transforms, tree = {root: np.eye(3)}, []
    while len(transforms) < len(ids):
        candidates = [e for e in edges if (e.i in transforms) != (e.j in transforms)]
        if not candidates:
            raise ValueError("Grafo desconectado durante alinhamento.")
        e = max(candidates, key=lambda e: e.stats["inliers"])
        known, new = (e.i, e.j) if e.i in transforms else (e.j, e.i)
        H = e.H if known == e.i else np.linalg.inv(e.H)  # known -> new
        if projection == "planar":
            T = transforms[known] @ np.linalg.inv(H)
            transforms[new] = T / T[2, 2]
        else:
            relative = rotation_from_homography(H, intrinsic(frames[known], focal_factor),
                                                intrinsic(frames[new], focal_factor))
            transforms[new] = transforms[known] @ relative.T  # camera -> mundo
        tree.append((known, new))
    return transforms, root, tree


def infer_order(ids, transforms, frames, projection):
    if projection == "planar":
        centers = np.array([project(transforms[i], np.array([[(frames[i].image.shape[1]-1)/2,
                            (frames[i].image.shape[0]-1)/2]]))[0] for i in ids])
        _, _, vt = np.linalg.svd(centers - centers.mean(axis=0), full_matrices=False)
        axis = vt[0]
        if axis[np.argmax(np.abs(axis))] < 0:
            axis = -axis
        return [ids[k] for k in np.argsort(centers @ axis)]
    yaw = np.array([np.arctan2(transforms[i][0, 2], transforms[i][2, 2]) for i in ids])
    indices = np.argsort(yaw)
    ordered = yaw[indices]
    gaps = np.diff(np.r_[ordered, ordered[0] + 2 * np.pi])
    # Abre o ciclo no maior intervalo angular sem centros de câmera.
    indices = np.roll(indices, -int(np.argmax(gaps)) - 1)
    return [ids[k] for k in indices]


def consistent_edges(edges, tree, transforms, frames, projection, focal, threshold):
    """Remove atalhos contraditórios; mantém a árvore que ancora a componente."""
    tree_keys = {frozenset(pair) for pair in tree}
    kept, rejected = [], []
    for e in edges:
        if projection == "planar":
            H = np.linalg.solve(transforms[e.j], transforms[e.i])
        else:
            H = intrinsic(frames[e.j], focal) @ transforms[e.j].T @ transforms[e.i]
            H = H @ np.linalg.inv(intrinsic(frames[e.i], focal))
        err = float(np.median(np.linalg.norm(project(H, e.a)-e.b, axis=1)))
        e.stats["tree_consistency_median_px"] = err
        use = frozenset((e.i, e.j)) in tree_keys or err <= threshold
        e.stats["used_for_alignment"] = use
        if use:
            kept.append(e)
        else:
            rejected.append(dict(i=e.i, j=e.j, median_px=err,
                                 reason="atalho inconsistente com a árvore de maior confiança"))
    return kept, rejected
