"""Métricas sobre suporte fixo SIFT; não confundir com ground truth independente."""
from copy import copy
import json
from pathlib import Path
import cv2
import numpy as np
from panorama.cli import parser
from panorama.features import extract, match_all
from panorama.geometry import intrinsic, project
from panorama.io import read_frames, save_json


def canonical_names(dataset, frames):
    mapping = {}
    if dataset == "quintal_shuffled":
        mapping = json.loads(Path("data/quintal_shuffled/manifest.json").read_text())["original_names"]
    return [mapping.get(f.name, f.name).rsplit(".", 1)[0] for f in frames]


def build_support(folder, output):
    frames = read_frames(folder, 600)
    args = parser().parse_args(["build", str(folder), "--ratio", ".65", "--ransac", "1.5",
                                "--nfeatures", "4000", "--max-side", "600"])
    cv2.setRNGSeed(2026)
    cv2.setNumThreads(1)
    edges, records, _ = match_all(frames, extract(frames, "sift", 4000), args)
    support = []
    for e in edges:
        pick = np.linspace(0, len(e.a)-1, min(200, len(e.a)), dtype=int)
        support.append(dict(i=e.i, j=e.j, a=e.a[pick], b=e.b[pick]))
    save_json(output, dict(images=[f.name for f in frames], pairs=support,
                          note="SIFT ratio .65, RANSAC 1.5px, max-side 600; no máximo 200 pontos por par. "
                               "Suporte comum, não ground truth nem teste independente do treinamento."))
    return frames, support


def transform_between(ts, i, j, frames, projection, focal):
    if projection == "planar":
        return np.linalg.solve(ts[j], ts[i])
    return intrinsic(frames[j], focal) @ ts[j].T @ ts[i] @ np.linalg.inv(intrinsic(frames[i], focal))


def evaluate(status, metrics, fixed_frames, support):
    frames = read_frames(status["input"], status["config"]["max_side"])
    names = canonical_names(status["dataset"], frames)
    fixed_names = [f.name.rsplit(".", 1)[0] for f in fixed_frames]
    index = {fixed_names.index(name): k for k, name in enumerate(names) if name in fixed_names}
    ts = {int(k): np.array(v) for k, v in metrics["transforms"].items()}
    gains = {int(k): v for k, v in metrics.get("exposure_gains", {}).items()}
    errors, photometric, total = [], [], sum(len(e["a"]) for e in support)
    for e in support:
        if e["i"] not in index or e["j"] not in index:
            continue
        i, j = index[e["i"]], index[e["j"]]
        if i not in ts or j not in ts:
            continue
        a, b = np.asarray(e["a"]), np.asarray(e["b"])
        si, sj = frames[i].scale/fixed_frames[e["i"]].scale, frames[j].scale/fixed_frames[e["j"]].scale
        H = transform_between(ts, i, j, frames, status["config"]["projection"], metrics["focal_factor"])
        forward = np.linalg.norm(project(H, a*si)/sj-b, axis=1)
        reverse = np.linalg.norm(project(np.linalg.inv(H), b*sj)/si-a, axis=1)
        errors.extend(np.sqrt((forward**2+reverse**2)/2).tolist())
        samples = []
        for k, pts in ((i, a*si), (j, b*sj)):
            gray = cv2.cvtColor(frames[k].image, cv2.COLOR_BGR2GRAY).astype(np.float32)
            gray = cv2.GaussianBlur(gray, (9, 9), 0)
            values = cv2.remap(gray, pts[:, 0].astype(np.float32).reshape(-1, 1),
                               pts[:, 1].astype(np.float32).reshape(-1, 1), cv2.INTER_LINEAR).ravel()
            samples.append(np.clip(values*gains.get(k, 1.), 0, 255))
        photometric.extend(np.abs(samples[0]-samples[1]).tolist())
    if not errors:
        return dict(eval_fraction=0)
    return dict(eval_fraction=len(errors)/max(total, 1), eval_points=len(errors),
                eval_median_px600=float(np.median(errors)), eval_mean_px600=float(np.mean(errors)),
                eval_p95_px600=float(np.percentile(errors, 95)),
                eval_rmse_px600=float(np.sqrt(np.mean(np.square(errors)))),
                photo_mae=float(np.mean(photometric)))


def summarize(status, fixed_frames, support):
    output = Path(status["output"])
    row = {k: status[k] for k in ("dataset", "variant", "group", "status", "wall_seconds")}
    row.update(status["config"])
    row["output"] = str(output)
    path = output/"metrics.json"
    if not path.exists():
        log = output.parent/(output.name+".log")
        lines = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        row["failure"] = next((x for x in reversed(lines) if "Erro:" in x), "timeout ou falha; consulte log")
        return row
    m = json.loads(path.read_text(encoding="utf-8"))
    row.update(accepted=len(m["accepted"]), rejected=len(m["rejected"]),
               core_seconds=m["core_seconds"], pipeline_seconds=m["pipeline_seconds"],
               keypoints_mean=float(np.mean(m["detectors"][row["detector"]]["keypoints"])),
               graph_edges=sum(p["accepted"] for p in m["pairs"]),
               used_edges=len(m["final_alignment"]), coverage=m["coverage_fraction"],
               changed_fraction=m["changed_pixels"]/max(1,m["coverage_fraction"]*m["canvas"]["width"]*m["canvas"]["height"]),
               fitted_focal=m["focal_factor"], final_mean_px=float(np.mean([p["mean_px"] for p in m["final_alignment"]])),
               ba_converged=m["bundle"]["converged"] if m["bundle"] else None,
               ba_accepted=m["bundle"]["accepted"] if m["bundle"] else None,
               warnings=" | ".join(m["warnings"]))
    row.update({f"seconds_{k}":v for k,v in m["stage_seconds"].items()})
    for tag, ref in (("reference", "ref"), ("reference_all_inputs", "ref_all")):
        if tag in m:
            row[ref+"_success"] = m[tag]["success"]
            row[ref+"_seconds"] = m[tag]["seconds"]
    row.update(evaluate(status, m, fixed_frames, support))
    return row
