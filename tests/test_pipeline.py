import json
import numpy as np
import pytest
from panorama.cli import main
from panorama.synthetic import generate


def test_shuffled_pipeline_rejects_intruder_and_saves_evidence(tmp_path):
    folder = tmp_path/"input"
    generate(folder)
    output = tmp_path/"result"
    assert main(["build", str(folder), "--output", str(output), "--max-side", "600",
                 "--nfeatures", "2000", "--alignment", "bundle", "--ba-points", "40",
                 "--exposure", "gain"]) == 0
    truth = json.loads((folder/"ground_truth.json").read_text())
    result = json.loads((output/"metrics.json").read_text(encoding="utf-8"))
    order = [result["images"][i] for i in result["order"]]
    assert order == truth["order"] or order == truth["order"][::-1]
    assert [result["images"][i] for i in result["rejected"]] == [truth["intruder"]]
    assert set(result["detectors"]) == {"sift", "orb"}
    assert result["bundle"]["accepted"]
    assert result["changed_pixels"] > 0
    assert max(p["mean_px"] for p in result["final_alignment"]) < 1
    for name in ("panorama.png", "without_deghost.png", "deghost_comparison.png",
                 "index.html", "connectivity.csv", "ghost_mask.png"):
        assert (output/name).exists()
    # Uma segunda execução não deve tocar o resultado existente.
    assert main(["build", str(folder), "--output", str(output)]) == 2


def test_blank_images_fail_cleanly(tmp_path):
    from panorama.io import save_image
    inputs = tmp_path/"blank"
    inputs.mkdir()
    for i in range(2):
        save_image(inputs/f"{i}.png", np.zeros((100, 100, 3), np.uint8))
    assert main(["build", str(inputs), "--output", str(tmp_path/"result")]) == 2


@pytest.mark.parametrize("projection", ["cylindrical", "spherical"])
def test_full_360_integration(tmp_path, projection):
    folder, output = tmp_path/"input", tmp_path/"output"
    generate(folder, kind="rotation360")
    assert main(["build", str(folder), "--output", str(output), "--projection", projection,
                 "--full-360", "--alignment", "bundle", "--focal-factor", "0.75",
                 "--compare-detectors", "--nfeatures", "1800", "--ba-points", "40",
                 "--ba-iterations", "80"]) == 0
    metrics = json.loads((output/"metrics.json").read_text(encoding="utf-8"))
    truth = json.loads((folder/"ground_truth.json").read_text())
    assert metrics["horizontal_coverage"] == 1
    assert metrics["closing_edge"]
    assert len(metrics["accepted"]) == 12 and len(metrics["rejected"]) == 1
    assert metrics["images"][metrics["rejected"][0]] == truth["intruder"]
    order = [metrics["images"][i] for i in metrics["order"]]
    # Ciclos aceitam qualquer origem e qualquer sentido.
    doubled = truth["order"]*2
    candidates = [doubled[i:i+12] for i in range(12)]
    assert order in candidates or order[::-1] in candidates
    assert abs(metrics["focal_factor"]-.75) < .05
    assert max(p["rmse_px"] for p in metrics["final_alignment"]) < 1


def test_names_do_not_control_order(tmp_path):
    folder, output = tmp_path/"input", tmp_path/"output"
    generate(folder)
    truth = json.loads((folder/"ground_truth.json").read_text())
    files = sorted(folder.glob("*.png"))
    mapping = {file.name: f"random_{7-i}.png" for i, file in enumerate(files)}
    for file in files:
        file.rename(folder/mapping[file.name])
    assert main(["build", str(folder), "--output", str(output), "--compare-detectors",
                 "--nfeatures", "1800"]) == 0
    metrics = json.loads((output/"metrics.json").read_text(encoding="utf-8"))
    order = [metrics["images"][i] for i in metrics["order"]]
    expected = [mapping[name] for name in truth["order"]]
    assert order == expected or order == expected[::-1]
