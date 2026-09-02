# AI Agent Security — Multi-Step Tool Attacks

Attack submission engine. Specs & plans in `docs/superpowers/`:
Phase 1 (public workhorse) `specs/2026-08-10-ai-agent-security-attack-engine-design.md`;
Phase 2 (transfer robustness) `specs/2026-08-11-phase2-transfer-robustness-design.md`.
**Working Note (Kaggle Writeup): [`docs/working-note-submission.md`](docs/working-note-submission.md)** — *"Public Score Is Not Security: The Confused-Deputy Transfer Result."* This repository is its public companion. Method draft: `docs/working-note-draft.md`. Experiment log: `experiments/`.

## Results & final submissions (campaign complete — private leaderboard revealed)

Public trajectory **52.9 → 87.0** (forge → fill-fraction, saturated at 0.97–0.98); deputy **11.9 → 19.2**.
All levers exhausted or dominated (forge ✅, fill-fraction ✅; `probe_hops=1` ≈ wash, multi-post / encoding / short-template ❌).

| Role | Variant / kernel | Public | Private (revealed 2026-09-01) |
|---|---|---|---|
| **PUBLIC final** (lenient-private bet) | `exp9-frac98` — forge + latency-split + fill 0.98 (`aas-attack-exp9`) | **86.985** | **0.000** — blocked (payload inspected) |
| **PRIVATE-STRICT final** (strict bet) | `robustness-deputy-forge-uncond` + fill 0.97 (`aas-attack-deputy-uncond-frac97`) | **19.155** | **19.155** — transferred intact |

**Outcome — transfer thesis confirmed.** The two finals hedged the two private-guardrail regimes; the strict regime
obtained. The private guardrail inspects the outbound payload, so *every* exfiltration submission scored **0** across
the whole public range 52.9→87.0, while the benign confused-deputy final transferred **exactly** (19.155 → 19.155) —
it survives the strict-guardrail panel 4/4 and blocking it is self-defeating by the false-positive economics. The
robust hedge moved the team from **public rank 1267/4252 to private rank 142/4252**. Public leaderboard performance
was *uncorrelated* with private score for the exfiltration family: on this benchmark, robustness to an unseen
stricter defense — not public score — is the evidence of a real, transferable agent-security failure.

## Layout
- `attack.py` — the submission engine (single self-contained file; source of truth). Two families: `exfil` (default, SECRET_MARKER public workhorse) and `deputy` (CONFUSED_DEPUTY, transfer-robust).
- `tools/local_score.py` — local scoring harness (SandboxEnv + OptimalGuardrail).
- `tools/build_notebook.py` — generates a notebook by inlining `attack.py`; `--variant` selects a variant override.
- `tools/guardrails_strict.py` — dev-time panel of strict guardrails (proxies for the hidden private).
- `tools/robustness_eval.py` — families × panel survival table + the CONFUSED_DEPUTY false-positive proof.
- `tests/` — pytest suite (+ extended compliant mock agent).
- `experiments/` — experiment log, results.csv, `robustness_table.md`.
- `sdk/` — extracted competition SDK (gitignored).

## Dev loop
```bash
pip install -r requirements-dev.txt
pytest tests/ -v                                              # unit + integration
python tools/local_score.py --budget-s 60 --agent compliant  # local score
python tools/robustness_eval.py                              # survival table + FP proof
python tools/build_notebook.py                               # -> submission.ipynb (baseline)
python tools/build_notebook.py --variant robustness-deputy   # -> submission_robustness-deputy.ipynb
```

## Variants (via `build_notebook.py --variant`)
Variants append a small module-constant override (the Kaggle gateway instantiates `AttackAlgorithm(config={})`, so levers must be module constants):
- `baseline` — exfil, all levers off (v1 = public 52.865).
- `exp2-forge` — `HARMONY_FORGE`+`SPLIT_BY_LATENCY` on (gpt_oss CoT suppression).
- `robustness-deputy` — `FAMILY="deputy"` (CONFUSED_DEPUTY; survives the strict panel 4/4 vs exfil 1/4).

## Submit
Upload the chosen `submission*.ipynb`, set **GPU T4×2**, **Internet OFF**, Submit. Private is hidden until 2026-09-01; the panel/`robustness_table.md` is our transfer-robustness proxy, not the real private.

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
