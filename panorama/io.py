"""Entrada sem EXIF e saída que nunca reutiliza uma execução anterior."""
import json
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass
class Frame:
    name: str
    image: np.ndarray
    scale: float


def read_frames(folder, max_side):
    paths = sorted(p for p in Path(folder).iterdir()
                   if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"})
    frames = []
    for path in paths:
        # IGNORE_ORIENTATION: nem a orientação EXIF é consultada.
        im = cv2.imdecode(np.fromfile(path, np.uint8),
                          cv2.IMREAD_COLOR | cv2.IMREAD_IGNORE_ORIENTATION)
        if im is None:
            raise ValueError(f"Não foi possível ler {path}")
        scale = min(1., max_side / max(im.shape[:2]))
        if scale < 1:
            im = cv2.resize(im, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        frames.append(Frame(path.name, im, scale))
    if len(frames) < 2:
        raise ValueError("A pasta precisa conter pelo menos duas imagens legíveis.")
    return frames


def save_image(path, image):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ok, data = cv2.imencode(path.suffix, np.clip(image, 0, 255).astype(np.uint8))
    if not ok:
        raise ValueError(f"Erro ao codificar {path}")
    data.tofile(path)


def save_json(path, value):
    def convert(x):
        if isinstance(x, np.ndarray):
            return x.tolist()
        if isinstance(x, np.generic):
            return x.item()
        if isinstance(x, Path):
            return str(x)
        raise TypeError(type(x).__name__)
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False,
                                    default=convert, allow_nan=False), encoding="utf-8")


def new_output(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=False)
    return path
