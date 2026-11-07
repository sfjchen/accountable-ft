# Accountable model training: the walkthrough

Jon Chen and Eitan Green, CS 224V, mentor Cyrus Zhou. Read top to bottom, each level adds detail. Everything here is in `PLAN.md` with sources.

## 1. Why

- Models explain decisions, but the explanation may not be what drove the decision.
  - A model can cite rule 3 and actually decide on rule 7, or on a fact it never mentions.
  - For rule-based decisions (eligibility, compliance, review) that makes the explanation useless for audit.
- Question: can fine-tuning make the stated reasons actually track the decisions?
  - Not "are the reasons plausible", but "do they predict what the model does when the facts change".

## 2. What we claim and what we do not

- Claim: training on verified accounts beats training on decisions alone at making accounts predictive, with no real accuracy loss.
  - An account = which facts, which rules, which defaults the decision rests on, plus the smallest change that would reverse it.
  - "Verified" = checked by a rule engine, not by a human or an LLM.
- Two properties we measure.
  - Policy-grounded: the cited facts and rules justify the decision under the policy. The engine checks this.
  - Behaviorally faithful: the account predicts the model's own answer after an edit it has not seen. We rerun the model to check.
- One property we do not claim.
  - Causal: that the account is how the model computed the answer. That needs interpretability tools we are not using.

## 3. How: the 4 design decisions

- Invented policy domains with an exact oracle.
  - 4 made-up domains (grant, trial, review, permit), 8 to 15 rules each, exceptions and defaults, facts with small finite domains.
  - A Python rule engine gives the gold decision, gold account, smallest flip, and "which facts suffice". z3 is a cross check only.
  - Why invented: nothing leaks from pretraining, every label is exact. Cost: no claim about real policy text. A 40-item realism check is a descriptive aside.
- A matched control.
  - Account SFT and decision-only SFT see the same cases, prompts and target sequences.
  - The only difference is the loss: the control zeroes the account tokens. Decision tokens carry equal weight in both.
  - So any gap is from account supervision, not from more data or a different format.
- Three views, split by rule family.
  - Each case appears as a table, as prose, and as prose with derived facts (date gaps, sums).
  - Train/dev/test split by rule family (which rule templates a policy uses), so test policies are new combinations and thresholds.
  - Permit is a whole held-out domain: the real transfer test. "Unseen family" is only threshold-and-combination transfer.
- A behavioral endpoint, no LLM judge.
  - Primary: dSim. A frozen external simulator sees the policy, the model's decision, its account and an edit, never the case, and predicts the model's fresh post-edit decision.
  - Score = accuracy with the model's own account minus accuracy with another case's account from the same policy (same decision line kept). Format earns nothing, only content.
  - Guardrails: an always-"unchanged" baseline and an oracle baseline sit next to every simulator number. Self-prediction (the model predicting itself) is secondary, because a model with the case in view just re-solves it.
  - Accuracy is a constraint, not the goal: the account model must stay within 3 points of the control.
  - Every number comes with a 95% CI clustered by rule family, and flips are read against a repeat-without-edit control.

## 4. The pipeline, step by step

- Generate: `gen.py` samples policies and cases per domain, the engine labels them, Gemini writes the prose, an extraction check drops prose that distorts a fact.
- Export: `scripts/sft_data.py` turns cases into chat examples with the account span marked, flagged items dropped.
- Train: `train.py`, LoRA on Qwen3.5-9B, condition account or decision, 3 seeds each, same fixed epoch for both.
- Answer: `infer.py` runs the trained model on held-out cases and on the edit bank.
- Edit bank: 782 edits built by the engine, 40% flip a decision, 30% should not, 15% remove a fact, 15% reveal a missing one. Flip edits are chosen to differ from the gold "smallest change" so the model cannot have memorized them.
- Simulate and evaluate: `infer.py --mode simulate`, then `evaluate.py` produces the table with CIs. `runs/README.md` has the exact commands.

## 5. Where we are (Nov 7)

- Data v1: about 5,000 cases, 3 views, 72 held-out families, 60 permit families, 100-item blind sample for us to hand-label.
- Harness: 55 tests, end to end on two prompting pilots, same 150 held-out cases (logs `v1-lite-eval-52322ce-20261107-0253`, `qwen9b-lite-eval-52322ce-20261107-0254`).

|                             | Gemini 3.5 Flash-Lite | Qwen3.5-9B base   |
| --------------------------- | --------------------- | ----------------- |
| accuracy                    | 0.77                  | 0.60              |
| account validity            | 0.22                  | 0.07              |
| dSim                        | 0.04 [-0.06, 0.13]    | 0.09 [0.04, 0.15] |
| always-"unchanged" baseline | 0.69                  | 0.85              |

- Both never say "cannot determine". Both give mostly invalid accounts. The simulator does not beat the trivial baseline yet.
- Reading: accounts are where the headroom is, accuracy has some too. That is the shape the comparison needs.
- Compute: FarmShare (Stanford, free), 6 nodes with 4 L40S 48 GB each, 4 GPUs per user. Environment and data are on the cluster, smoke jobs submitted Nov 7.

## 6. Next

- Nov 9-16: 6 training runs (2 conditions x 3 seeds), about 2 hours each on an L40S, then evaluation on the held-out families.
- Nov 17-23: permit transfer, error analysis, a second simulator family as a robustness check.
- Nov 24-30: report and slides.
- Relabel round (CREDIT-style) only if account SFT is below the accuracy ceiling.

## 7. Risks, one line each

- Gains that come from accuracy rather than accounts: matched control and the 3-point margin.
- Noise read as flips: greedy decoding, repeat control, a planned paraphrase-edit noise floor.
- dSim underpowered: 72 families, ICC measured, power redone on the first clean run.
- Queue time on FarmShare: RunPod ($1.19/h A100) as the fallback.
