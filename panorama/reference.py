"""Referência pronta isolada do pipeline autoral."""
from time import perf_counter
import cv2
from .io import save_image


def stitch_reference(frames, ids, output):
    start = perf_counter()
    stitcher = cv2.Stitcher_create(cv2.Stitcher_PANORAMA)
    try:
        status, pano = stitcher.stitch([frames[i].image for i in ids])
        info = dict(status=int(status), success=status == cv2.Stitcher_OK,
                    seconds=perf_counter()-start, input_indices=ids,
                    status_legend={0: "OK", 1: "NEED_MORE_IMGS", 2: "HOMOGRAPHY_EST_FAIL",
                                   3: "CAMERA_PARAMS_ADJUST_FAIL"})
        if info["success"]:
            save_image(output / "panorama.png", pano)
            info["size"] = list(pano.shape[:2])
        return info
    except cv2.error as e:
        return dict(success=False, error=str(e), seconds=perf_counter()-start, input_indices=ids)
