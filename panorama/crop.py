"""Recorta um panorama pelo maior retângulo inteiramente válido.

Uso: python -m panorama.crop outputs/alguma_execucao
Preserva panorama.png e grava derivados na mesma pasta.
"""

import argparse
import json
from pathlib import Path

import cv2
import numpy as np


def largest_valid_rectangle(mask: np.ndarray) -> tuple[int, int, int, int]:
    """Retorna (x, y, largura, altura) do maior retângulo sem pixels inválidos."""
    heights = np.zeros(mask.shape[1], dtype=np.int32)
    best = (0, 0, 0, 0)
    best_area = 0
    for bottom, row in enumerate(mask):
        heights = np.where(row, heights + 1, 0)
        stack: list[tuple[int, int]] = []
        for x in range(mask.shape[1] + 1):
            height = int(heights[x]) if x < mask.shape[1] else 0
            start = x
            while stack and stack[-1][1] > height:
                left, old_height = stack.pop()
                area = old_height * (x - left)
                if area > best_area:
                    best_area = area
                    best = (left, bottom - old_height + 1, x - left, old_height)
                start = left
            if not stack or stack[-1][1] < height:
                stack.append((start, height))
    return best


def crop_run(folder: Path) -> dict:
    image = cv2.imread(str(folder / "panorama.png"), cv2.IMREAD_COLOR)
    mask_image = cv2.imread(str(folder / "valid_mask.png"), cv2.IMREAD_GRAYSCALE)
    if image is None or mask_image is None or image.shape[:2] != mask_image.shape:
        raise ValueError(f"Panorama e valid_mask ausentes ou de tamanhos diferentes: {folder}")
    mask = mask_image > 0
    x, y, width, height = largest_valid_rectangle(mask)
    if width == 0 or height == 0:
        raise ValueError(f"Nenhuma região válida em {folder}")
    roi = np.s_[y:y + height, x:x + width]
    cv2.imwrite(str(folder / "panorama_cropped.png"), image[roi])
    alpha = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)
    alpha[:, :, 3] = mask_image
    cv2.imwrite(str(folder / "panorama_transparent.png"), alpha)
    without_path = folder / "without_deghost.png"
    original_without = (cv2.imread(str(without_path), cv2.IMREAD_COLOR)
                        if without_path.exists() else None)
    if original_without is not None and original_without.shape == image.shape:
        cv2.imwrite(str(folder / "without_deghost_cropped.png"), original_without[roi])
    info = {
        "method": "largest all-valid axis-aligned rectangle",
        "source_size": [image.shape[1], image.shape[0]],
        "crop_xywh": [x, y, width, height],
        "crop_area_fraction_of_canvas": round(width * height / mask.size, 5),
        "valid_pixels_retained_fraction": round(width * height / int(mask.sum()), 5),
        "note": "O recorte remove pixels; panorama.png continua intacto.",
    }
    (folder / "crop.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    return info


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path, nargs="+")
    args = parser.parse_args()
    for folder in args.folder:
        print(folder, crop_run(folder))


if __name__ == "__main__":
    main()
