import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _load_build_module():
    spec = importlib.util.spec_from_file_location("build_notebook", REPO / "tools" / "build_notebook.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_variants_registry_has_baseline_and_exp2():
    bn = _load_build_module()
    assert "baseline" in bn.VARIANTS
    assert bn.VARIANTS["baseline"] == ""  # no override
    assert "exp2-forge" in bn.VARIANTS
    ov = bn.VARIANTS["exp2-forge"]
    assert "HARMONY_FORGE = True" in ov
    assert "SPLIT_BY_LATENCY = True" in ov


def test_build_notebook_inlines_override_and_compiles(tmp_path):
    bn = _load_build_module()
    out = tmp_path / "nb.ipynb"
    bn.build(variant="exp2-forge", output=str(out))
    nb = json.loads(out.read_text())
    assert len(nb["cells"]) == 4
    cell2 = "".join(nb["cells"][1]["source"])
    assert cell2.startswith("%%writefile /kaggle/working/attack.py")
    assert "class AttackAlgorithm(AttackAlgorithmBase)" in cell2
    assert "HARMONY_FORGE = True" in cell2
    assert "SPLIT_BY_LATENCY = True" in cell2
    # the inlined attack.py body (minus the %%writefile magic) must compile
    body = cell2.split("\n", 1)[1]
    compile(body, "attack.py", "exec")


def test_baseline_has_no_override(tmp_path):
    bn = _load_build_module()
    out = tmp_path / "nb.ipynb"
    bn.build(variant="baseline", output=str(out))
    cell2 = "".join(json.loads(out.read_text())["cells"][1]["source"])
    assert "# --- variant override:" not in cell2  # no override block appended


def test_robustness_deputy_variant_sets_family(tmp_path):
    bn = _load_build_module()
    assert "robustness-deputy" in bn.VARIANTS
    ov = bn.VARIANTS["robustness-deputy"]
    assert 'family' in ov and 'deputy' in ov
    out = tmp_path / "nb.ipynb"
    bn.build(variant="robustness-deputy", output=str(out))
    cell2 = "".join(json.loads(out.read_text())["cells"][1]["source"])
    assert 'FAMILY = "deputy"' in cell2 or "'deputy'" in cell2 or '"deputy"' in cell2
    compile(cell2.split("\n", 1)[1], "attack.py", "exec")  # inlined source compiles
