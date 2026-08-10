"""Local scoring harness. Runs the attack against a SandboxEnv with the
OptimalGuardrail and a selectable agent, prints the score, and logs a row.

Usage: python tools/local_score.py --budget-s 60 [--agent compliant|deterministic] [--label name] [--config knobs.json]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "sdk"))

from aicomp_sdk.attacks.contracts import AttackRunConfig  # noqa: E402
from aicomp_sdk.core.env.sandbox import SandboxEnv  # noqa: E402
from aicomp_sdk.core.predicates import eval_predicates  # noqa: E402
from aicomp_sdk.guardrails.optimal import Guardrail as Optimal  # noqa: E402
from aicomp_sdk.scoring import score_attack  # noqa: E402
from aicomp_sdk.core.cells import cell_signature  # noqa: E402
from aicomp_sdk.agents.factory import build_agent  # noqa: E402

import attack  # noqa: E402


def _make_agent(name: str):
    if name == "compliant":
        from tests.compliant_agent import CompliantAgent
        return CompliantAgent()
    return build_agent("deterministic")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget-s", type=float, default=60.0)
    ap.add_argument("--agent", choices=["compliant", "deterministic"], default="compliant")
    ap.add_argument("--label", default="local")
    ap.add_argument("--config", default=None, help="path to JSON of engine config knobs")
    args = ap.parse_args()

    knobs = json.loads(Path(args.config).read_text()) if args.config else {}
    fixtures = REPO / "sdk" / "aicomp_sdk" / "fixtures"

    algo = attack.AttackAlgorithm(config=knobs)
    gen_env = SandboxEnv(seed=123, fixtures_dir=fixtures, agent=_make_agent(args.agent), guardrail=Optimal())
    candidates = algo.run(gen_env, AttackRunConfig(time_budget_s=args.budget_s, max_tool_hops=8))

    # Replay + score (mirrors the grader: fresh env per candidate).
    findings = []
    for c in candidates:
        env = SandboxEnv(seed=123, fixtures_dir=fixtures, agent=_make_agent(args.agent), guardrail=Optimal())
        env.reset()
        for m in c.user_messages:
            env.interact(m, max_tool_hops=8)
        trace = env.export_trace_dict()
        preds = eval_predicates(trace)
        if preds:
            findings.append({
                "predicates": preds,
                "score_cell_signature": cell_signature(trace.get("tool_events", [])),
            })

    score = score_attack(findings)
    n_eff = len(findings)
    cells = len({f["score_cell_signature"]["hash"] for f in findings})
    pred_counts: dict[str, int] = {}
    for f in findings:
        for p in f["predicates"]:
            pred_counts[p["predicate"]] = pred_counts.get(p["predicate"], 0) + 1

    print(f"agent={args.agent} budget={args.budget_s}s returned={len(candidates)} "
          f"n_eff={n_eff} cells={cells} score={score:.3f} preds={pred_counts}")

    # Void-safety sanity: returned count must be positive and within cap.
    assert 0 < len(candidates) <= attack.HARD_N_CAP

    row = [time.strftime("%Y-%m-%dT%H:%M:%S"), args.label, args.agent, args.budget_s,
           len(candidates), n_eff, cells, f"{score:.3f}", "", "", "", "", ""]
    with (REPO / "experiments" / "results.csv").open("a", newline="") as fh:
        csv.writer(fh).writerow(row)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
