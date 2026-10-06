"""Interface de linha de comando e validação de parâmetros."""
import argparse
from datetime import datetime
from pathlib import Path
import sys
import cv2


def parser():
    p = argparse.ArgumentParser(description="T1: panorama automático de imagens fora de ordem.")
    sub = p.add_subparsers(dest="command", required=True)
    for name in ("build", "compare"):
        q = sub.add_parser(name, help="Gera panorama" if name == "build" else "Executa variantes isoladas")
        q.add_argument("input", type=Path, help="Pasta com fotos e intrusa")
        q.add_argument("--output", type=Path)
        q.add_argument("--detector", choices=["sift", "orb", "akaze"], default="sift")
        q.add_argument("--compare-detectors", nargs="*", choices=["sift", "orb", "akaze"], default=["sift", "orb"])
        q.add_argument("--nfeatures", type=int, default=5000)
        q.add_argument("--ratio", type=float, default=.75)
        q.add_argument("--ransac", type=float, default=3., help="Limiar em pixels após resize")
        q.add_argument("--min-inliers", type=int, default=20)
        q.add_argument("--min-inlier-ratio", type=float, default=.3)
        q.add_argument("--min-coverage", type=float, default=.01)
        q.add_argument("--max-side", type=int, default=1200)
        q.add_argument("--max-megapixels", type=float, default=12.)
        q.add_argument("--projection", choices=["planar", "cylindrical", "spherical"], default="planar")
        q.add_argument("--focal-factor", type=float, default=.9, help="Foco/largura, sem EXIF")
        q.add_argument("--full-360", action="store_true", help="Exige laço e cobertura horizontal completa")
        q.add_argument("--alignment", choices=["pairwise", "bundle"], default="pairwise")
        q.add_argument("--ba-points", type=int, default=250, help="Máximo de inliers por par no ajuste")
        q.add_argument("--ba-iterations", type=int, default=150)
        q.add_argument("--exposure", choices=["none", "gain"], default="none")
        q.add_argument("--blend", choices=["feather", "multiband"], default="feather")
        q.add_argument("--bands", type=int, default=5)
        q.add_argument("--deghost", choices=["none", "inconsistency"], default="inconsistency")
        q.add_argument("--ghost-threshold", type=float, default=30., help="Diferença média BGR 0..255")
        q.add_argument("--ghost-dilate", type=int, default=5)
        q.add_argument("--ghost-min-area", type=int, default=25)
        q.add_argument("--roi", nargs=4, type=int, metavar=("X", "Y", "W", "H"))
        q.add_argument("--draw-matches", type=int, default=120)
        q.add_argument("--reference", action="store_true", help="Compara com cv2.Stitcher")
        q.add_argument("--diagnostics", choices=["full", "compact"], default="full",
                       help="compact omite keypoints/matches/progressivo; mantém métricas e panoramas")
        q.add_argument("--seed", type=int, default=42)
    q = sub.add_parser("demo", help="Gera fotos sintéticas, não substitui a coleta")
    q.add_argument("--output", type=Path, default=Path("data/demo"))
    q.add_argument("--kind", choices=["planar", "rotation360"], default="planar")
    q.add_argument("--seed", type=int, default=42)
    return p


def validate(args, p):
    if not args.input.is_dir():
        p.error("Pasta de entrada não encontrada.")
    if not 0 < args.ratio < 1 or not 0 < args.min_inlier_ratio <= 1:
        p.error("--ratio e --min-inlier-ratio precisam estar entre 0 e 1.")
    if not 0 <= args.min_coverage <= 1 or not .15 < args.focal_factor < 5:
        p.error("--min-coverage deve estar em [0,1]; --focal-factor em (0.15,5).")
    for name in ("nfeatures", "ransac", "max_side", "max_megapixels", "ba_points", "ba_iterations",
                 "bands", "ghost_threshold", "ghost_min_area", "draw_matches"):
        if getattr(args, name) <= 0:
            p.error(f"{name} precisa ser positivo.")
    if args.min_inliers < 4 or args.ghost_dilate < 0 or args.bands > 10:
        p.error("Use min-inliers >= 4, ghost-dilate >= 0 e bands <= 10.")
    if args.command == "build" and args.full_360 and args.projection == "planar":
        p.error("--full-360 exige --projection cylindrical ou spherical.")
    args.output = args.output or Path("outputs") / datetime.now().strftime("%Y%m%d_%H%M%S_%f")


def main(argv=None):
    p = parser()
    args = p.parse_args(argv)
    try:
        if args.command == "demo":
            from .synthetic import generate
            generate(args.output, args.kind, args.seed)
        else:
            validate(args, p)
            if args.command == "compare":
                from .experiments import compare
                compare(args)
            else:
                from .pipeline import run
                run(args)
    except (ValueError, OSError, cv2.error) as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 2
    return 0
