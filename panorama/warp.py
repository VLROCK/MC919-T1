"""Projeção inversa com máscaras explícitas, limites de memória e longitude periódica."""
from dataclasses import dataclass
import cv2
import numpy as np
from .geometry import corners, intrinsic, project


@dataclass
class Canvas:
    width: int
    height: int
    x0: float
    y0: float
    scale: float
    center: float = 0.
    wrap: bool = False


def border_rays(frame, R, focal):
    h, w = frame.image.shape[:2]
    x, y = np.linspace(0, w-1, 80), np.linspace(0, h-1, 80)
    pts = np.vstack([np.c_[x, x*0], np.c_[x, x*0+h-1],
                     np.c_[y*0, y], np.c_[y*0+w-1, y]])
    rays = np.c_[pts, np.ones(len(pts))] @ np.linalg.inv(intrinsic(frame, focal)).T
    return rays @ R.T


def make_canvas(frames, transforms, order, args, focal):
    if args.projection == "planar":
        all_points = []
        for i in order:
            pts = corners(frames[i])
            z = np.c_[pts, np.ones(4)] @ transforms[i][2]
            if z.min() <= 0 <= z.max():
                raise ValueError(
                    f"A projeção plana de '{frames[i].name}' cruza o infinito "
                    "(não existe um canvas finito nesse referencial). Isso pode ocorrer "
                    "em uma varredura ampla ou por alinhamento incorreto. "
                    "Tente novamente acrescentando --projection cylindrical --alignment bundle "
                    "--exposure gain, sem reutilizar a pasta --output da tentativa anterior.")
            all_points.append(project(transforms[i], pts))
        points = np.vstack(all_points)
        low, high = np.floor(points.min(axis=0)), np.ceil(points.max(axis=0))
        canvas = Canvas(int(high[0]-low[0]+1), int(high[1]-low[1]+1), *low, 1.)
    else:
        yaw = np.unwrap([np.arctan2(transforms[i][0, 2], transforms[i][2, 2]) for i in order])
        center = float((yaw.min()+yaw.max())/2)
        scale = float(np.median([frames[i].image.shape[1] for i in order]) * focal)
        xs, ys = [], []
        for i in order:
            r = border_rays(frames[i], transforms[i], focal)
            theta = center + (np.arctan2(r[:, 0], r[:, 2])-center+np.pi) % (2*np.pi)-np.pi
            rho = np.hypot(r[:, 0], r[:, 2])
            vertical = (r[:, 1] / np.maximum(rho, 1e-6) if args.projection == "cylindrical"
                        else np.arctan2(r[:, 1], rho))
            xs.extend(theta * scale)
            ys.extend(vertical * scale)
        x0, x1 = (center-np.pi)*scale, (center+np.pi)*scale
        if not args.full_360:
            x0, x1 = min(xs), max(xs)
        else:
            # Uma volta exata: W/scale = 2*pi, sem coluna duplicada.
            width = int(round(2*np.pi*scale))
            new_scale = width/(2*np.pi)
            ys = np.asarray(ys) * new_scale/scale
            scale = new_scale
            x0, x1 = (center-np.pi)*scale, (center+np.pi)*scale
        canvas = Canvas(int(np.ceil(x1-x0)), int(np.ceil(max(ys)-min(ys)))+1,
                        x0, float(np.floor(min(ys))), scale, center, args.full_360)
    if (not 1 <= canvas.width < 32767 or not 1 <= canvas.height < 32767 or
            canvas.width * canvas.height > args.max_megapixels * 1e6):
        raise ValueError(f"Canvas {canvas.width}x{canvas.height} excede o limite. "
                         "Reduza --max-side ou use outra projeção; confira o alinhamento.")
    return canvas


def warp_frame(frame, transform, canvas, projection, focal):
    h, w = frame.image.shape[:2]
    size = canvas.width, canvas.height
    if projection == "planar":
        shift = np.array([[1, 0, -canvas.x0], [0, 1, -canvas.y0], [0, 0, 1.]])
        H = shift @ transform
        image = cv2.warpPerspective(frame.image, H, size)
        mask = cv2.warpPerspective(np.ones((h, w), np.uint8), H, size,
                                   flags=cv2.INTER_NEAREST).astype(bool)
        return image, mask
    image = np.zeros((canvas.height, canvas.width, 3), np.uint8)
    mask = np.zeros((canvas.height, canvas.width), bool)
    theta = (np.arange(canvas.width)+canvas.x0)/canvas.scale
    K = intrinsic(frame, focal)
    # Blocos evitam alocar vários mapas float64 do tamanho de todo o panorama.
    for top in range(0, canvas.height, 128):
        bottom = min(canvas.height, top+128)
        v = (np.arange(top, bottom)+canvas.y0)/canvas.scale
        tt, vv = np.meshgrid(theta, v)
        if projection == "cylindrical":
            world = np.stack([np.sin(tt), vv, np.cos(tt)], axis=-1)
        else:
            world = np.stack([np.cos(vv)*np.sin(tt), np.sin(vv), np.cos(vv)*np.cos(tt)], axis=-1)
        camera = world @ transform
        z = camera[..., 2]
        mx = (camera[..., 0]/np.maximum(z, 1e-9)*K[0, 0]+K[0, 2]).astype(np.float32)
        my = (camera[..., 1]/np.maximum(z, 1e-9)*K[1, 1]+K[1, 2]).astype(np.float32)
        valid = (z > 0) & (mx >= 0) & (mx <= w-1) & (my >= 0) & (my <= h-1)
        image[top:bottom] = cv2.remap(frame.image, mx, my, cv2.INTER_LINEAR)
        mask[top:bottom] = valid
    image[~mask] = 0
    return image, mask
