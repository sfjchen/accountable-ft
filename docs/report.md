# Accountable model training: why, how, what

Jon Chen and Eitan Green, CS 224V, mentor Cyrus Zhou. One page. Full detail and sources in `PLAN.md`.

## Why

A model can give a convincing explanation and still decide for other reasons. For decisions that have to follow written rules (eligibility, compliance, review), that makes the explanation useless: you cannot tell what the model relied on, what it assumed, or what would change its answer. We ask: does supervising the reasons, not just the decision, make a model's stated reasons actually track its decisions?

## Claim we can test by Dec 4

Fine-tuning on verified accounts (which facts, which rules, which defaults) improves how well a model's account predicts its own behavior under edits, beyond fine-tuning on decisions alone, at no real accuracy cost. We measure 2 properties and claim nothing about a 3rd:

- Policy-grounded: the cited facts and rules justify the decision under the policy. Checked by a rule engine.
- Behaviorally faithful: the account predicts the model's own answer after an independent edit. Checked by rerunning the model.
- Not claimed: that the account is causally how the model computed the decision.

## How: 4 structural decisions

1. Invented policy domains, exact oracle. 4 made-up domains (grant, trial, review, permit) with 8 to 15 rules each, exceptions and defaults, over small finite facts. A Python rule engine gives the gold decision, a gold account, the smallest edit that flips the decision, and whether a set of facts suffices. Everything is checkable, nothing leaks from pretraining. Cost: no claim about real policy text, so we add a 40-item realism check as a descriptive aside.
2. Matched control. Account SFT and decision-only SFT see the same cases, the same prompts and the same sequences. The only difference is whether account tokens are in the loss. Any gap is then attributable to account supervision, not to more data or a better format.
3. Three views of each case, split by rule family. Table, prose, prose with derived facts. Held-out rule families and a held-out domain (permit) test transfer across policy structure and vocabulary. "Unseen family" means new threshold and rule combinations, not new rule shapes. Permit is the honest transfer test.
4. Behavioral endpoint, no LLM judge. Primary endpoint dSim: a frozen external simulator that sees only the policy, the model's decision, its account and an edit (never the case) predicts the model's fresh post-edit decision. We score own account minus a shuffled account from the same policy, so format alone earns nothing. Self-prediction (the model predicting itself) is secondary, since a model with the case in view just re-solves it. Accuracy is a non-inferiority constraint (3-point margin), and every number comes with family-clustered CIs and a repeat-without-edit control.

## What exists now

- Dataset v1: about 5,000 cases, 3 views, 72 held-out families, 60 permit families, prose written by Gemini and checked by extraction, 100-item blind sample for hand labeling.
- Harness: generation, answering, edit bank, self-prediction, external simulation, evaluation with clustered CIs. 44 tests. Repo `sfjchen/accountable-ft`.
- 2 prompting pilots on the same 150 held-out cases (logs `v1-lite-eval-145ad3c-20261105-1758`, `qwen9b-lite-eval-c479313-20261107-0147`; simulator rows rerun at 52322ce, logs `v1-lite-simulate-52322ce-20261107-0252`, `v1-lite-eval-52322ce-20261107-0253`, `qwen9b-lite-simulate-52322ce-20261107-0253`, `qwen9b-lite-eval-52322ce-20261107-0254`, n=176 shared bank items):

|                       | Gemini 3.5 Flash-Lite      | Qwen3.5-9B base           |
| --------------------- | -------------------------- | ------------------------- |
| accuracy              | 0.77                       | 0.60                      |
| account validity      | 0.22                       | 0.07                      |
| sim_acct              | 0.68 [0.60, 0.74]          | 0.82 [0.76, 0.89]         |
| sim_shuf              | 0.64 [0.55, 0.72]          | 0.73 [0.66, 0.81]         |
| sim_const_unchanged   | 0.69 [0.60, 0.78]          | 0.85 [0.78, 0.92]         |
| sim_oracle            | 0.62 [0.56, 0.69]          | 0.52 [0.46, 0.58]         |
| dSim                  | 0.04 [-0.06, 0.13]         | 0.09 [0.04, 0.15]         |
| dSim [changed]        | 0.15 [0.00, 0.26] n=55     | 0.19 [0.03, 0.40] n=26    |
| dSim [unchanged]      | -0.01 [-0.13, 0.13] n=121  | 0.07 [0.02, 0.13] n=150   |
| gross (acct - noacc)  | 0.24 [0.14, 0.34]          | 0.41 [0.33, 0.50]         |

Both models never say "cannot determine" and both give mostly invalid accounts, so accounts are where the headroom is. That is the shape the comparison needs.

## Next

Nov 9-16: account SFT vs decision-only SFT on Qwen3.5-9B, 3 seeds each, LoRA, GPU via FarmShare or RunPod. Nov 17-23: held-out and permit evaluation, error analysis. Nov 24-30: report and slides. Relabel round (CREDIT-style) only if account SFT is not already at the accuracy ceiling.

## Risks

Gains that come from accuracy rather than accounts (handled by the matched control and the non-inferiority margin), sampling noise read as flips (greedy decoding plus the repeat control), too few clusters for dSim (72 families, measured ICC, power redone on the next clean run), GPU access.
