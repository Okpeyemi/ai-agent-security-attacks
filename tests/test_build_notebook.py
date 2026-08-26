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


def test_exp3_variant_stacks_forge_and_frac(tmp_path):
    bn = _load_build_module()
    assert "exp3-forge-frac95" in bn.VARIANTS
    ov = bn.VARIANTS["exp3-forge-frac95"]
    assert "HARMONY_FORGE = True" in ov and "SPLIT_BY_LATENCY = True" in ov
    assert "REPLAY_SAFE_FRAC = 0.95" in ov
    out = tmp_path / "nb.ipynb"
    bn.build(variant="exp3-forge-frac95", output=str(out))
    cell2 = "".join(json.loads(out.read_text())["cells"][1]["source"])
    assert "REPLAY_SAFE_FRAC = 0.95" in cell2
    compile(cell2.split("\n", 1)[1], "attack.py", "exec")


def test_exp10_probe1_uncond_variant(tmp_path):
    bn = _load_build_module()
    assert "exp10-probe1-uncond" in bn.VARIANTS
    ov = bn.VARIANTS["exp10-probe1-uncond"]
    assert "HARMONY_FORGE = True" in ov and "SPLIT_BY_LATENCY = False" in ov
    assert "PROBE_HOPS = 1" in ov and "REPLAY_COST_COEF = 1.3" in ov
    assert "REPLAY_SAFE_FRAC = 0.95" in ov
    out = tmp_path / "nb.ipynb"
    bn.build(variant="exp10-probe1-uncond", output=str(out))
    cell2 = "".join(json.loads(out.read_text())["cells"][1]["source"])
    assert "PROBE_HOPS = 1" in cell2 and "REPLAY_COST_COEF = 1.3" in cell2
    compile(cell2.split("\n", 1)[1], "attack.py", "exec")


def test_exp9_frac98_variant(tmp_path):
    bn = _load_build_module()
    assert "exp9-frac98" in bn.VARIANTS
    ov = bn.VARIANTS["exp9-frac98"]
    assert "HARMONY_FORGE = True" in ov and "SPLIT_BY_LATENCY = True" in ov
    assert "REPLAY_SAFE_FRAC = 0.98" in ov
    out = tmp_path / "nb.ipynb"
    bn.build(variant="exp9-frac98", output=str(out))
    cell2 = "".join(json.loads(out.read_text())["cells"][1]["source"])
    assert "REPLAY_SAFE_FRAC = 0.98" in cell2
    compile(cell2.split("\n", 1)[1], "attack.py", "exec")


def test_deputy_uncond_frac97_variant(tmp_path):
    bn = _load_build_module()
    assert "deputy-uncond-frac97" in bn.VARIANTS
    ov = bn.VARIANTS["deputy-uncond-frac97"]
    assert 'FAMILY = "deputy"' in ov and "HARMONY_FORGE = True" in ov
    assert "SPLIT_BY_LATENCY = False" in ov and "REPLAY_SAFE_FRAC = 0.97" in ov
    out = tmp_path / "nb.ipynb"
    bn.build(variant="deputy-uncond-frac97", output=str(out))
    cell2 = "".join(json.loads(out.read_text())["cells"][1]["source"])
    assert "REPLAY_SAFE_FRAC = 0.97" in cell2 and 'FAMILY = "deputy"' in cell2
    compile(cell2.split("\n", 1)[1], "attack.py", "exec")


def test_deputy_forge_uncond_variant(tmp_path):
    bn = _load_build_module()
    assert "robustness-deputy-forge-uncond" in bn.VARIANTS
    ov = bn.VARIANTS["robustness-deputy-forge-uncond"]
    assert 'FAMILY = "deputy"' in ov
    assert "HARMONY_FORGE = True" in ov
    assert "SPLIT_BY_LATENCY = False" in ov
    assert "REPLAY_SAFE_FRAC = 0.95" in ov
    out = tmp_path / "nb.ipynb"
    bn.build(variant="robustness-deputy-forge-uncond", output=str(out))
    cell2 = "".join(json.loads(out.read_text())["cells"][1]["source"])
    assert 'FAMILY = "deputy"' in cell2 and "SPLIT_BY_LATENCY = False" in cell2
    compile(cell2.split("\n", 1)[1], "attack.py", "exec")


def test_exp6_forge_uncond_variant(tmp_path):
    bn = _load_build_module()
    assert "exp6-forge-uncond" in bn.VARIANTS
    ov = bn.VARIANTS["exp6-forge-uncond"]
    assert "HARMONY_FORGE = True" in ov
    assert "SPLIT_BY_LATENCY = False" in ov
    assert "REPLAY_SAFE_FRAC = 0.95" in ov  # confirmed-best frac (isolate the forge-routing change)
    out = tmp_path / "nb.ipynb"
    bn.build(variant="exp6-forge-uncond", output=str(out))
    cell2 = "".join(json.loads(out.read_text())["cells"][1]["source"])
    assert "SPLIT_BY_LATENCY = False" in cell2 and "HARMONY_FORGE = True" in cell2
    compile(cell2.split("\n", 1)[1], "attack.py", "exec")


def test_exp5_frac97_variant(tmp_path):
    bn = _load_build_module()
    assert "exp5-frac97" in bn.VARIANTS
    ov = bn.VARIANTS["exp5-frac97"]
    assert "HARMONY_FORGE = True" in ov and "SPLIT_BY_LATENCY = True" in ov
    assert "REPLAY_SAFE_FRAC = 0.97" in ov
    assert "PROBE_HOPS" not in ov  # single-post at grader hops, no probe_hops
    out = tmp_path / "nb.ipynb"
    bn.build(variant="exp5-frac97", output=str(out))
    cell2 = "".join(json.loads(out.read_text())["cells"][1]["source"])
    assert "REPLAY_SAFE_FRAC = 0.97" in cell2
    compile(cell2.split("\n", 1)[1], "attack.py", "exec")


def test_exp4_probe1_variant(tmp_path):
    bn = _load_build_module()
    assert "exp4-probe1" in bn.VARIANTS
    ov = bn.VARIANTS["exp4-probe1"]
    for needle in ("HARMONY_FORGE = True", "SPLIT_BY_LATENCY = True",
                   "REPLAY_SAFE_FRAC = 0.95", "PROBE_HOPS = 1", "REPLAY_COST_COEF = 2.5"):
        assert needle in ov
    out = tmp_path / "nb.ipynb"
    bn.build(variant="exp4-probe1", output=str(out))
    cell2 = "".join(json.loads(out.read_text())["cells"][1]["source"])
    assert "PROBE_HOPS = 1" in cell2 and "REPLAY_COST_COEF = 2.5" in cell2
    compile(cell2.split("\n", 1)[1], "attack.py", "exec")


def test_robustness_deputy_forge_variant(tmp_path):
    bn = _load_build_module()
    assert "robustness-deputy-forge" in bn.VARIANTS
    ov = bn.VARIANTS["robustness-deputy-forge"]
    assert 'FAMILY = "deputy"' in ov
    assert "HARMONY_FORGE = True" in ov and "SPLIT_BY_LATENCY = True" in ov
    out = tmp_path / "nb.ipynb"
    bn.build(variant="robustness-deputy-forge", output=str(out))
    cell2 = "".join(json.loads(out.read_text())["cells"][1]["source"])
    assert 'FAMILY = "deputy"' in cell2 and "HARMONY_FORGE = True" in cell2
    compile(cell2.split("\n", 1)[1], "attack.py", "exec")


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
