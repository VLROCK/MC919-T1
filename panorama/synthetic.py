"""Cenas controladas para testes, sempre identificadas como sintéticas."""
import cv2
import numpy as np
from scipy.spatial.transform import Rotation
from .io import new_output, save_image, save_json


def texture(width, height, rng):
    image = rng.integers(35, 210, (height, width, 3), dtype=np.uint8)
    image = cv2.GaussianBlur(image, (5, 5), 0)
    for _ in range(width*2):
        x, y = int(rng.integers(width)), int(rng.integers(height))
        color = tuple(int(x) for x in rng.integers(10, 245, 3))
        cv2.circle(image, (x, y), int(rng.integers(2, 10)), color, -1)
    for x in range(20, width, 90):
        cv2.putText(image, str(rng.integers(1000, 9999)), (x, height//2), 0, .7, (245, 245, 245), 2)
    return image


def generate(output, kind="planar", seed=42):
    output = new_output(output)
    rng = np.random.default_rng(seed)
    n = 6 if kind == "planar" else 12
    labels = rng.permutation(n+1)
    truth = []
    if kind == "planar":
        world = texture(1320, 320, rng)
        for i in range(n):
            image = world[:, i*160:i*160+520].copy()
            if i in (2, 3):
                cv2.rectangle(image, (180+i*15, 190), (220+i*15, 260), (15, 15, 220), -1)
            image = np.clip(image.astype(float)*(0.85+0.055*i), 0, 255)
            name = f"view_{labels[i]:03}.png"
            save_image(output/name, image)
            truth.append(name)
    else:
        world = texture(2400, 900, rng)
        h, w, f = 320, 440, 330.
        y, x = np.indices((h, w))
        rays = np.stack([(x-(w-1)/2)/f, (y-(h-1)/2)/f, np.ones((h, w))], axis=-1)
        for i in range(n):
            R = Rotation.from_euler("y", i*360/n, degrees=True).as_matrix()
            r = rays @ R.T
            theta = np.arctan2(r[..., 0], r[..., 2])
            phi = np.arctan2(r[..., 1], np.hypot(r[..., 0], r[..., 2]))
            mx = ((theta/(2*np.pi)+.5)*world.shape[1]).astype(np.float32)
            my = ((phi/np.pi+.5)*world.shape[0]).astype(np.float32)
            image = cv2.remap(world, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
            name = f"view_{labels[i]:03}.png"
            save_image(output/name, image)
            truth.append(name)
    intruder = f"view_{labels[-1]:03}.png"
    save_image(output/intruder, texture(520, 320, np.random.default_rng(seed+2026)))
    save_json(output/"ground_truth.json", dict(synthetic=True, kind=kind, order=truth,
                                               intruder=intruder, focal_factor=.75 if kind != "planar" else None))
    print(f"Cena sintética em {output}. ground_truth.json é somente gabarito dos testes.")
