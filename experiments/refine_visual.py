"""Compara variantes visuais e recorta panoramas sem apagar as saídas originais.

Execute na raiz: .venv/Scripts/python -m experiments.refine_visual
"""

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

from panorama.crop import crop_run


BASE = (
    ("--detector", "sift"), ("--compare-detectors", None),
    ("--nfeatures", "2500"), ("--ratio", "0.75"), ("--ransac", "3"),
    ("--max-side", "600"), ("--projection", "cylindrical"),
    ("--alignment", "bundle"), ("--ba-points", "100"),
    ("--ba-iterations", "100"), ("--exposure", "gain"),
    ("--blend", "feather"), ("--deghost", "inconsistency"),
    ("--ghost-threshold", "30"), ("--max-megapixels", "8"),
    ("--diagnostics", "compact"), ("--seed", "42"),
)

RUNS = {
    "quintal": {
        "01_base": (),
        "02_esferica_multibanda": ("--projection", "spherical", "--blend", "multiband"),
        "03_multibanda_sem_deghost": ("--blend", "multiband", "--deghost", "none"),
        "04_multibanda_limiar60": ("--blend", "multiband", "--ghost-threshold", "60"),
        "05_foco060_ratio060_multibanda": (
            "--focal-factor", "0.6", "--ratio", "0.6", "--blend", "multiband"),
        "06_foco060_ratio060_sem_deghost": (
            "--focal-factor", "0.6", "--ratio", "0.6", "--blend", "multiband",
            "--deghost", "none"),
    },
    "boat5": {
        "01_base": (),
        "02_esferica_multibanda_sem_deghost": (
            "--projection", "spherical", "--blend", "multiband", "--deghost", "none"),
        "03_cilindrica_multibanda_sem_deghost": (
            "--blend", "multiband", "--deghost", "none"),
    },
}


def option_list(changes: tuple[str, ...]) -> list[str]:
    # Substitui a opção base, evitando passar o mesmo parâmetro duas vezes.
    values = dict(BASE)
    values.update(zip(changes[::2], changes[1::2]))
    result = []
    for key, value in values.items():
        result.append(key)
        if value is not None:
            result.append(value)
    return result


