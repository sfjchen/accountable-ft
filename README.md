# accountable-ft

CS 224V final project (Stanford, fall 2026). Jon Chen and Eitan Green, mentor Cyrus Zhou. This README is the working doc: the walkthrough first, then the technical reference. Reasoning and sources are in `PLAN.md`.

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
- Edit bank: 782 edits built by the engine, 40% flip a decision, 30% should not, 15% remove a fact, 15% reveal a missing one. Flip edits differ from the gold "smallest change" so the model cannot have memorized them.
- Simulate and evaluate: `infer.py --mode simulate`, then `evaluate.py` produces the table with CIs. `runs/README.md` has the exact commands.

## 5. Domains and rules

- How a yaml rule becomes logic (the yaml in `domains/*.yaml` is the single source).
  - `cond`: the rule holds iff cond, e.g. `requested_amount <= 90000`.
  - `unless: cond2`: rule := cond ∨ cond2, the exception waives it.
  - `scoped`, written `A or B`: conditional rule, trigger ¬A, requirement B. `near` marks the distractor case (trigger off, B false).
  - `derived_facts`: a named expression over source facts, never edited directly, e.g. `duration_weeks = (end_day − start_day) // 7`.
  - `defaults`: fill a missing fact before evaluation. The account must cite them as assumptions.
  - `params`: threshold placeholders. Family = templates, exceptions and defaults chosen. Policy = family with thresholds. Case = one applicant under one policy.
- Decision semantics.
  - All facts known: approve if every rule holds, else deny.
  - Facts missing after defaults: approve if every admissible completion approves, deny if every one denies, else "cannot determine".
  - Gold account = a sufficient set of cited facts, rules and defaults. Smallest flip = fewest fact changes that reverse the decision. Exact backtracking with a time budget.
- The 4 domains (facts / rule templates / defaults).
  - Grant, Halbrecht Early Inquiry Grants: 12 / 12 / 5. PhD-age cap with career-break exception, amount cap with community-lab exception, letter unless university, open data unless hospital, host types, start date, equipment cap, ethics, hospital travel cap, project length, equipment plus travel cap.
  - Trial, Protocol VX-118 enrollment: 12 / 13 / 4. Age range, biomarker floor with index exception, clearance floor with tier-A exception, washout, no prior drug, anticoagulant rules, consent window, composite score cap.
  - Review, SQM 2027 submissions: 16 / 14 / 6. Page limit with position-track exception, anonymity, dual submission, deadline with extension, supplement rules, author and reference caps, reviewer conflict, ethics statement, artifact license, total pages, coauthor window.
  - Permit, Marrowgate street equipment, held out: 12 / 10 / 3. Weight cap with operator exception, insurance, night work, operator level, crane, sidewalk notice, residential weight, night crew, lead time, placement length.
- Why grant, trial and review train and permit is held out.
  - Same rule shapes everywhere, so a held-out family is a new combination and permit is the real vocabulary transfer.
  - Every domain has derived facts and defaults, so assumptions show up in every case.
- Known data issues (`docs/audit_cd.md`, Nov 7).
  - Engine labels are sound. Gemini prose distorts about 10% of "cannot determine" items ("university" as "an academic institution", prose implying supplementary files).
  - 222 items are listed in `data/v1.flagged.txt` and dropped at export. The generator now rejects lossy enum sentences.
- Open between us.
  - Keep permit as the only held-out domain, or add a 5th (about $3 of prose and an afternoon of yaml) and hold out 2.
  - Hold whole rule templates out of training too, so "unseen" means new rule shapes.
  - Split the 100-item blind labeling (`data/v1.blind100.jsonl`, answers in the sibling file, do not open first).

## 6. What a case looks like

- Prompt = system line, the policy (about 10 numbered rules, 2 with exceptions), a 20-sentence case file with filler and shuffled facts, and the 4-line answer format. Full prompts are in the run files, cases in the `data-v1` release.
- Example, grant-p010-c01-reveal (prose, held-out family). Gold: approve. Qwen3.5-9B base: deny.
  - Qwen cited R5 (request over $90,000) and R6 (start before Jan 14). R5 is waived because the host is a community laboratory and the request is exactly the exception's $120,000 limit. R6 holds, the start is Feb 1.
  - The gold account needs 9 facts, including the career-break exception that waives R2 for a 9-year-old doctorate.
