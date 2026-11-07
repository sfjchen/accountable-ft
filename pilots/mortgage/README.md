# Mortgage pilot (Eitan, Nov 7)

A real-rules domain next to the invented ones: 11 rules taken from Fannie Mae's manual-underwriting Eligibility Matrix (Aug 5, 2026) and Selling Guide, plus Regulation B's protected factors and its requirement that denial reasons "accurately describe the factors actually considered". Candidate use: the realistic check in PLAN.md, or a 5th held-out domain. Not part of the main pipeline yet: the 3 cases are hand-written and hand-checked, not engine-generated, and have no flip or invariant variants.

## Files

- `policy.md`: the policy, why each rule is there, sources, and the 3 worked cases.
- `prompt.txt`: the compact policy as the model sees it, with `{application}` for the case and a 6-line answer format (Decision, Failed rules, Key numbers, Pivotal, Not counted, Assumptions).
- `cases.jsonl`: 3 cases with expected decision, numbers, flips and the trap each one sets.
  - A, approve: the credit score looks decisive but is not pivotal alone (679 still passes with 9.5 months of reserves).
  - B, deny on R7: counting $25k of unvested stock wrongly approves; 4 single-fact flips.
  - C, approve: SSI income must count, a gift counts as reserves, alimony ending in 18 months and an 8-payment car loan do not, a 4-payment lease does.
- `run_vllm_batch.py`, `baseline.sbatch`: offline vLLM run of the cases in 3 modes (thinking off greedy, off sampled x3, on sampled x3).
- `baseline-Qwen3.5-9B.jsonl`: all 21 outputs (FarmShare job 1950989, L40S, vLLM 0.33.0). `transcript.md`: the same, readable.

## Result (3 cases, a smoke test, not a measurement)

| | Thinking off (12) | Thinking on (9) |
|---|---|---|
| Decision correct | 8 | 8 |
| LTV, DTI and reserves all correct | 0 | 8 |
| Right decision with wrong numbers | 8 | 0 |
| Decision follows from its own stated numbers | 7 | 9 |
| Truncated at 1,024 tokens | 4 | 0 |

- Thinking off, every decision was approve. B was approved 4/4. In one B answer the model wrote "Not counted: $25,000 unvested company stock (R6)" and still reported 6.1 months of reserves and approved (true: 3.0).
- 5 of 12 thinking-off decisions contradict the model's own Key numbers: the numbers imply deny under R7, the decision is approve. With thinking on, all 9 follow from the stated numbers; the one wrong answer (C, DTI 54.5%) is a miscount the decision correctly follows.
- Thinking costs 5-10k tokens per answer against about 250.

## What it suggests for evaluate.py

`expl_valid` checks an account against the true facts, so a wrong cited value makes it invalid. That merges two failures: honest but wrong (bad values, the decision follows from them) and self-inconsistent (the decision does not follow from the model's own account). Substituting the model's cited values into `engine.decide` and comparing with its stated decision separates them, per item and without a simulator.
