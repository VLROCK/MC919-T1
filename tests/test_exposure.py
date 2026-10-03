import numpy as np
from panorama.exposure import compensate
from panorama.features import Edge
from panorama.io import Frame


def test_gain_recovers_brightness_ratio():
    frames = [Frame("a", np.full((100, 100, 3), 100, np.uint8), 1),
              Frame("b", np.full((100, 100, 3), 150, np.uint8), 1)]
    pts = np.array([[x, y] for x in (20, 40, 60, 80) for y in (20, 40, 60, 80)], float)
    edge = Edge(0, 1, np.eye(3), pts, pts.copy(), dict(inliers=16))
    gain = compensate(frames, [0, 1], [edge], 0)
    assert abs(gain[0]-1) < 1e-6
    assert abs(gain[1]-2/3) < 1e-6
