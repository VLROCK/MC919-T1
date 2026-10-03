"""Orquestração do pipeline; algoritmos ficam nos módulos especializados."""
from dataclasses import asdict
from time import perf_counter
import platform
import cv2
import numpy as np
import scipy

from . import diagnostics, features, graph
from .blend import blend_pair
from .exposure import compensate
from .io import new_output, read_frames, save_image, save_json
from .optimize import alignment_errors, bundle
from .reference import stitch_reference
from .warp import make_canvas, warp_frame


def run(args):
    start = perf_counter()
    output = new_output(args.output)
    cv2.setRNGSeed(args.seed)
    cv2.setNumThreads(1)
    frames = read_frames(args.input, args.max_side)
    print(f"{len(frames)} imagens; detector={args.detector}; saída={output}", flush=True)
    selected = features.extract(frames, args.detector, args.nfeatures, output)
    edges, records, matrix = features.match_all(frames, selected, args, output)
    detector_stats = {}
    for detector in dict.fromkeys([args.detector] + args.compare_detectors):
        if detector == args.detector:
            current, pairs = selected, records
        else:
            from copy import copy
            other = copy(args)
            other.detector = detector
            current = features.extract(frames, detector, args.nfeatures, output)
            _, pairs, _ = features.match_all(frames, current, other)
        detector_stats[detector] = dict(keypoints=[len(f.keypoints) for f in current],
                                        extraction_seconds=sum(f.seconds for f in current),
                                        accepted_pairs=sum(p["accepted"] for p in pairs), pairs=pairs)
    diagnostics.connectivity(matrix, [f.name for f in frames], output)
    save_json(output / "matching.json", dict(images=[f.name for f in frames], pairs=records,
                                             detectors=detector_stats, config=vars(args)))
    ids, rejected = graph.component(len(frames), edges)
    edges = [e for e in edges if e.i in ids and e.j in ids]
    transforms, root, tree = graph.initialize(ids, edges, frames, args.projection, args.focal_factor)
    edges, inconsistent = graph.consistent_edges(edges, tree, transforms, frames, args.projection,
                                                 args.focal_factor,
                                                 max(5*args.ransac, .08*max(
                                                     frames[i].image.shape[1] for i in ids)))
    baseline = {i: T.copy() for i, T in transforms.items()}
    focal, ba = args.focal_factor, None
    if args.alignment == "bundle":
        print("Ajustando todos os pares aceitos...", flush=True)
        transforms, focal, ba = bundle(transforms, root, edges, frames, args)
    order = graph.infer_order(ids, transforms, frames, args.projection)
    edge_keys = {frozenset((e.i, e.j)) for e in edges}
    closing_edge = frozenset((order[0], order[-1])) in edge_keys
    if args.full_360 and (len(edges) < len(ids) or not closing_edge):
        raise ValueError("360° requer fechamento de laço: não há par confiável entre as extremidades.")
    gains = compensate(frames, ids, edges, root) if args.exposure == "gain" else {i: 1. for i in ids}
    # Preserva o diagnóstico geométrico mesmo se o canvas não puder ser construído.
    save_json(output / "alignment.json", dict(
        images=[f.name for f in frames], accepted=ids, rejected=rejected,
        order=order, root=root, tree=tree, projection=args.projection,
        transforms=transforms, focal_factor=focal, bundle=ba,
        inconsistent_edges=inconsistent,
        errors=alignment_errors(transforms, edges, frames, args.projection, focal)))
    canvas = make_canvas(frames, transforms, order, args, focal)
    shape = canvas.height, canvas.width
    normal, clean = np.zeros((*shape, 3), np.float32), np.zeros((*shape, 3), np.float32)
    valid, changes = np.zeros(shape, bool), np.zeros(shape, np.uint8)
    overlap_stats = []
    for step, i in enumerate(order):
        print(f"Compondo {step+1}/{len(order)}: {frames[i].name}", flush=True)
        warped, mask = warp_frame(frames[i], transforms[i], canvas, args.projection, focal)
        warped = np.clip(warped.astype(np.float32)*gains[i], 0, 255)
        normal, _, diff, overlap = blend_pair(normal, warped, valid, mask, args, False)
        clean, changed, _, _ = blend_pair(clean, warped, valid, mask, args, args.deghost != "none")
        changes |= changed
        if overlap.any():
            overlap_stats.append(dict(image=i, pixels=int(overlap.sum()),
                                       mean_absolute_color_difference=float(diff[overlap].mean())))
        valid |= mask
        preview = clean
        if max(shape) > 1600:
            preview = cv2.resize(clean, None, fx=1600/max(shape), fy=1600/max(shape))
        save_image(output / "progressive" / f"{step+1:03}.jpg", preview)
    coverage = float(np.mean(valid.any(axis=0)))
    if args.full_360 and coverage < 1.:
        save_image(output / "incomplete_coverage.png", valid.astype(np.uint8)*255)
        raise ValueError(f"Cobertura horizontal incompleta ({coverage:.1%}); não é um panorama 360°.")
    save_image(output / "panorama.png", clean)
    save_image(output / "without_deghost.png", normal)
    save_image(output / "valid_mask.png", valid.astype(np.uint8)*255)
    save_image(output / "ghost_mask.png", changes)
    roi = diagnostics.comparison(normal, clean, changes, output, args.roi)
    warnings = []
    if inconsistent:
        warnings.append(f"{len(inconsistent)} atalhos rejeitados por inconsistência global; confira as texturas.")
    if ba and not ba["converged"]:
        warnings.append("Bundle atingiu limite sem convergir; confira os erros e considere --ba-iterations.")
    if len(ids) < 6:
        warnings.append("Menos de seis imagens aceitas: conjunto insuficiente para a etapa 1 do T1.")
    if not rejected:
        warnings.append("Nenhuma imagem rejeitada; a demonstração da intrusa ainda precisa ser conferida.")
    if not changes.any():
        warnings.append("Nenhuma região inconsistente selecionada; confira a presença de objeto móvel.")
    if any(frozenset(pair) not in edge_keys for pair in zip(order, order[1:])):
        warnings.append("Ordem espacial contém vizinhos sem aresta direta; confira grafo e cena multifaixa.")
    metrics = dict(config=vars(args), images=[f.name for f in frames], scales=[f.scale for f in frames],
                   accepted=ids, rejected=rejected, order=order, root=root, tree=tree,
                   pairs=records, detectors=detector_stats, canvas=asdict(canvas),
                   inconsistent_edges=inconsistent,
                   baseline_transforms=baseline, transforms=transforms, focal_factor=focal,
                   baseline_alignment=alignment_errors(baseline, edges, frames, args.projection, args.focal_factor),
                   final_alignment=alignment_errors(transforms, edges, frames, args.projection, focal),
                   bundle=ba, exposure_gains=gains, overlap=overlap_stats, comparison_roi=roi,
                   coverage_fraction=float(valid.mean()), horizontal_coverage=coverage,
                   closing_edge=closing_edge, changed_pixels=int(np.count_nonzero(changes)), warnings=warnings,
                   versions=dict(python=platform.python_version(), opencv=cv2.__version__,
                                 numpy=np.__version__, scipy=scipy.__version__))
    if args.full_360:
        both = valid[:, 0] & valid[:, -1]
        metrics["wrap_boundary_mae"] = float(np.abs(clean[both, 0]-clean[both, -1]).mean()) if both.any() else None
    metrics["pipeline_seconds"] = perf_counter()-start
    if args.reference:
        metrics["reference"] = stitch_reference(frames, ids, output / "reference")
        metrics["reference_all_inputs"] = stitch_reference(frames, list(range(len(frames))), output / "reference_all")
    save_json(output / "metrics.json", metrics)
    diagnostics.gallery(output, metrics)
    print(f"Ordem: {[frames[i].name for i in order]}", flush=True)
    print(f"Rejeitadas: {[frames[i].name for i in rejected]}", flush=True)
    for warning in warnings:
        print(f"AVISO: {warning}")
    return metrics
