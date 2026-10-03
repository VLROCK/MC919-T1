from types import SimpleNamespace
import numpy as np
import pytest
from scipy.spatial.transform import Rotation
from panorama.geometry import project, intrinsic
from panorama.features import Edge
from panorama.graph import component, initialize, consistent_edges
from panorama.io import Frame
from panorama.optimize import bundle
from panorama.warp import Canvas, warp_frame, make_canvas


def test_project_and_inverse():
    H = np.array([[1.1, .1, 40], [-.1, .9, 10], [.001, 0, 1]])
    pts = np.array([[20, 30], [180, 150], [22, 230.]])
    np.testing.assert_allclose(project(np.linalg.inv(H), project(H, pts)), pts, atol=1e-9)


def test_bundle_rotation_improves_noisy_initialization():
    rng = np.random.default_rng(4)
    frames = [Frame(str(i), np.zeros((300, 400, 3), np.uint8), 1) for i in range(3)]
    truth = {i: Rotation.from_euler("y", i*12, degrees=True).as_matrix() for i in range(3)}
    K = intrinsic(frames[0], .8)
    edges = []
    for i, j in [(0, 1), (1, 2), (0, 2)]:
        a = rng.uniform([170, 60], [360, 240], (60, 2))
        H = K @ truth[j].T @ truth[i] @ np.linalg.inv(K)
        b = project(H, a)+rng.normal(0, .1, a.shape)
        edges.append(Edge(i, j, H, a, b, dict(inliers=60)))
    initial = {i: Rotation.from_euler("y", i*13, degrees=True).as_matrix() for i in range(3)}
    args = SimpleNamespace(projection="spherical", focal_factor=.85, ba_points=100,
                           ba_iterations=100, ransac=3)
    _, focal, info = bundle(initial, 0, edges, frames, args)
    assert info["accepted"]
    assert info["final_rmse_px"] < info["initial_rmse_px"] / 10
    assert abs(focal-.8) < .03


def test_intruder_and_transform_direction():
    frames = [Frame(str(i), np.zeros((100, 100, 3), np.uint8), 1) for i in range(3)]
    H = np.array([[1., 0, -50], [0, 1, 0], [0, 0, 1]])
    e = Edge(0, 1, H, np.empty((0, 2)), np.empty((0, 2)), dict(inliers=30))
    ids, rejected = component(3, [e])
    assert ids == [0, 1] and rejected == [2]
    ts, _, _ = initialize(ids, [e], frames, "planar", .9)
    np.testing.assert_allclose(project(ts[0], np.array([[70., 40]])),
                               project(ts[1], np.array([[20., 40]])))


def test_spherical_wrap_renders_both_ends():
    frame = Frame("black", np.zeros((80, 100, 3), np.uint8), 1)
    canvas = Canvas(628, 100, -314, -50, 628/(2*np.pi), 0, True)
    R = Rotation.from_euler("y", 180, degrees=True).as_matrix()
    _, mask = warp_frame(frame, R, canvas, "spherical", .9)
    assert mask[:, 0].any() and mask[:, -1].any()
    assert not mask[:, 314].any()  # raios atrás da câmera não são aceitos


def test_false_loop_edge_is_not_used_in_bundle():
    frames = [Frame(str(i), np.zeros((200, 300, 3), np.uint8), 1) for i in range(3)]
    transforms = {i: np.array([[1., 0, i*100], [0, 1, 0], [0, 0, 1]]) for i in range(3)}
    points = np.array([[210., 20], [250, 40], [230, 80], [270, 120]])
    edges = [Edge(0, 1, np.eye(3), points, points-[100, 0], dict(inliers=100)),
             Edge(1, 2, np.eye(3), points, points-[100, 0], dict(inliers=100)),
             Edge(0, 2, np.eye(3), points, points.copy(), dict(inliers=20))]
    kept, rejected = consistent_edges(edges, [(0, 1), (1, 2)], transforms, frames, "planar", .9, 30)
    assert len(kept) == 2 and len(rejected) == 1
    assert rejected[0]["median_px"] == 200


def test_planar_horizon_is_rejected_with_actionable_message():
    frame = Frame("wide.jpg", np.zeros((100, 100, 3), np.uint8), 1)
    H = np.array([[1., 0, 0], [0, 1, 0], [-.02, 0, 1]])
    args = SimpleNamespace(projection="planar", max_megapixels=12)
    with pytest.raises(ValueError, match="--projection cylindrical --alignment bundle"):
        make_canvas([frame], {0: H}, [0], args, .9)
