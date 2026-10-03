"""Convenções geométricas e operações pequenas compartilhadas."""
import numpy as np


def project(H, points):
    q = np.column_stack([points, np.ones(len(points))]) @ H.T
    z = q[:, 2:3]
    z = np.where(np.abs(z) < 1e-9, np.where(z < 0, -1e-9, 1e-9), z)
    return q[:, :2] / z


def intrinsic(frame, focal_factor):
    h, w = frame.image.shape[:2]
    return np.array([[focal_factor * w, 0, (w - 1) / 2],
                     [0, focal_factor * w, (h - 1) / 2], [0, 0, 1.]])


def rotation_from_homography(H, Ki, Kj):
    M = np.linalg.inv(Kj) @ H @ Ki
    if np.linalg.det(M) < 0:
        M = -M
    u, _, vt = np.linalg.svd(M)
    return u @ np.diag([1, 1, np.linalg.det(u @ vt)]) @ vt


def corners(frame):
    h, w = frame.image.shape[:2]
    return np.float64([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]])
