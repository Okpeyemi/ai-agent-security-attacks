# AI Agent Security — Multi-Step Tool Attacks

Attack submission engine. See `docs/superpowers/specs/2026-08-10-ai-agent-security-attack-engine-design.md`
and the plan `docs/superpowers/plans/2026-08-10-attack-engine-mvp.md`.

## Layout
- `attack.py` — the submission engine (single self-contained file; source of truth).
- `tools/local_score.py` — local scoring harness (SandboxEnv + OptimalGuardrail).
- `tools/build_notebook.py` — generates `submission.ipynb` by inlining `attack.py`.
- `tests/` — pytest suite (+ compliant mock agent).
- `experiments/` — experiment log and results.csv.
- `sdk/` — extracted competition SDK (gitignored).

## Dev loop
```bash
pip install -r requirements-dev.txt
pytest tests/ -v                                              # unit + integration
python tools/local_score.py --budget-s 60 --agent compliant  # local score
python tools/build_notebook.py                               # -> submission.ipynb
```

## Submit
Upload `submission.ipynb` to the competition, set **GPU T4×2**, **Internet OFF**, Submit.

## Engine knobs (via AttackAlgorithm config)
Defaults are conservative (first submission cannot void). Tune one per submission:
- `replay_safe_frac` (0.90 → 0.95/0.97) — how much of the budget to fill.
- `probe_hops` (0 = grader hops; 1 = faster fill).
- `split_by_latency` + `harmony_forge` — gpt_oss chain-of-thought suppression (the ~60→~85 lever).
- `slowest0` — seed for the per-candidate cost estimate. Default 25.0 is a conservative
  floor sized for the real ~9000s budget. **For local runs** on a small budget, pass a low
  value so the fill loop runs instead of bailing to the fallback, e.g.:
  `python tools/local_score.py --budget-s 8 --agent compliant --config knobs.json`
  with `knobs.json = {"slowest0": 0.02}`.
```

## Notes
- `attack.py` imports only `aicomp_sdk` + stdlib (it is inlined into the notebook).
- Local `compliant` agent gives a true score signal (`score = 0.09 × N_eff`); the SDK
  `deterministic` agent posts a fixed `"demo"` payload so it is a no-crash check only.
  Neither predicts real gpt_oss/gemma fire rates — that comes from Kaggle submissions,
  logged in `experiments/`.
