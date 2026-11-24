# accountable-ft

Jon Chen and Eitan Green, CS 224V fall 2026. Design, every cited result and the limits in [DECISIONS.md](DECISIONS.md), stack, clusters and commands in [OPS.md](OPS.md).

Can fine-tuning make a model's stated reasons predict what it does when the facts change? We train Qwen3.5-9B on rule-based eligibility cases: invented policies with exact labels from a rule engine, plus real mortgage, SNAP and IRS dependent rules. Explanation SFT (supervised fine-tuning) learns the decision and an engine-verified explanation. The matched control, decision-only SFT, sees the same rows with the explanation tokens masked out of the loss. The main score is simulatability gain: how much better a frozen simulator (Gemini 3.5 Flash-Lite, Claude Opus 5.5 as the 2nd on the grid) predicts the model's answer after an edit when it sees the model's own explanation rather than another case's. The simulator never sees the case.

## Results

Paired simulatability gain (Gemini), explanation SFT minus decision-only, seed by seed, 95% CI clustered by rule family. v1 = unseen families of the invented training domains, mortgage = 24 held-out mortgage families. Logs `final-v1-gemini-eval-e6fbbe1-20261124-1308`, `final-mortgage-gemini-eval-e6fbbe1-20261124-1320`.

| training mix | gain, v1 | gain, mortgage | accuracy, v1 |
|---|---|---|---|
| round 1: grant, trial, review | 0.099 [0.066, 0.131] | 0.008 [-0.036, 0.050] | 0.004 [-0.008, 0.016] |
| round 2: grant, trial, mortgage | 0.104 [0.071, 0.137] | 0.074 [0.015, 0.131] | 0.033 [0.020, 0.049] |
| mortgage only, seed 0 | -0.008 [-0.058, 0.041] | 0.070 [-0.019, 0.158] | 0.006 [-0.018, 0.031] |

## Findings

- On invented rules, trained explanations are case-specific and need the right reason. Swapping the cited facts for true non-binding ones (same decision, format, length) costs +7.9 points of gain on v1, every seed clear of 0. The gain holds on permit, an invented domain never trained on (+9.9 [6.6, 12.9]).
- Explanation SFT matches decision-only on v1 accuracy (0.976 vs 0.972) and is the only condition with valid explanations (0.756 vs 0.000).
- Real-rules transfer is not shown. The pre-registered grid test (IRS dependent, held out) failed: gain is negative for every mix (-7.9 to -3.1). Round 1 mortgage gain is +0.8 points, and a prompted untrained explanation ties it.
- Cause on IRS dependents: of 2,309 wrong decisions, 690 cite a rule that an exception waives and 757 a rule for the other claim type. Training taught the format, not the scope of the rules.
- Mix pick: train on invented + real, for correctness (44.5% vs 35.8% real-only, 39.0% invented-only over 6 tests) and accuracy (87.1% vs 79.8%, 78.2%) (log `final-grid-seeds-e6fbbe1-*`). Not a data-volume effect: every mix has 3,600 rows and about 268 root cases, and real-only has the most text. Mixed has 2x the rule families at half the rows per domain. On gain, mixed and real-only tie: own minus wrong-reason, mix - real, pooled over 84 mortgage and 84 SNAP families, is +0.7 / +0.8 on mortgage and -1.0 / -1.0 on SNAP (Gemini / Opus, every CI covers 0). The Opus real-only edge on the registered paired gain (mortgage -3.4 [-6.0, -0.8]) comes from subtracting decision-only runs, whose placeholder lines Opus reads.

## Files

- `engine.py` rule engine, `gen.py` data generator, `domains/` policies.
- `infer.py` model runner and simulator passes, `evaluate.py` metrics and CIs, `train.py` LoRA SFT with the matched loss.
- `cluster.sh`, `score.sh`, `sim.sh`, `resim.py` (simulator reruns) jobs, `compare_sims.py`, `errors.py`, `seeds.py` (grid gains seed by seed) analyses, `tests/test_all.py`.
- `runs/` outputs, `data/` datasets. Commands in [OPS.md](OPS.md).