def make_hybrid(root: Path) -> dict:
    """Mantém a árvore limpa e usa mistura suave onde havia cortes à direita."""
    sharp = root / "quintal/01_base/resultado"
    smooth = root / "quintal/03_multibanda_sem_deghost/resultado"
    target = root / "quintal/07_hibrido_arvore_nitida/resultado"
    target.mkdir(parents=True, exist_ok=True)
    left = cv2.imread(str(sharp / "panorama.png"), cv2.IMREAD_COLOR)
    right = cv2.imread(str(smooth / "panorama.png"), cv2.IMREAD_COLOR)
    ma = cv2.imread(str(sharp / "valid_mask.png"), cv2.IMREAD_GRAYSCALE)
    mb = cv2.imread(str(smooth / "valid_mask.png"), cv2.IMREAD_GRAYSCALE)
    meta_left = json.loads((sharp / "metrics.json").read_text(encoding="utf-8"))
    meta_right = json.loads((smooth / "metrics.json").read_text(encoding="utf-8"))
    if (left is None or right is None or ma is None or mb is None
            or left.shape != right.shape
            or not np.array_equal(ma, mb)
            or meta_left["order"] != meta_right["order"]
            or meta_left["transforms"] != meta_right["transforms"]
            or meta_left["focal_factor"] != meta_right["focal_factor"]):
        raise ValueError("O híbrido exige panoramas com exatamente a mesma geometria e máscara.")
    x0, x1 = 550, 850
    xx = np.arange(left.shape[1], dtype=np.float32)
    fraction = np.clip((xx - x0) / (x1 - x0), 0, 1)
    fraction = fraction * fraction * (3 - 2 * fraction)
    weight = fraction[None, :, None]
    result = np.clip(left * (1 - weight) + right * weight, 0, 255).astype(np.uint8)
    cv2.imwrite(str(target / "panorama.png"), result)
    cv2.imwrite(str(target / "valid_mask.png"), ma)
    info = {
        "type": "derived_comparison_not_independent_build",
        "left_source": str(sharp), "right_source": str(smooth),
        "left_behavior": "deghosting original na árvore",
        "right_behavior": "multibanda sem deghosting",
        "transition_x_pixels": [x0, x1],
        "note": "A região à direita pode conter desfoque/ghosting por paralaxe."
    }
    (target / "derivation.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    crop = crop_run(target)
    return {
        "conjunto": "quintal", "variante": "07_hibrido_arvore_nitida", "status": "derivado",
        "projecao": "cylindrical", "blending": "misto", "deghost": "esquerda",
        "recorte_largura": crop["crop_xywh"][2],
        "recorte_altura": crop["crop_xywh"][3],
        "fracao_valida_mantida": crop["valid_pixels_retained_fraction"],
    }


def make_sheet(root: Path, dataset: str, names: list[str]) -> None:
    """Grade para inspecionar panorama recortado e detalhe do lado direito."""
    row_height, sheet_width = 290, 1700
    sheet = np.full((len(names) * row_height, sheet_width, 3), 248, np.uint8)
    for index, name in enumerate(names):
        path = root / dataset / name / "resultado/panorama_cropped.png"
        img = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if img is None:
            continue
        top = index * row_height
        cv2.putText(sheet, name, (15, top + 24), cv2.FONT_HERSHEY_SIMPLEX,
                    0.65, (35, 35, 35), 2, cv2.LINE_AA)
        height, width = img.shape[:2]
        scale = min(1120 / width, 245 / height)
        resized = cv2.resize(img, (round(width * scale), round(height * scale)))
        sheet[top + 35:top + 35 + resized.shape[0], 15:15 + resized.shape[1]] = resized
        right = img[:, round(width * .55):round(width * .95)]
        scale = min(500 / right.shape[1], 245 / right.shape[0])
        detail = cv2.resize(right, (round(right.shape[1] * scale),
                                    round(right.shape[0] * scale)))
        sheet[top + 35:top + 35 + detail.shape[0], 1180:1180 + detail.shape[1]] = detail
    cv2.imwrite(str(root / f"comparacao_{dataset}.png"), sheet)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/refino_visual_20261006"))
    parser.add_argument("--dataset", choices=["quintal", "boat5", "both"], default="both")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    datasets = RUNS if args.dataset == "both" else {args.dataset: RUNS[args.dataset]}
    rows = []
    for dataset, variants in datasets.items():
        source = Path("data/minha_cena" if dataset == "quintal" else "data/benchmark_boat5")
        for name, changes in variants.items():
            folder = args.output / dataset / name
            folder.mkdir(parents=True, exist_ok=True)
            run_folder = folder / "resultado"
            command = [sys.executable, "-m", "panorama", "build", str(source),
                       "--output", str(run_folder), *option_list(changes)]
            (folder / "comando.txt").write_text(subprocess.list2cmdline(command), encoding="utf-8")
            print(f"Rodando {dataset}/{name} ...", flush=True)
            if (run_folder / "metrics.json").exists():
                print("  resultados existentes; preservados", flush=True)
            else:
                with (folder / "execucao.log").open("w", encoding="utf-8") as log:
                    result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                            text=True, check=False)
                if result.returncode:
                    print(f"  falhou (código {result.returncode}); veja execucao.log", flush=True)
                    rows.append({"conjunto": dataset, "variante": name, "status": "falhou"})
                    continue
            crop = crop_run(run_folder)
            metrics = json.loads((run_folder / "metrics.json").read_text(encoding="utf-8"))
            row = {
                "conjunto": dataset, "variante": name, "status": "ok",
                "projecao": metrics["config"]["projection"],
                "blending": metrics["config"]["blend"],
                "deghost": metrics["config"]["deghost"],
                "limiar_deghost": metrics["config"]["ghost_threshold"],
                "foco_inicial": metrics["config"]["focal_factor"],
                "ratio": metrics["config"]["ratio"],
                "imagens_aceitas": len(metrics["accepted"]),
                "imagens_rejeitadas": len(metrics["rejected"]),
                "pixels_marcados_deghost": metrics["changed_pixels"],
                "tempo_nucleo_s": round(metrics["core_seconds"], 2),
                "rmse_ajuste_global_px": (round(metrics["bundle"]["final_rmse_px"], 3)
                                           if metrics.get("bundle") else ""),
                "recorte_largura": crop["crop_xywh"][2],
                "recorte_altura": crop["crop_xywh"][3],
                "fracao_valida_mantida": crop["valid_pixels_retained_fraction"],
            }
            rows.append(row)
            print(f"  concluído; recorte {row['recorte_largura']}×{row['recorte_altura']}", flush=True)
    if args.dataset in ("quintal", "both"):
        rows.append(make_hybrid(args.output))
        print("Híbrido do quintal gerado com transição suave entre x=550 e x=850.", flush=True)
    for dataset, variants in datasets.items():
        names = list(variants)
        if dataset == "quintal":
            names.append("07_hibrido_arvore_nitida")
        make_sheet(args.output, dataset, names)
    with (args.output / "resumo.csv").open("w", newline="", encoding="utf-8-sig") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=list(dict.fromkeys(
            key for item in rows for key in item)))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
