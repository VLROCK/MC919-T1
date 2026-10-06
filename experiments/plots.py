"""Figuras estáticas em PNG (300 dpi), PDF e SVG para publicação."""
from pathlib import Path
import json
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "figure.constrained_layout.use": True, "svg.fonttype": "none"})
COLORS = ["#176B87", "#CE6C39", "#519E8A", "#995D81", "#525B76"]


def save(fig, folder, name):
    folder.mkdir(parents=True, exist_ok=True)
    for suffix in ("png", "pdf", "svg"):
        fig.savefig(folder/f"{name}.{suffix}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def comparisons(rows, folder):
    for dataset in ("quintal", "boat5"):
        group = [r for r in rows if r["dataset"] == dataset]
        for family in ("detector", "projection", "alignment", "blend", "exposure", "focal"):
            selected = [r for r in group if r["group"] in {"base", family}]
            fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
            for ax, metric, title in zip(axes, ["eval_median_px600", "core_seconds"],
                                         ["Erro geométrico mediano (px @600)", "Tempo do núcleo (s)"]):
                for k, row in enumerate(selected):
                    value = row.get(metric)
                    if row["status"] != "ok" or value is None:
                        ax.text(k, .05, "FALHOU", rotation=90, ha="center", transform=ax.get_xaxis_transform(), color="#a32020")
                    else:
                        ax.bar(k, value, color=COLORS[k%len(COLORS)], width=.65)
                        ax.annotate(f"{value:.2f}", (k,value), xytext=(0,3), textcoords="offset points", ha="center", fontsize=8)
                ax.set_xticks(range(len(selected)), [r["variant"].replace(family+"_", "") for r in selected], rotation=25, ha="right")
                ax.set_title(title)
                ax.set_xlim(-.6,len(selected)-.4)
                ax.grid(axis="y", alpha=.2)
                ax.margins(y=.22)
            note = "plano/par a par altera dois fatores" if family == "projection" else "uma alteração por vez"
            fig.suptitle(f"{dataset} • {family} • {note}")
            save(fig, folder, f"{dataset}_{family}")
        fig, axes = plt.subplots(2, 2, figsize=(10, 7))
        for ax, family, field, xlabel in zip(axes.flat, ["ratio", "ransac", "features", "resolution"],
                                            ["ratio", "ransac", "nfeatures", "max_side"],
                                            ["Ratio de Lowe", "RANSAC (px de processamento)", "Limite SIFT", "Maior lado (px)"]):
            selected = sorted([r for r in group if r["group"] in {"base", family}], key=lambda r:r[field])
            good = [r for r in selected if r["status"] == "ok"]
            ax.plot([r[field] for r in good], [r["eval_median_px600"] for r in good], "o-", color=COLORS[0])
            ax.set(xlabel=xlabel, ylabel="Erro mediano (px @600)")
            ax.grid(alpha=.2)
            for r in selected:
                if r["status"] != "ok":
                    ax.text(r[field], .1, "falhou", rotation=90, transform=ax.get_xaxis_transform())
        fig.suptitle(f"{dataset} • sensibilidade de parâmetros (suporte de avaliação fixo)")
        save(fig, folder, f"{dataset}_sensibilidade")
        selected = [r for r in group if r["group"] in {"base", "detector"} and r["status"] == "ok"]
        fig, ax = plt.subplots(figsize=(7, 3.5))
        bottom = np.zeros(len(selected))
        for k, phase in enumerate(("read", "extract", "match", "geometry", "compose")):
            values = np.array([r["seconds_"+phase] for r in selected])
            ax.bar([r["detector"] for r in selected], values, bottom=bottom, label=phase, color=COLORS[k])
            bottom += values
        ax.set(ylabel="Tempo (s)", title=f"{dataset} • custo por etapa")
        ax.legend(ncol=3, fontsize=8)
        save(fig, folder, f"{dataset}_tempos")


def visual_panels(rows, folder):
    for dataset in ("quintal", "boat5"):
        for label, names in (("panoramas", ["base", "alignment_pairwise", "projection_spherical", "blend_bands5"]),
                             ("deghost", ["deghost_none", "deghost_15", "base", "deghost_60"])):
            selected = [next((r for r in rows if r["dataset"] == dataset and r["variant"] == name
                              and r["status"] == "ok"), None) for name in names]
            selected = [r for r in selected if r]
            if not selected:
                continue
            fig, axes = plt.subplots(len(selected), 1, figsize=(11, max(3, 2.3*len(selected))), squeeze=False)
            roi = None
            base = next(r for r in rows if r["dataset"] == dataset and r["variant"] == "base")
            if label == "deghost":
                metrics = json.loads((Path(base["output"])/"metrics.json").read_text(encoding="utf-8"))
                roi = metrics["comparison_roi"]
            for ax, row in zip(axes.flat, selected):
                im = cv2.imread(str(Path(row["output"])/"panorama.png"))
                if roi:
                    x,y,w,h = roi
                    im = im[y:y+h, x:x+w]
                ax.imshow(cv2.cvtColor(im, cv2.COLOR_BGR2RGB))
                ax.set_title(row["variant"], loc="left", fontsize=10)
                ax.axis("off")
            fig.suptitle(f"{dataset} • {'mesma ROI do baseline, sem redimensionamento geométrico' if roi else 'panoramas em seus próprios canvases'}")
            save(fig, folder, f"{dataset}_{label}")
        base = next(r for r in rows if r["dataset"] == dataset and r["variant"] == "base")
        own, ref = Path(base["output"])/"panorama.png", Path(base["output"])/"reference/panorama.png"
        if own.exists() and ref.exists():
            fig, axes = plt.subplots(2, 1, figsize=(11, 6))
            for ax, path, name in zip(axes, (own,ref), ("Pipeline próprio", "cv2.Stitcher")):
                ax.imshow(cv2.cvtColor(cv2.imread(str(path)), cv2.COLOR_BGR2RGB));ax.axis("off");ax.set_title(name,loc="left")
            fig.suptitle(dataset+" • comparação visual; canvases diferentes")
            save(fig, folder, dataset+"_stitcher")
