# Public Score Is Not Security: A Held-Out Transfer Framework and the Confused-Deputy Result on a Multi-Step Tool-Attack Benchmark

**Competition:** AI Agent Security — Multi-Step Tool Attacks (OpenAI / Google / IEEE).
**TL;DR.** We treat the held-out private leaderboard as the real target and build a framework to estimate which findings transfer to an unseen stricter defense *without probing it*. Its prediction held at the reveal: Every exfiltration submission scored **0** private; the confused-deputy final transferred **intact (19.155)**, lifting the team from public rank 1267 to **private rank 142 / 4252**. The transfer thesis is confirmed (§7). Working Note deadline 2026-09-08.

> **Responsible communication.** This note is about the *competition benchmark* — a deterministic, offline, fixture-backed sandbox. It documents how the benchmark scores multi-step tool-use failures and how a submission behaves under held-out defenses. It contains no instructions for attacking real systems and discloses no vulnerabilities outside the benchmark. All "attacks" are benchmark predicates fired against a simulated agent in a sealed sandbox.

## 1. Abstract

Tool-using LLM agents fail not only by emitting harmful text but by taking unsafe **actions** across multiple steps. On a deterministic, replay-scored benchmark for this setting, we make four contributions, in order of importance. **(1) A transfer-robustness framework.** Because prizes are decided by a stricter, held-out guardrail we can never probe, we estimate which findings survive an unseen defense *without probing it*: a panel of strict guardrail proxies, a survival/breach evaluator built on the benchmark's own oracle, and a false-positive-economics argument. **(2) A security finding.** Of the four scored failure modes, the benign **confused deputy** (an unsolicited `email.send`) is the *only* robustly-transferable one — because a rational defender cannot block it without an unacceptable false-positive cost. This is the quantitative side of the documented "capability gates are not authorization" failure, and it says something concrete about where the defense for tool-using agents must live. **(3) Two verified negatives** that map blind spots in the attack space and the harness: sentinel exfiltration has *no encoding hedge*, and single-hop fill-probing does not transfer. **(4) Documented seams** in the benchmark itself (a first-argument-only guardrail check; plaintext-only sentinel matching; throughput-dominated scoring), reported as actionable feedback to benchmark designers, with concrete defense recommendations. A supporting yield model (`S ≈ 0.09·N_eff`) and a void-safe live-fill procedure make every measurement reproducible; leaderboard scores are used only as evidence for the findings, never as the contribution. **At close, the held-out reveal confirmed the framework's central prediction:** every exfiltration submission scored zero against the private guardrail while the confused-deputy submission transferred intact, moving the team from public rank 1267 to private rank 142 of 4252.

## 2. The benchmark and its scoring

The evaluator replays each returned candidate (a chain of user messages) in a fresh sandbox and scores the resulting tool trace against four predicates (severity in braces): EXFILTRATION {5}, UNTRUSTED_TO_ACTION {5/4}, DESTRUCTIVE_WRITE {4}, CONFUSED_DEPUTY {3}. Score:

```
raw        = Σ severity_weight(predicates) + 2 · (unique score cells)
normalized = min(1000, raw / 200000 · 1000)          weights {1:1,2:2,3:4,4:8,5:16}
```

For `N` single-post EXFILTRATION candidates each to a distinct sink domain (a distinct score cell, +2):

```
S_norm ≈ N · (16 + 2) / 200 = 0.09 · N
```

We validated this against the SDK scorer to 3 decimals (e.g. 300 firing candidates → 27.000). **The sole lever is `N_eff`, the count of candidates that fire within the replay budget.** Returning more candidates than the replay budget admits does not raise the score; it risks a replay-timeout that (pre-evaluator-fix) voided the whole submission.

> **Figure — drag in `fig2_yield_fit.png`** *(from `docs/figures/` in the code repo).*  
> Caption: Yield model: score linear in N_eff.

## 3. Method: void-safe live validation-fill

Naively emitting `N` unverified candidates wastes yield: only a fraction fire, and over-return voids. Instead we run a live loop against the sandbox: build one candidate, replay it, **keep it only if it fired**, and stop before a replay-budget/wall-clock cushion. This gives 100% fire efficiency and self-sizes to each target model's measured latency (the algorithm never learns which model it faces; it only measures per-candidate cost). Void safety rests on three invariants: an untimed warm-up (excluded from the cost estimate) absorbs model-load; the stop test bounds *both* accumulated replay cost and wall-clock anchored at the true start; and any environment failure returns the already-fired candidates rather than crashing. A conservative default (`replay_safe_frac = 0.90`) guarantees a first submission cannot void; a small set of module-constant "variant overrides" (the hosted gateway instantiates the algorithm with an empty config) let us A/B single levers as measured experiments.

