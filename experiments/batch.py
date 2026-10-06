"""Executa processos sequenciais isolados, com logs, timeout e retomada explícita."""
import argparse
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
from time import perf_counter
from panorama.io import save_json
from .plan import make_plan, inventory


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--resume", action="store_true")
    p.add_argument("--timeout", type=int, default=240)
    args = p.parse_args()
    if args.output.exists() and not args.resume:
        p.error("Saída existente; use outra pasta ou --resume.")
    args.output.mkdir(parents=True, exist_ok=True)
    plan_path = args.output/"plan.json"
    if args.resume:
        jobs = json.loads(plan_path.read_text(encoding="utf-8"))
    else:
        jobs = make_plan()
        save_json(plan_path, jobs)
        save_json(args.output/"inputs.json", {j["dataset"]: inventory(j["input"]) for j in jobs})
        save_json(args.output/"environment.json", dict(platform=platform.platform(), python=sys.version,
                  timing="Processos sequenciais, uma thread nas bibliotecas; sem repetições concorrentes",
                  timeout_seconds=args.timeout))
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1",
               NUMEXPR_NUM_THREADS="1", PYTHONIOENCODING="utf-8")
    results = []
    for number, job in enumerate(jobs, 1):
        location = args.output/"runs"/job["dataset"]/job["variant"]
        status_file = location.parent/(location.name+".status.json")
        if status_file.exists():
            results.append(json.loads(status_file.read_text(encoding="utf-8")))
            continue
        if location.exists():
            raise ValueError(f"Saída incompleta preservada: {location}; use nova pasta de lote.")
        location.parent.mkdir(parents=True, exist_ok=True)
        command = [sys.executable, "-m", "panorama", "build", job["input"], "--output", str(location)]
        for key, value in job["config"].items():
            command.extend(["--"+key.replace("_", "-"), str(value)])
        command.append("--compare-detectors")
        if job["reference"]:
            command.append("--reference")
        print(f"[{number}/{len(jobs)}] {job['dataset']} / {job['variant']}", flush=True)
        start = perf_counter()
        with (location.parent/(location.name+".log")).open("w", encoding="utf-8") as log:
            try:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                        env=env, timeout=args.timeout, check=False)
                status = "ok" if result.returncode == 0 else "failed"
                code = result.returncode
            except subprocess.TimeoutExpired:
                status, code = "timeout", None
        row = job | dict(status=status, returncode=code, wall_seconds=perf_counter()-start,
                         output=str(location), command=subprocess.list2cmdline(command))
        save_json(status_file, row)
        results.append(row)
        save_json(args.output/"status.json", results)
        print(f"  {status}, {row['wall_seconds']:.1f}s", flush=True)
    save_json(args.output/"status.json", results)


if __name__ == "__main__":
    main()
