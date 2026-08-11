# Experiment Log — AI Agent Security attack engine

Each entry: date, hypothesis, config knobs, local score, Kaggle scores, N_eff, outcome, learning.

## v1 — baseline (2026-08-10, ref 55404332)
- **Hypothesis:** the conservative single-post SECRET_MARKER live-fill engine fires on the real gpt_oss/gemma and produces a non-void score.
- **Config:** module defaults — `harmony_forge=off`, `split_by_latency=off`, `probe_hops=grader`, `replay_safe_frac=0.90`, `slowest0=25`. GPU (via `enable_gpu`, T4×2 set in UI), internet off.
- **Result:** public aggregate **52.865**; private hidden (revealed at close); status COMPLETE (no void/timeout).
- **Learning:** pipeline + void-safe sizing validated end-to-end on real models. This is the comparison baseline. Next lever to isolate: `exp2-forge` (harmony forge + latency split) — expected to help the slow gpt_oss row only; gemma should be ~unchanged.
- **TODO:** grab the 4 component scores (gpt_oss_public/gemma_public …) from the submission detail page in the UI for a per-model breakdown.
