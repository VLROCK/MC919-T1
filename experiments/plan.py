"""Plano pré-definido: uma alteração por vez em relação à base."""
from pathlib import Path
import hashlib
import json
import shutil
import cv2
import numpy as np
from panorama.io import read_frames, save_image, save_json


BASE = dict(projection="cylindrical", alignment="bundle", exposure="gain", blend="feather",
            detector="sift", max_side=600, nfeatures=2500, ratio=.75, ransac=3.,
            ba_points=100, ba_iterations=100, focal_factor=.9, seed=42,
            deghost="inconsistency", ghost_threshold=30, ghost_dilate=5, bands=5,
            diagnostics="compact", max_megapixels=8)


def variants():
    rows = [("base", "base", {})]
    groups = {
        "detector": [("orb", dict(detector="orb")), ("akaze", dict(detector="akaze"))],
        "ratio": [("060", dict(ratio=.60)), ("085", dict(ratio=.85))],
        "ransac": [("15", dict(ransac=1.5)), ("60", dict(ransac=6.))],
        "features": [("1000", dict(nfeatures=1000)), ("5000", dict(nfeatures=5000))],
        "resolution": [("400", dict(max_side=400, ransac=2.)),
                       ("900", dict(max_side=900, ransac=4.5))],
        "alignment": [("pairwise", dict(alignment="pairwise"))],
        "projection": [("spherical", dict(projection="spherical")),
                       ("planar_bundle", dict(projection="planar")),
                       ("planar_pairwise", dict(projection="planar", alignment="pairwise"))],
        "exposure": [("none", dict(exposure="none"))],
        "blend": [("bands3", dict(blend="multiband", bands=3)),
                  ("bands5", dict(blend="multiband", bands=5))],
        "deghost": [("none", dict(deghost="none")), ("15", dict(ghost_threshold=15)),
                    ("60", dict(ghost_threshold=60))],
        "focal": [("060", dict(focal_factor=.6)), ("120", dict(focal_factor=1.2))],
        "seed": [("7", dict(seed=7)), ("101", dict(seed=101))],
    }
    for group, options in groups.items():
        rows.extend((f"{group}_{name}", group, config) for name, config in options)
    return rows


def inventory(folder):
    return [{"file": p.name, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
            for p in sorted(Path(folder).iterdir()) if p.suffix.lower() in {".jpg", ".jpeg", ".png"}]


def prepare():
    datasets = {"quintal": "data/minha_cena", "boat5": "data/benchmark_boat5"}
    stress = Path("data/benchmark_boat5_exposure")
    if not stress.exists():
        stress.mkdir()
        gains = [.65, 1.2, .8, 1.1, .7]
        frames = read_frames(datasets["boat5"], 10000)
        for frame, gain in zip(frames, gains):
            save_image(stress/(Path(frame.name).stem+".png"), frame.image.astype(float)*gain)
        save_json(stress/"manifest.json", dict(derived_from=datasets["boat5"],
                    purpose="Perturbação fotométrica artificial; não são novas capturas",
                    source_files=[f.name for f in frames], gains=gains, clipping=True))
    shuffled = Path("data/quintal_shuffled")
    if not shuffled.exists():
        shuffled.mkdir()
        images = inventory(datasets["quintal"])
        permutation = np.random.default_rng(203).permutation(len(images))
        mapping = {}
        for i, entry in enumerate(images):
            name = f"foto_{permutation[i]:03}"+Path(entry["file"]).suffix
            shutil.copy2(Path(datasets["quintal"])/entry["file"], shuffled/name)
            mapping[name] = entry["file"]
        save_json(shuffled/"manifest.json", dict(original_names=mapping,
                                                 note="Apenas nomes alterados; bytes idênticos."))
    return datasets, stress, shuffled


def make_plan():
    datasets, stress, shuffled = prepare()
    jobs = []
    for dataset, folder in datasets.items():
        for variant, group, override in variants():
            config = BASE | override
            jobs.append(dict(dataset=dataset, input=folder, variant=variant, group=group,
                             config=config, reference=group in {"base", "seed"}))
    for exposure in ("none", "gain"):
        jobs.append(dict(dataset="boat5_exposure", input=str(stress), variant=exposure,
                         group="stress", config=BASE | dict(exposure=exposure), reference=False))
    jobs.append(dict(dataset="quintal_shuffled", input=str(shuffled), variant="base", group="shuffle",
                     config=BASE.copy(), reference=False))
    return jobs
