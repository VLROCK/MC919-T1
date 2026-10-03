from types import SimpleNamespace
import numpy as np
import pytest
from panorama.blend import blend_pair


@pytest.mark.parametrize("method", ["feather", "multiband"])
def test_deghost_does_not_mix_moving_region(method):
    a = np.full((100, 150, 3), 120, np.float32)
    b = a.copy()
    b[30:70, 60:90] = 240
    mask = np.ones(a.shape[:2], bool)
    args = SimpleNamespace(full_360=False, ghost_threshold=25, ghost_dilate=3,
                           ghost_min_area=10, blend=method, bands=4)
    naive, _, _, _ = blend_pair(a, b, mask, mask, args, False)
    clean, changed, _, _ = blend_pair(a, b, mask, mask, args, True)
    assert 120 < naive[50, 75, 0] < 240
    np.testing.assert_allclose(clean[40:60, 65:85], 120)
    assert changed[50, 75] == 255


def test_black_pixels_are_valid_and_no_overlap_preserved():
    a = np.zeros((20, 40, 3), np.float32)
    b = np.full_like(a, 200)
    ma, mb = np.zeros((20, 40), bool), np.zeros((20, 40), bool)
    ma[:, :20], mb[:, 20:] = True, True
    args = SimpleNamespace(full_360=False, blend="feather")
    image, _, _, _ = blend_pair(a, b, ma, mb, args, False)
    assert (image[:, :20] == 0).all() and (image[:, 20:] == 200).all()
