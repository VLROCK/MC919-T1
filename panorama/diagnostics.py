"""Figuras e tabelas de evidências; nenhuma métrica inventada de qualidade visual."""
import csv
import html
from pathlib import Path
import cv2
import numpy as np
from .io import save_image


def connectivity(matrix, names, output):
    with (output / "connectivity.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["image"] + names)
        writer.writerows([[name] + row.tolist() for name, row in zip(names, matrix)])
    cell = 60
    n = len(names)
    img = np.full((cell*(n+1), cell*(n+1), 3), 255, np.uint8)
    maximum = max(int(matrix.max()), 1)
    for i in range(n):
        cv2.putText(img, str(i), (i*cell+cell+10, 35), 0, .6, (0, 0, 0), 1)
        cv2.putText(img, str(i), (10, i*cell+cell+35), 0, .6, (0, 0, 0), 1)
        for j in range(n):
            y, x = (i+1)*cell, (j+1)*cell
            value = int(matrix[i, j])
            img[y:y+cell, x:x+cell] = (255, int(245-160*value/maximum), 180)
            cv2.putText(img, str(value), (x+3, y+35), 0, .45, (0, 0, 0), 1)
    save_image(output / "connectivity.png", img)


def comparison(before, after, change, output, roi=None):
    h, w = change.shape
    if roi is None:
        if change.any():
            smooth = cv2.boxFilter((change > 0).astype(np.float32), -1, (151, 151))
            y, x = np.unravel_index(np.argmax(smooth), smooth.shape)
        else:
            y, x = h//2, w//2
        x, y = max(0, x-160), max(0, y-120)
        roi = (x, y, min(320, w-x), min(240, h-y))
    x, y, rw, rh = roi
    if x < 0 or y < 0 or rw < 1 or rh < 1 or x+rw > w or y+rh > h:
        raise ValueError("--roi está fora do canvas; consulte canvas em metrics.json.")
    pair = np.hstack([before[y:y+rh, x:x+rw], after[y:y+rh, x:x+rw]])
    pair = cv2.resize(pair, None, fx=2, fy=2, interpolation=cv2.INTER_NEAREST)
    pair = cv2.copyMakeBorder(pair, 35, 0, 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255))
    cv2.putText(pair, "SEM DE GHOST", (8, 24), 0, .6, (0, 0, 0), 1)
    cv2.putText(pair, "COM DE GHOST", (rw*2+8, 24), 0, .6, (0, 0, 0), 1)
    save_image(output / "deghost_comparison.png", pair)
    return list(roi)


def gallery(output, metrics):
    names = metrics["images"]
    lines = ["<!doctype html><html lang='pt-BR'><meta charset='utf-8'>",
             "<title>Panorama T1 — execução</title><style>body{font:16px system-ui;max-width:1200px;",
             "margin:32px auto;padding:20px}img{max-width:100%}pre{white-space:pre-wrap}</style>",
             "<h1>Panorama T1</h1><p>Índices são apenas identificadores de arquivo; não são a ordem.</p>",
             "<ul>" + "".join(f"<li>{i}: {html.escape(n)}</li>" for i, n in enumerate(names)) + "</ul>",
             "<p>Ordem espacial: " + html.escape(str(metrics["order"])) + "</p>",
             "<p>Rejeitadas: " + html.escape(str(metrics["rejected"])) + "</p>",
             "<p><a href='metrics.json'>Métricas e parâmetros completos</a></p>"]
    for name in ("panorama.png", "connectivity.png", "deghost_comparison.png", "ghost_mask.png",
                 "reference/panorama.png"):
        if (output/name).exists():
            lines.append(f"<h2>{name}</h2><a href='{name}'><img src='{name}'></a>")
    for folder in ("keypoints", "matches", "progressive"):
        lines.append(f"<details><summary>{folder}</summary>")
        for p in sorted((output/folder).rglob("*.jpg")):
            relative = p.relative_to(output).as_posix()
            lines.append(f"<p>{relative}</p><img loading='lazy' src='{relative}'>")
        lines.append("</details>")
    lines.append("</html>")
    (output/"index.html").write_text("\n".join(lines), encoding="utf-8")
