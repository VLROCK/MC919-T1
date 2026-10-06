from pathlib import Path
import numpy as np
from experiments.evaluate import evaluate
from experiments.plan import variants
from experiments.tables import export
from panorama.io import read_frames, save_image


def test_comparison_support_is_resolution_normalized(tmp_path):
    for name in ("a", "b"):
        save_image(tmp_path/f"{name}.png", np.full((200, 200, 3), 100, np.uint8))
    fixed = read_frames(tmp_path, 100)
    support = [dict(i=0,j=1,a=np.array([[40.,40],[60,60]]),b=np.array([[30.,40],[50,60]]))]
    H = np.array([[1.,0,20],[0,1,0],[0,0,1]])
    metrics = dict(transforms={"0":np.eye(3),"1":H}, focal_factor=.9,exposure_gains={"0":1,"1":1})
    row = dict(input=str(tmp_path),dataset="test",config=dict(max_side=200,projection="planar"))
    values = evaluate(row,metrics,fixed,support)
    assert values["eval_fraction"] == 1
    assert values["eval_rmse_px600"] < 1e-9  # unidade = escala do suporte fornecido
    assert values["photo_mae"] == 0
    metrics["transforms"].pop("1")
    assert evaluate(row,metrics,fixed,support)["eval_fraction"] == 0


def test_plan_has_unique_variants_and_expected_controls():
    rows = variants()
    assert len(rows) == len({r[0] for r in rows}) == 25
    assert {"detector", "resolution", "focal", "seed", "deghost"} <= {r[1] for r in rows}


def test_tables_escape_tex_and_preserve_failure(tmp_path):
    export(tmp_path,"table",[dict(name="run_1",status="failed",error=None)])
    tex=(tmp_path/"table.tex").read_text(encoding="utf-8")
    assert r"run\_1" in tex and "failed" in tex and "--" in tex
