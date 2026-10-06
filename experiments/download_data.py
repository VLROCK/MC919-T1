"""Baixa cinco vistas boat do repositório oficial OpenCV, com proveniência."""
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen


def fetch(url):
    with urlopen(Request(url, headers={"User-Agent": "MC919-T1-benchmark"}), timeout=60) as r:
        return r.read()


def main():
    folder = Path("data/benchmark_boat5")
    folder.mkdir(parents=True, exist_ok=True)
    if (folder/"manifest.json").exists():
        print("Benchmark já baixado; preservando arquivos.")
        return
    commit = json.loads(fetch("https://api.github.com/repos/opencv/opencv_extra/commits/4.x"))["sha"]
    rows = []
    # Rótulos não sequenciais; o manifest não é entrada do pipeline.
    for source, label in zip(range(1, 6), ["vista_d", "vista_a", "vista_e", "vista_b", "vista_c"]):
        url = f"https://raw.githubusercontent.com/opencv/opencv_extra/{commit}/testdata/stitching/boat{source}.jpg"
        data = fetch(url)
        target = folder/f"{label}.jpg"
        target.write_bytes(data)
        rows.append(dict(file=target.name, source=f"boat{source}.jpg", url=url,
                         sha256=hashlib.sha256(data).hexdigest(), bytes=len(data)))
    readme_url = f"https://raw.githubusercontent.com/opencv/opencv_extra/{commit}/README.md"
    (folder/"UPSTREAM_README.md").write_bytes(fetch(readme_url))
    manifest = dict(dataset="OpenCV extra, boat1..boat5", upstream_commit=commit,
                    downloaded_date="2026-10-05", source="https://github.com/opencv/opencv_extra/tree/4.x/testdata/stitching",
                    tutorial="https://docs.opencv.org/4.x/d8/d19/tutorial_stitcher.html",
                    license_url=None, note="O diretório e a raiz não fornecem licença individual para as fotos. Origem arquivada, sem afirmar licença adicional; não republicar como autoria própria.",
                    images=rows, ground_truth_homographies=False, full_360=False)
    (folder/"manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Cinco imagens baixadas em {folder}, commit {commit}.")


if __name__ == "__main__":
    main()
