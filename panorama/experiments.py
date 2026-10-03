"""Ablações com uma mudança por vez e resultados que não se sobrescrevem."""
from copy import copy
import cv2
from .io import new_output, save_json
from .pipeline import run


def compare(args):
    output = new_output(args.output)
    if args.full_360:
        variants = [
            ("01_cylindrical_pairwise", dict(projection="cylindrical", alignment="pairwise")),
            ("02_cylindrical_bundle", dict(projection="cylindrical", alignment="bundle")),
            ("03_spherical_bundle", dict(projection="spherical", alignment="bundle")),
            ("04_cylindrical_exposure", dict(projection="cylindrical", alignment="bundle", exposure="gain")),
        ]
    else:
        variants = [
            ("01_baseline", {}),
            ("02_bundle", dict(alignment="bundle")),
            ("03_exposure", dict(exposure="gain")),
            ("04_multiband", dict(blend="multiband")),
            ("05_cylindrical_pairwise", dict(projection="cylindrical")),
            ("06_cylindrical_bundle", dict(projection="cylindrical", alignment="bundle")),
            ("07_spherical_pairwise", dict(projection="spherical")),
            ("08_spherical_bundle", dict(projection="spherical", alignment="bundle")),
        ]
    rows = []
    for name, changes in variants:
        config = copy(args)
        # Base fixa torna as ablações comparáveis; demais parâmetros são herdados.
        config.projection, config.alignment = "planar", "pairwise"
        config.exposure, config.blend, config.deghost = "none", "feather", "inconsistency"
        config.reference = name == variants[0][0]
        config.output = output / name
        for key, value in changes.items():
            setattr(config, key, value)
        try:
            result = run(config)
            row = dict(name=name, success=True, seconds=result["pipeline_seconds"],
                       alignment=result["final_alignment"], warnings=result["warnings"])
        except (ValueError, OSError, cv2.error) as e:
            row = dict(name=name, success=False, error=str(e))
        rows.append(row)
        save_json(output / "comparison.json", rows)
    links = "\n".join(f"<li><a href='{r['name']}/index.html'>{r['name']}</a>: "
                       f"{'OK' if r['success'] else 'falhou (consulte comparison.json)'}</li>" for r in rows)
    (output / "index.html").write_text("<!doctype html><meta charset='utf-8'><h1>Comparações</h1><ul>"
                                      + links + "</ul>", encoding="utf-8")
    if not any(row["success"] for row in rows):
        raise ValueError("Todas as variantes falharam; consulte comparison.json.")