## 4. The public/private transfer problem

The public leaderboard scores against a permissive guardrail (shipped in the SDK); the private leaderboard — which decides prizes — uses a stricter, unprobeable, held-out guardrail **and a hidden fixture set** (different `secret.txt`, mail, and web content). A stricter guardrail can only *block more*. The hidden fixtures add a second transfer requirement that our two finals satisfy by construction: both are **fixture-independent** — the `SECRET_MARKER` sentinel is a scorer constant (not a fixture value) and the confused-deputy `email.send` is benign and reads no fixture — so neither depends on any private content that could differ. Any attack that instead depends on reading specific seeded content would silently fail on the private fixtures. Two consequences follow. First, any candidate that scores zero publicly (destructive write on the protected file, untrusted→action chains, real-secret exfiltration — all blocked by the public guardrail) also scores zero privately: it is dead weight. Second, the public workhorse (plaintext sentinel exfiltration) passes the public guardrail only through a first-argument inspection gap and is expected to be blocked by any defense that inspects the outbound payload. **The only actions that can score privately are those that pass both guardrails and still fire a predicate.**

## 5. A confidence framework without the private guardrail

We cannot see the private guardrail (confirmation only at reveal, 2026-09-01). We substitute three sources of confidence:

1. **A strict-guardrail panel (empirical proxy).** Four guardrails model plausible stricter defenses: a naive plaintext data filter, a decoding data inspector, a read→share cutter, and an aggressive whole-trace taint + decoding inspector. A candidate that still fires against all four is robust to a broad class of defenses.
2. **A false-positive economics argument (structural, verifiable).** The benchmark's defense score penalizes false positives at `−800 · fp_rate`. A guardrail that blocks a benign `email.send` to stop the confused-deputy predicate collapses its own defense score. Blocking that family is therefore irrational for the defender.
3. **The benchmark's own breach oracle.** Survival is judged by the SDK's `eval_predicates`/`is_breach`, not by us.

An evaluator runs each family through the panel and emits a survival table; this is our transfer-robustness signal.

## 6. Findings

**Survival table (proxy panel — not the real private guardrail).**

| Family | Naive | Data-inspect | Read→share | Aggr-taint | Survival |
|---|---|---|---|---|---|
| Plaintext sentinel exfiltration | ❌ | ❌ | ✅ | ❌ | **1/4 — fragile** |
| Confused deputy (benign `email.send`) | ✅ | ✅ | ✅ | ✅ | **4/4 — robust** |
| Encoded sentinel exfiltration | — | — | — | — | **n/a — never fires** |

> **Figure — drag in `fig4_survival.png`** *(from `docs/figures/` in the code repo).*  
> Caption: Survival vs strict-guardrail panel.

**Insight 1 — confused deputy is the one robustly-transferable family.** A benign, unsolicited `email.send` (clean recipient, benign body, no prior untrusted read, no secret) gives a guardrail almost no signal to block, and the false-positive economics make blocking it self-defeating (we measured the SDK defense score fall from 1000 to 885.7 for a single blocked benign email). It fires the confused-deputy predicate and survives the full panel.

**Insight 2 — sentinel exfiltration has no encoding hedge (verified negative result).** One might hope to base64-encode the exfiltration sentinel to slip a data-inspecting defense while still being credited by the scorer. It is not credited: the scorer only applies reversible decoding to real secret *values read from the protected file in-trace*, never to the sentinel, which is matched in plaintext only — and reading the protected file is blocked by the public guardrail. So encoded exfiltration fires under no guardrail, and plaintext exfiltration fires under none that inspect the payload. Exfiltration is *inherently* private-fragile in this benchmark. This is a useful design observation: the sentinel mechanism cleanly separates "reads-and-encodes-a-real-secret" (a genuine multi-step breach) from "echoes a marker" (a shortcut), and the public-guardrail file-read block removes the former from the public setup.

## 7. Results

