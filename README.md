# accountable-ft

Jon Chen and Eitan Green, CS 224V fall 2026. Design, every cited result and the limits in [DECISIONS.md](DECISIONS.md), stack, clusters and commands in [OPS.md](OPS.md).

Can fine-tuning make a model's stated reasons predict what it does when the facts change? We train Qwen3.5-9B on rule-based eligibility cases: invented policies with exact labels from a rule engine, plus real mortgage, SNAP and IRS dependent rules. Explanation SFT (supervised fine-tuning) learns the decision and an engine-verified explanation. The matched control, decision-only SFT, sees the same rows with the explanation tokens masked out of the loss. The main score is simulatability gain: how much better a frozen simulator (Gemini 3.5 Flash-Lite, Claude Opus 5.5 as the 2nd) predicts the model's answer after an edit when it sees the model's own explanation rather than another case's. The simulator never sees the case.

## Results

Paired simulatability gain, explanation SFT minus decision-only, seed by seed, 95% CI clustered by rule family. v1 = unseen families of the invented training domains, mortgage = 24 held-out mortgage families. Logs `final-v1-gemini-eval-abaa830-20261120-1542`, `final-mortgage-gemini-eval-abaa830-20261120-1542`, `final-v1-opus-eval-abaa830-20261120-1542`, `final-mortgage-opus-eval-abaa830-20261120-1542`.

| training mix | v1, Gemini | mortgage, Gemini | v1, Opus | mortgage, Opus | accuracy, v1 |
|---|---|---|---|---|---|
| round 1: grant, trial, review | 0.081 [0.043, 0.123] | 0.038 [-0.018, 0.094] | 0.161 [0.129, 0.195] | 0.091 [0.048, 0.137] | 0.004 [-0.008, 0.016] |
| round 2: grant, trial, mortgage | 0.041 [0.007, 0.078] | 0.094 [0.036, 0.151] | 0.120 [0.086, 0.151] | 0.170 [0.129, 0.211] | 0.033 [0.020, 0.049] |
| mortgage only, seed 0 | -0.005 [-0.044, 0.036] | 0.066 [-0.018, 0.150] | 0.009 [-0.038, 0.056] | 0.024 [-0.036, 0.083] | 0.006 [-0.018, 0.031] |

## Findings

- On invented rules, trained explanations are case-specific and need the right reason. Swapping the cited facts for true non-binding ones (same decision, format, length) costs +9.1 points of gain on v1, every seed clear of 0. The gain holds on permit, an invented domain never trained on (+10.0 [6.5, 13.6], Opus +13.3).
- Explanation SFT matches decision-only on v1 accuracy (0.976 vs 0.972) and is the only condition with valid explanations (0.756 vs 0.000).
- Explanations do not reveal the model's errors. Where the model is wrong after an edit, a shuffled explanation tracks it at least as well as its own.
- Real-rules transfer is not shown. The pre-registered grid test (IRS dependent, held out) failed: gain is negative for every mix (-6.6 to -3.6). On mortgage the gain is format-driven (own minus wrong-reason -0.2), and a prompted untrained explanation ties it.
- Cause on IRS dependents: of 2,309 wrong decisions, 690 cite a rule that an exception waives and 757 a rule for the other claim type. Training taught the format, not the scope of the rules.
- Mix pick: train on invented + real, for correctness (44% vs 36% real-only, 39% invented-only over 6 tests) and accuracy (87% vs 80%, 78%). Not a data-volume effect: every mix has 3,600 rows and about 268 root cases, and real-only has the most text. Mixed has 2x the rule families at half the rows per domain. On gain (leaky simulator prompts, rerun under way, see DECISIONS) the simulators seemed to disagree: Gemini puts mixed above real-only in 9 of 9 seed pairs over the 6 tests, Opus in 3 of 9, and Opus favors real-only on mortgage (+6.5 [2.8, 10.5]) (log `final-grid-seeds-2005f39-20261120-1856`), which holds with 60 new families pooled in (+6.0 [4.1, 7.9], log `final-mortgage-split-x-pool-grid-opus-eval-4776607-20261121-0500`).

## Files

- `engine.py` rule engine, `gen.py` data generator, `domains/` policies.
- `infer.py` model runner and simulator passes, `evaluate.py` metrics and CIs, `train.py` LoRA SFT with the matched loss.
- `cluster.sh`, `score.sh`, `sim.sh`, `resim.py` (simulator reruns) jobs, `compare_sims.py`, `errors.py`, `seeds.py` (grid gains seed by seed) analyses, `tests/test_all.py`.
- `runs/` outputs, `data/` datasets. Commands in [OPS.md](OPS.md).
