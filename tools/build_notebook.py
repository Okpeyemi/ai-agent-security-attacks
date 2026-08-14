"""Generate the Kaggle submission notebook by inlining attack.py.

Keeps attack.py as the single source of truth. A "variant" appends a small
override block that reassigns module-level constants AFTER the class is defined
(the gateway instantiates AttackAlgorithm(config={}), so on Kaggle the engine
reads module constants, not config). This mirrors the public-notebook pattern.

Usage:
  python tools/build_notebook.py                       # baseline -> submission.ipynb
  python tools/build_notebook.py --variant exp2-forge  # -> submission_exp2-forge.ipynb
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Variant overrides: Python appended after the attack.py source. Empty = baseline.
VARIANTS: dict[str, str] = {
    "baseline": "",
    "exp2-forge": (
        "\n\n# --- variant override: exp2-forge (2026-08-10) ---\n"
        "# gpt_oss chain-of-thought suppression via Harmony token forge, applied\n"
        "# only to the latency-classified slow row. gemma (fast) keeps the plain\n"
        "# verbose template. Enabled via module constants because the gateway\n"
        "# instantiates AttackAlgorithm(config={}).\n"
        "HARMONY_FORGE = True\n"
        "SPLIT_BY_LATENCY = True\n"
    ),
    "exp3-forge-frac95": (
        "\n\n# --- variant override: exp3-forge-frac95 (2026-08-12) ---\n"
        "# Stacks on the proven forge win (exp2 = 75.420 public): forge + latency split,\n"
        "# plus a more aggressive replay fill fraction (0.90 -> 0.95) to fit more N_eff.\n"
        "HARMONY_FORGE = True\n"
        "SPLIT_BY_LATENCY = True\n"
        "REPLAY_SAFE_FRAC = 0.95\n"
    ),
    "robustness-deputy": (
        "\n\n# --- variant override: robustness-deputy (2026-08-11) ---\n"
        "# CONFUSED_DEPUTY family: benign, unsolicited email.send. The one\n"
        "# transfer-robust family (survives the strict-guardrail panel 4/4 vs exfil\n"
        "# 1/4). Enabled via module constant because the gateway instantiates\n"
        "# AttackAlgorithm(config={}).\n"
        'FAMILY = "deputy"\n'
    ),
    "exp5-frac97": (
        "\n\n# --- variant override: exp5-frac97 (2026-08-14) ---\n"
        "# Same proven single-post recipe as exp3 (forge + split), but fill 0.97 of\n"
        "# the budget instead of 0.95 -> more N_eff. Disclosed public 79-86 notebooks\n"
        "# use 0.97-0.98 safely with replay-safe (accumulated-cost) sizing. No probe_hops.\n"
        "HARMONY_FORGE = True\n"
        "SPLIT_BY_LATENCY = True\n"
        "REPLAY_SAFE_FRAC = 0.97\n"
    ),
    "exp4-probe1": (
        "\n\n# --- variant override: exp4-probe1 (2026-08-13) ---\n"
        "# Stacks on exp3 (public 83.250): probe the fill at 1 hop (~1.5-2x faster ->\n"
        "# more N_eff). The exfil event is recorded at hop-0 so a candidate fires\n"
        "# identically at 1 or 8 hops. REPLAY_COST_COEF=2.5 conservatively scales the\n"
        "# 1-hop fill measurement up to the true 8-hop replay cost so replay-safe\n"
        "# sizing cannot under-count and void.\n"
        "HARMONY_FORGE = True\n"
        "SPLIT_BY_LATENCY = True\n"
        "REPLAY_SAFE_FRAC = 0.95\n"
        "PROBE_HOPS = 1\n"
        "REPLAY_COST_COEF = 2.5\n"
    ),
    "robustness-deputy-forge": (
        "\n\n# --- variant override: robustness-deputy-forge (2026-08-13) ---\n"
        "# CONFUSED_DEPUTY family + Harmony forge on the gpt_oss (slow) row to speed\n"
        "# its generation -> more N_eff on our private-transfer bet. gemma unchanged.\n"
        'FAMILY = "deputy"\n'
        "HARMONY_FORGE = True\n"
        "SPLIT_BY_LATENCY = True\n"
    ),
}

CELL1_SETUP = (
    "import sys, glob, os\n"
    "from pathlib import Path\n"
    "sys.argv = [sys.argv[0]]\n"
    "for c in glob.glob('/kaggle/input/**/kaggle_evaluation', recursive=True):\n"
    "    r = str(Path(c).parent)\n"
    "    if r not in sys.path:\n"
    "        sys.path.insert(0, r)\n"
    "    break\n"
    "print('setup done | IS_RERUN:', bool(os.getenv('KAGGLE_IS_COMPETITION_RERUN')))\n"
)

CELL3_CHECK = (
    "import py_compile\n"
    "py_compile.compile('/kaggle/working/attack.py', doraise=True)\n"
    "src = open('/kaggle/working/attack.py').read()\n"
    "assert 'class AttackAlgorithm(AttackAlgorithmBase)' in src\n"
    "assert 'SECRET_MARKER' in src\n"
    "print('attack.py OK')\n"
)

CELL4_RUN = (
    "import os, csv\n"
    "if os.getenv('KAGGLE_IS_COMPETITION_RERUN'):\n"
    "    import kaggle_evaluation.jed_attack_134815.jed_attack_inference_server as server\n"
    "    server.JEDAttackInferenceServer().serve()\n"
    "else:\n"
    "    with open('/kaggle/working/submission.csv', 'w', newline='') as fh:\n"
    "        w = csv.writer(fh); w.writerow(['Id', 'Score'])\n"
    "        for r in ['gpt_oss_public','gpt_oss_private','gemma_public','gemma_private']:\n"
    "            w.writerow([r, 0.0])\n"
    "    print('placeholder submission.csv written. Set GPU T4x2, Internet OFF, then Submit.')\n"
)


def _code_cell(source: str) -> dict:
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": source.splitlines(keepends=True)}


def build(variant: str = "baseline", output: str | None = None) -> str:
    if variant not in VARIANTS:
        raise ValueError(f"Unknown variant {variant!r}; known: {sorted(VARIANTS)}")
    attack_src = (REPO / "attack.py").read_text() + VARIANTS[variant]
    cell2 = "%%writefile /kaggle/working/attack.py\n" + attack_src

    nb = {
        "cells": [
            _code_cell(CELL1_SETUP),
            _code_cell(cell2),
            _code_cell(CELL3_CHECK),
            _code_cell(CELL4_RUN),
        ],
        "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3"},
                     "language_info": {"name": "python"}},
        "nbformat": 4, "nbformat_minor": 5,
    }
    if output is None:
        name = "submission.ipynb" if variant == "baseline" else f"submission_{variant}.ipynb"
        output = str(REPO / name)
    Path(output).write_text(json.dumps(nb, indent=1))
    return output


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="baseline", choices=sorted(VARIANTS))
    ap.add_argument("-o", "--output", default=None)
    args = ap.parse_args()
    out = build(variant=args.variant, output=args.output)
    attack_len = len((REPO / "attack.py").read_text()) + len(VARIANTS[args.variant])
    print(f"wrote {out} (variant={args.variant}, {attack_len} chars of attack.py inlined)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