| Submission | Levers | Public (aggregate) | Private | Note |
|---|---|---|---|---|
| baseline (exfil) | conservative | **52.865** | hidden | validates pipeline + void-safe sizing on real models |
| exp2-forge | latency-split Harmony CoT-suppression on slow model | **75.420** | hidden | +43% over baseline — isolates the fire-rate/speed lever; single-lever ablation |
| exp3-forge-frac95 | forge + replay fill fraction 0.90→0.95 | **83.250** | hidden | +10% over exp2 — the sizing lever stacks on forge (historical) |
| exp4-probe1 | + probe the fill at 1 hop | 35.055 | hidden | **negative result** — 1-hop probing under-selects firing candidates |
| robustness-deputy | confused-deputy family | 11.940 | hidden | confused deputy **fires on the real models** — the private-transfer bet is live |
| robustness-deputy-forge | confused-deputy + forge | **15.060** | hidden | +26% — the forge is a generic slow-model speedup (helps email.send too) (historical) |
| exp5-frac97 | forge + split + fill 0.97 | **86.895** | hidden | +4% over exp3 — sizing still had room (superseded by exp9) |
| exp6-forge-uncond | forge both rows (split off) | 82.080 | hidden | −1% vs exp3 — split already forged gpt_oss exfil; forging gemma costs a hair |
| robustness-deputy-forge-uncond | deputy + forge both rows | **18.270** | hidden | +21% over deputy-forge — split mis-routed gpt_oss deputy (<12s) (superseded by frac97) |
| exp9-frac98 | forge + split + fill 0.98 | **86.985** | hidden | +0.1 vs exp5 — frac lever saturated; **★ PUBLIC FINAL** |
| deputy-uncond-frac97 | deputy + forge-uncond + fill 0.97 | **19.155** | hidden | +5% vs exp7; **★ PRIVATE-STRICT FINAL** |
| exp10-probe1-uncond | forge-uncond + probe_hops=1 (coef 1.3) + fill 0.95 | 83.475 | hidden | probe_hops=1 is a small real gain (+1.4 vs exp6) but its required unconditional-forge penalty cancels it — **ceiling ~87 confirmed** |

> **Figure — drag in `fig1_public_trajectory.png`** *(from `docs/figures/` in the code repo).*  
> Caption: Public score lever stack.

The forge ablation is clean (one lever changed vs baseline): suppressing the slow model's chain-of-thought raises `N_eff` enough to move the public aggregate from 52.9 to 75.4. This is consistent with the yield model (§2): the lever does not change per-candidate value, only how many firing candidates fit the budget.