- Why base models score low: exceptions, boundary values and distractors in long prose, not trick wording.
  - Qwen's 309 wrong base answers: 196 approve called deny, 82 cannot-determine called deny, 16 deny called approve, 15 cannot-determine called approve.
  - Two failure modes cover 90%: missed exceptions and boundaries, and never abstaining.

## 7. Where we are (Nov 7)

- Data v1: about 5,000 cases, 3 views, 72 held-out families, 60 permit families.
- Harness: 55 tests, end to end on two prompting pilots, same 150 held-out cases (logs `v1-lite-eval-52322ce-20261107-0253`, `qwen9b-lite-eval-52322ce-20261107-0254`).

| | Gemini 3.5 Flash-Lite | Qwen3.5-9B base |
|---|---|---|
| accuracy | 0.77 | 0.60 |
| account validity | 0.22 | 0.07 |
| dSim | 0.04 [-0.06, 0.13] | 0.09 [0.04, 0.15] |
| always-"unchanged" baseline | 0.69 | 0.85 |

- Both never say "cannot determine". Both give mostly invalid accounts. The simulator does not beat the trivial baseline yet.
  - Reading: accounts are where the headroom is, accuracy has some too. That is the shape the comparison needs.
- Compute: FarmShare (Stanford, free), 6 nodes with 4 L40S 48 GB each, 4 GPUs per user. Environment, data and model are on the cluster, smoke jobs queued Nov 7. RunPod ($1.19/h A100) is the fallback.

## 8. Next

- Nov 9-16: 6 training runs (2 conditions x 3 seeds), about 2 hours each on an L40S, then evaluation on the held-out families.
- Nov 17-23: permit transfer, error analysis, a second simulator family as a robustness check.
- Nov 24-30: report and slides.
- Relabel round (CREDIT-style) only if account SFT is below the accuracy ceiling.

## 9. Risks, one line each

- Gains that come from accuracy rather than accounts: matched control and the 3-point margin.
- Noise read as flips: greedy decoding, repeat control, a planned paraphrase-edit noise floor.
- dSim underpowered: 72 families, ICC measured, power redone on the first clean run.
- Queue time on FarmShare: RunPod as the fallback.

# Technical reference

## Files

- `gen_z3_v0.py` — first generator (toy trial eligibility, z3). Kept as a cross-check only, the engine replaces it.
- `engine.py` — rule engine: decide, minimal sufficient sets (exact, over admissible completions), minimal flips up to radius 4, invariant edits, `is_valid_justification`.
- `gen.py` — generator: template families, policies, base cases and flip/invariant/missing variants in 3 views (table, prose, prose_derive), optional Gemini prose. `render_case()` re-renders edited cases for interventions.
- `domains/*.yaml` — 4 invented domains (grant, permit, trial, review): facts, derived facts, rule templates, defaults, prose vocabulary. Permit is the held-out domain.
- `tests/test_engine.py` — engine tests on hand-written policies plus brute-force cross-checks.
- Smoke run: `python gen.py --domains all --n-policies 4 --cases-per-family 10 --seed 0 --prose template --out data/smoke.jsonl`
- `infer.py` — one `Runner` over OpenAI-compatible endpoints (vLLM serve, OpenRouter), Gemini and offline vLLM, with fixed decoding, a response cache, `--rep` for the repeat control, `--mode bank` (intervention bank, `data/<name>.bank.jsonl`) and `--mode predict` (self-prediction with or without the frozen account).
- `evaluate.py` — all metrics with cluster bootstrap CIs, slices (primary: prose, unseen families, training vocabularies), paired comparisons, seed aggregates, coverage, checkpoint selection. Markdown to stdout, every number in JSON.
- `tests/test_evaluate.py`, `tests/fixtures/mini.jsonl` — parser, metric math on a 12-record hand-made fixture, bank, selection, bootstrap.

## Data

