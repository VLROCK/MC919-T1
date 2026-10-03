"""Detectores, BF, ratio de Lowe e validação geométrica de todos os pares."""
from dataclasses import dataclass
from itertools import combinations
from time import perf_counter

import cv2
import numpy as np

from .io import save_image
from .geometry import project


@dataclass
class Features:
    keypoints: list
    descriptors: np.ndarray | None
    seconds: float


@dataclass
class Edge:
    i: int
    j: int
    H: np.ndarray  # pixel i -> pixel j
    a: np.ndarray  # inliers na imagem i
    b: np.ndarray  # inliers na imagem j
    stats: dict


def extract(frames, detector, nfeatures, output=None):
    maker = {"sift": lambda: cv2.SIFT_create(nfeatures=nfeatures),
             "orb": lambda: cv2.ORB_create(nfeatures=nfeatures),
             "akaze": cv2.AKAZE_create}[detector]()
    result = []
    for i, frame in enumerate(frames):
        start = perf_counter()
        kp, desc = maker.detectAndCompute(cv2.cvtColor(frame.image, cv2.COLOR_BGR2GRAY), None)
        result.append(Features(kp, desc, perf_counter() - start))
        if output:
            picture = cv2.drawKeypoints(frame.image, kp, None,
                                       flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS)
            save_image(output / "keypoints" / detector / f"{i:03}.jpg", picture)
    return result


def match_all(frames, features, args, output=None):
    norm = cv2.NORM_L2 if args.detector == "sift" else cv2.NORM_HAMMING
    matcher = cv2.BFMatcher(norm)
    edges, records = [], []
    matrix = np.zeros((len(frames), len(frames)), dtype=int)
    for i, j in combinations(range(len(frames)), 2):
        fi, fj = features[i], features[j]
        row = dict(i=i, j=j, candidates=0, ratio_matches=0, inliers=0,
                   inlier_rate=0., mean_reprojection_px=None, symmetric_rmse_px=None,
                   accepted=False, reason="descritores insuficientes")
        records.append(row)
        if fi.descriptors is None or fj.descriptors is None or len(fj.descriptors) < 2:
            continue
        knn = matcher.knnMatch(fi.descriptors, fj.descriptors, k=2)
        before = [m[0] for m in knn if m]
        good = [m[0] for m in knn if len(m) == 2 and m[0].distance < args.ratio * m[1].distance]
        # Evita que várias origens votem no mesmo destino.
        unique = {}
        for m in sorted(good, key=lambda m: m.distance):
            unique.setdefault(m.trainIdx, m)
        good = list(unique.values())
        row.update(candidates=len(before), ratio_matches=len(good), reason="poucos matches")
        if output:
            for name, matches in (("before", before), ("ratio", good)):
                view = cv2.drawMatches(frames[i].image, fi.keypoints, frames[j].image,
                                       fj.keypoints, matches[:args.draw_matches], None,
                                       flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
                save_image(output / "matches" / f"{i:03}_{j:03}_{name}.jpg", view)
        if len(good) < 4:
            continue
        a = np.float64([fi.keypoints[m.queryIdx].pt for m in good])
        b = np.float64([fj.keypoints[m.trainIdx].pt for m in good])
        H, mask = cv2.findHomography(a, b, cv2.RANSAC, args.ransac,
                                     maxIters=5000, confidence=.999)
        if H is None or mask is None or not np.isfinite(H).all():
            row["reason"] = "RANSAC sem modelo"
            continue
        try:
            back = project(np.linalg.inv(H), b)
        except (np.linalg.LinAlgError, ValueError):
            row["reason"] = "homografia singular"
            continue
        forward = np.linalg.norm(project(H, a) - b, axis=1)
        reverse = np.linalg.norm(back - a, axis=1)
        keep = mask.ravel().astype(bool) & (reverse <= args.ransac * 2)
        count = int(keep.sum())
        matrix[i, j] = matrix[j, i] = count
        row.update(inliers=count, inlier_rate=count / len(good))
        if count:
            row.update(mean_reprojection_px=float(forward[keep].mean()),
                       symmetric_rmse_px=float(np.sqrt(np.mean(
                           (forward[keep] ** 2 + reverse[keep] ** 2) / 2))))
        # Rejeita consensos restritos a uma linha ou a um objeto pequeno.
        coverage = []
        for pts, f in ((a[keep], frames[i]), (b[keep], frames[j])):
            area = cv2.contourArea(cv2.convexHull(pts.astype(np.float32))) if len(pts) >= 3 else 0
            coverage.append(area / np.prod(f.image.shape[:2]))
        row["coverage"] = min(coverage)
        accepted = (count >= args.min_inliers and row["inlier_rate"] >= args.min_inlier_ratio
                    and min(coverage) >= args.min_coverage)
        row.update(accepted=accepted, reason="aceito" if accepted else "consenso insuficiente")
        if accepted:
            edges.append(Edge(i, j, H / H[2, 2], a[keep], b[keep], row))
        if output:
            matches = [m for m, valid in zip(good, keep) if valid]
            view = cv2.drawMatches(frames[i].image, fi.keypoints, frames[j].image,
                                   fj.keypoints, matches[:args.draw_matches], None,
                                   flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS)
            save_image(output / "matches" / f"{i:03}_{j:03}_inliers.jpg", view)
    return edges, records, matrix