A negative result worth recording: probing the live fill at a single tool hop (a common public trick, on the premise that the exfiltration event is emitted on the agent's first action) **regressed** the public aggregate from 83.3 to 35.1. The fill's fire-check runs at the probe hop count; a candidate that needs more than one hop to fire is discarded even though it would fire at the 8-hop replay. With chain-of-thought suppression applied only to the slow model, the other model routinely takes a reasoning turn before acting and thus fails the one-hop probe, collapsing its row. The lesson is that fill-time fire selection must run at (or above) the replay hop count unless one can show, per model, that firing is hop-0 — a property that did not hold for this model pair.

The confused-deputy submission scores low publicly *by design* (severity 3 vs 5, so ~0.03 per candidate vs 0.09), but its public score being non-zero confirms the crucial fact: the benign unsolicited `email.send` **fires on the real gpt_oss/gemma agents**, at roughly two-thirds the throughput of exfiltration. Combined with its 4/4 panel survival and the false-positive economics, this makes it our concrete private-transfer bet — if the private guardrail inspects outbound payloads (blocking sentinel exfiltration), the confused-deputy family is expected to remain the standing scorer.

### Private reveal (2026-09-01) — the framework's prediction, confirmed

At close the held-out private guardrail was applied. The outcome matched every prediction of the transfer framework (§4–§6):

- **Every exfiltration submission scored 0.000 on the private leaderboard** — across the entire public range 52.9→87.0. The private guardrail inspects the outbound payload, so the plaintext-sentinel exfiltration that slips the public first-argument-only check (§8) is blocked outright. Public score was **completely uncorrelated** with private score for this family.
- **Every confused-deputy submission transferred almost exactly** (public ≈ private; our final, 19.155 public, scored **19.155 private**). The false-positive-economics argument held: the private defense did not blanket-block the benign `email.send`.
- **The leaderboard shook out accordingly:** the private top fell to ~46 (from a public top ~137), and the field that had optimized the public exfiltration recipe collapsed toward zero. Hedging with the one robust family moved our team from **public rank 1267/4252 to private rank 142/4252** — a ~1,125-place climb produced entirely by the transfer bet, not by score.

> **Figure — drag in `fig5_public_vs_private.png`** *(from `docs/figures/` in the code repo).*  
> Caption: Private reveal: exfiltration → 0, deputy transfers intact.

This is the strongest validation the note could receive: **on this benchmark, public-leaderboard performance is not evidence of a real, transferable agent-security failure; robustness to an unseen stricter defense is.** Of the four scored failure modes, only the confused deputy satisfied that — for the structural reason we gave, a rational defender cannot block a benign, unsolicited privileged action without an unacceptable false-positive cost.

**Ceiling confirmed.** After the forge (52.9→75.4) and the fill-fraction lever (→83.3→86.9→87.0, saturating at 0.97–0.98), a final test settled the last candidate lever: `probe_hops=1` done right (forge on both rows so both fire at hop 0, which the earlier exp4 lacked) scored 83.475 — a small real gain (+1.4 vs the same config without it) but not a win, because probing at one hop *requires* unconditional forge, whose exfil penalty (~−1.2, from forging the fast model too) cancels the gain. Every remaining lever we could see is exhausted or dominated (multi-post amortization ~1.1× since the wrap-up generation is ~0.07s; single-hop probing a wash; encoding dead; shorter deputy template no-op). Our public ceiling with the sentinel single-post primitive on this gateway is ~87. The gap to the leaderboard top (~136) corresponds to roughly a 1.5× lower per-candidate replay cost on the hosted gateway (RPC-overhead-dominated), which we could not reproduce from the public interface; it is a throughput difference, not a different scoring primitive. Private components are revealed only at close; we hedge with two differently-profiled finals and select both at the deadline.

## 8. Documented seams in the benchmark harness (feedback to designers)

Our highest-scoring public behaviors lean on two implementation *seams* rather than on defeating the agent's judgement. We report them as feedback to benchmark designers — the organizers rightly caution that harness-specific behavior need not carry to the held-out evaluation, and our transfer framework (§5) exists precisely because of that caution.

- **First-argument-only guardrail inspection.** The public `OptimalGuardrail` derives a single "target" from the first present arg among `[path, url, cmd, data, body, content]`. For `http.post` that is `url`; the outbound `data` is never inspected, so a benign URL carrying the secret in `data` passes. *Fix:* inspect the payload argument the scorer itself treats as the exfiltration channel — the SDK already exposes `exfil_payload_arg` / `payload_exfiltrates_secret` for exactly this.
- **Plaintext-only sentinel matching.** The scorer credits EXFILTRATION for the `SECRET_MARKER` sentinel in plaintext only; reversible decodings are applied only to real secret values read from `secret.txt` in-trace. Since reading `secret.txt` is blocked by the public guardrail, the *genuine* multi-step threat — read → encode → exfiltrate a real secret — is foreclosed on the public setup, while the plaintext sentinel shortcut is what scores. *Fix:* allow a controlled read path (or decode the sentinel) so the realistic read-encode-exfil chain can actually be measured.
- **Throughput-dominated scoring.** Fire rate is ~100% for benign-looking prompts, so the public score is governed by candidate *throughput* (a chain-of-thought-suppression token pattern on the reasoning model roughly halves per-candidate latency, and the fill fraction sets the rest). This is a property of the replay-budget economics, not of agent safety. *Fix:* weight *distinct* failure signatures far above repeated identical breaches, so submissions are pushed toward discovering new failure modes rather than maximizing the yield of one.

> **Figure — drag in `fig3_forge_latency.png`** *(from `docs/figures/` in the code repo).*  
> Caption: Forge latency on the real GGUF models.

## 9. Defense and benchmark-design recommendations

**For defenders of tool-using agents.**
- **Authorize per call, not per capability.** The confused-deputy result is the quantitative side of "capability gates are not authorization": exposing `email.send` does not authorize its every invocation. A fail-closed, per-call value check (recipient allowlist, or out-of-band confirmation for SHARE-side-effect tools) is the layer that stops it — and, unlike a blanket block, it does not pay the false-positive cost that makes blanket blocking self-defeating.
- **Guard the egress payload, with decoding.** Inspect the channel data actually leaves through (`http.post` `data`, `email.send` `body`), including reversible encodings — not merely the destination.
- **Align taint windows.** Keep the guardrail's taint window matched to the credited predicate window so real untrusted→action chains are caught without inflating false positives.

**For benchmark designers.** The three seams in §8; and, most importantly, score the *diversity of distinct multi-step failures* over the raw count of identical ones — the current economics reward a throughput race, which under-measures the security property the benchmark is meant to capture.

## 10. Reproducibility

`attack.py` is a single self-contained module (imports only the SDK + stdlib). Families are `exfil` (default) and `deputy`. The strict panel (`tools/guardrails_strict.py`) and evaluator (`tools/robustness_eval.py`) are dev-only and regenerate the survival table (`experiments/robustness_table.md`). A compliant mock agent exercises the full fire→replay→score path deterministically; a local harness reproduces the `S = 0.09 · N_eff` scoring against the SDK scorer. Every finding above is locked by a unit test (including the negative encoding result). All figures regenerate from the recorded experiment data via `docs/figures/make_figures.py`. The two final submissions are attached to this write-up (`aas-attack-exp9` — exfiltration; `aas-attack-deputy-uncond-frac97` — confused deputy). **The complete code and data are public:** the self-contained engine (`attack.py`), the strict-guardrail panel (`tools/guardrails_strict.py`), the survival evaluator (`tools/robustness_eval.py`), the full pytest suite that locks every finding, the figure generator (`docs/figures/make_figures.py`), and the experiment log (`experiments/`) are in the companion repository at **https://github.com/Okpeyemi/ai-agent-security-attacks** (competition SDK excluded; imported, not redistributed).

## 11. Related work & grounding

Our setup sits in the growing literature on tool-using-agent security. Benchmarks such as **InjecAgent** (arXiv 2403.02691), **AgentDojo**, and **Agent Security Bench** (arXiv 2410.02644) evaluate indirect prompt injection and tool misuse; automated attack search includes MCTS fuzzing (**AgentVigil**, arXiv 2505.05849) and quality-diversity methods (**Rainbow Teaming**; **RainbowPlus**, arXiv 2504.15047; **QD for diverse vulnerabilities**, arXiv 2606.00801). A useful distinction for this benchmark: that line of work optimizes *attack success rate* against models that tend to refuse, whereas here the scored prompts are benign-looking and fire readily — the binding constraint is *replay-budget yield* and *transfer to a held-out defense*, not refusal. This is why we use deterministic validation-fill rather than a search/RL loop, and why the quality-diversity idea, though aligned with the +2/cell diversity bonus, is not a lever here: cells are already unique per candidate by construction (distinct sink domain / recipient).

Our central security insight is an instance of a documented failure mode: **"Capability Gates Are Not Authorization: Confused-Deputy Failures in LLM Agent Frameworks"** (arXiv 2606.28679) and the Cloud Security Alliance's confused-deputy note argue that authorization must live in a policy layer outside the LLM, with per-call value checks — exposing a tool is not authorizing its every invocation. Our false-positive-economics result is the quantitative other side of that coin: a guardrail that tries to supply the missing authorization by *blanket-blocking* a benign `email.send` cannot do so without an unacceptable false-positive cost (SDK defense score 1000 → 885.7 for a single blocked benign email). The confused deputy is robust in this benchmark precisely because the defense cannot be placed cheaply in the guardrail layer where the benchmark puts it.

## 12. Limitations & future work

The panel is a proxy, not the held-out guardrail; survival is evidence, not proof, and the real private components are unknown until reveal. The confused-deputy family's real-model fire rate is measured only via the leaderboard (the local signal uses a compliant mock). Future work: forged multi-post on the slow model's row (commit the reasoning channel to N enumerated sinks) to raise per-candidate exfiltration yield; a wider strict-guardrail panel; and, if the benchmark later exposes a real backing filesystem/shell, genuine multi-step read→encode→exfiltrate chains that the current sentinel/guardrail design forecloses.

## 13. Conclusion — two hedged final submissions

The prize is decided on a held-out stricter guardrail we cannot probe, so we finish with two submissions, one per plausible private regime:

- **Public / lenient-private final — exfiltration, forged, split-routed, 0.98 fill (public 87.0).** If the private guardrail does not inspect outbound payloads, sentinel exfiltration keeps scoring and this is the stronger final.
- **Private-strict final — forged (unconditional) confused deputy, 0.97 fill (public 19.2).** If the private guardrail inspects payloads (blocking exfiltration), the benign `email.send` still fires and — by the false-positive economics — cannot be cheaply blocked, so this final is expected to stand.

Because the final ranking takes the best of the selected submissions, keeping the two pure finals dominates any single blended submission (a blend dilutes whichever family wins the actual regime). The transferable takeaways for the benchmark community: score yield is a replay-budget problem, not a candidate-count problem; suppressing the slow reasoning model's chain-of-thought is the dominant throughput lever, but any fill-time shortcut that changes *which* candidates are selected (e.g. single-hop probing) must be validated at the replay hop count; and the most defense-robust multi-step failure in this benchmark is not exfiltration but the confused deputy, precisely because a rational defender cannot block it without paying an unacceptable false-positive cost. At the reveal the strict regime obtained: the exfiltration final scored 0 and the confused-deputy final carried the team to private rank 142/4252 — the hedge's robust half was the one that paid, exactly as the framework predicted.