- `data/v1.jsonl` (not in git, about 150 MB) comes from `python gen.py --domains all --n-policies 120 --cases-per-family 5 --seed 0 --prose gemini --vertex --gemini-model gemini-3.5-flash-lite --workers 8 --out data/v1.jsonl > data/v1.gen.log`, with gcloud ADC on our GCP project. Gemini replies are cached in `data/.gemini_cache/`, so a rerun with the same seed costs nothing. Facts and gold depend only on the seed, except that a search can hit its 2 s budget on a loaded machine and mark that one item uncertified.
- `python scripts/data_report.py data/v1.jsonl --log data/v1.gen.log` writes `data/v1.stats.md` (counts, class balance, families, spend) and the blind sample `data/v1.blind100.jsonl`, with gold in `data/v1.blind100.answers.jsonl`. We each label the blind file before opening the answers.
- Each domain has 60 families of 2 policies with 5 base cases per family. Grant, trial and review split their families 30/6/24 into train/dev/unseen, so the unseen slice has 72 families (24 per domain) for clustered stats while train stays near 5.5k records. Permit's 60 families are the transfer slice. The previous dataset is kept as `data/v1.0.jsonl`.

## Training

`scripts/sft_data.py` exports chat rows (harness prompt, gold answer from `infer.format_target`, account span) and `train.py` runs LoRA SFT on Qwen3.5-9B with Unsloth and TRL on a CUDA GPU. Both conditions use the same export, and the loss per example is mean_dec + λ mean_acc (mean token loss over the Decision line plus end-of-turn, plus λ times the mean over the account lines), averaged over the batch. So the decision tokens carry the same total weight in both conditions however long the account is. The account condition uses λ = `--acc-weight` (default 1.0), the decision condition λ = 0 with the account labels set to -100.

- Stack (pinned in `train.PINS`, these co-install since unsloth caps trl at 1.15 and transformers at 5.17): `pip install torch==2.14.0 --index-url https://download.pytorch.org/whl/cu126 && pip install unsloth==2026.11.3 trl==1.15.0 transformers==5.17.0 peft==0.21.2 vllm==0.33.0`. `train_meta.json` records the installed versions and whether they match the pins.
- Thinking: Qwen3.5-9B has thinking off by default per Unsloth's docs, and the chat template is still rendered with `enable_thinking=False` so training and inference prompts stay identical.
- Export (once, both conditions): `python scripts/sft_data.py --split train --out data/v1.sft.train.jsonl && python scripts/sft_data.py --split dev --out data/v1.sft.dev.jsonl`
- Account SFT: `python train.py --condition account --data data/v1.sft.train.jsonl --eval-data data/v1.sft.dev.jsonl --seed 0 --out outputs/qwen9b-acct-s0`
- Decision-only SFT: `python train.py --condition decision --data data/v1.sft.train.jsonl --eval-data data/v1.sft.dev.jsonl --seed 0 --out outputs/qwen9b-dec-s0`
- In `<out>`: `checkpoint-<step>/` per epoch, `adapter/` (final LoRA adapter and tokenizer), `merged/` (merged 16-bit model for vLLM) and `train_meta.json` (flags, λ, commit and dirty state, pinned and installed library versions, GPU, token counts with the masked-token fraction, realized weight sums on decision and account tokens, training log).
- `tests/test_train.py` checks the masking and weights with the Qwen2.5-0.5B-Instruct tokenizer: on the smoke train rows the decision condition masks 94.5% of answer tokens (36,480 of 38,586) and the account condition none, decision tokens get identical weights summing to 1 per row in both conditions, account tokens sum to λ, λ = 0 reproduces the decision masking, and the trainer's loss equals mean_dec + λ mean_acc on random logits.

## Related work

VERDICT (2609.03366), CREDIT (2610.35295), Chen et al. 2024 (2307.08678), Chua et al. 2024 (2403.05518), Hase & Potts 2026 (2602.20710), Jia et al. 2026 (2605.24286), Mayne et al. 2025 (2509.09396), Doi et al. 2025 (2512.07288).

## FarmShare

- `farmshare/README.md` has the exact order. Login is the Open OnDemand shell (Duo), repo and venv live in `/scratch/users/<sunet>/accountable-ft`, model under `/scratch/users/<sunet>/hf`, data from the GitHub release `data-v1`.
- `farmshare/setup.sh` builds the venv (torch and torchvision both from the cu126 index), `smoke.sbatch` is a 15-minute check, `train.sbatch` is the 6-run array, `eval.sbatch` serves a merged checkpoint with vLLM and runs the answer, repeat and predict steps. Simulation with Gemini runs from a laptop afterwards.
