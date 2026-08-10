"""Generate the Kaggle submission notebook by inlining attack.py.

Usage: python tools/build_notebook.py [-o submission.ipynb]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

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


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-o", "--output", default=str(REPO / "submission.ipynb"))
    args = ap.parse_args()

    attack_src = (REPO / "attack.py").read_text()
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
    Path(args.output).write_text(json.dumps(nb, indent=1))
    print(f"wrote {args.output} ({len(attack_src)} chars of attack.py inlined)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
