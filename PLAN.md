# Plan and decisions (Nov 7, 2026)

CS 224V final project, Jon Chen and Eitan Green, mentor Cyrus Zhou. Presentation Dec 4. The reasoning behind each decision and its sources, written so someone outside the project can check it. What we run and how is in `README.md`.

## 1. Question and claim

Proposal question: can fine-tuning make a model's stated reasons and assumptions actually determine its decisions?

Operational question we can answer by Dec 4: does supervising a verified policy account, on top of decision supervision, improve a model's ability to state valid reasons and to predict its own decisions under specified edits, beyond decision-only fine-tuning, on unseen policy structures and a held-out vocabulary, while keeping decision accuracy within a stated margin?

| Property | What it establishes | Test |
|---|---|---|
| Policy-grounded account | the cited facts and defaults justify the decision under the policy | check the account against the rule engine |
| Behavioral faithfulness | the account predicts the model's own answers to specified edits | freeze the account, apply an edit chosen independently of it, rerun the model fresh |
| Causal use of the account | the account is part of the computation that produced the decision | intervene on the intermediate text or representation |

We measure the first two and do not claim the third. Correctness on a case does not show which fact the model used, and agreement over a defined intervention set supports a behavioral claim and nothing more.

- Primary comparison: account SFT vs decision-only SFT, same cases, same augmentation, same decision context (3.3).
- Primary endpoint: dSim (3.6). The simulator is a fixed frozen model that never sees the case text, so it cannot re-solve the case and its only route to the answer is the account. Self-prediction V is secondary: on the Nov 5 baseline a no-account self-predictor already scored 0.77-0.84 because it re-solves the case from the policy and facts, and after SFT both conditions converge toward self-consistency, which leaves V no headroom. Raw self-prediction validity S and its gain G over an oracle-copying predictor sit next to it, since S alone is matched by a predictor that outputs the policy answer.
- dSim compares the own account with a shuffled one (another case's account under the same policy), not with no account. The first smoke run of the protocol showed why: the whole gain over no account came from having account-shaped text, not from this account's content. Sim(own) - Sim(no account) is reported beside it as the gross gain.
- Accuracy is a non-inferiority requirement with a 3-point margin on the primary population (a design choice): the paired CI on the accuracy difference has to exclude a loss larger than 3 points.
- Not claimed: cross-schema transfer, causal mediation, introspection, anything about real clinical or legal use.

## 2. What we learned before the design

- Oct 25: first generator, toy trial eligibility, 4-7 flat rules, z3 labels. Retired once the engine existed (it is in the git history before Nov 7), and the tests' brute-force enumeration is now the independent cross-check.
- Oct 31 probe (Eitan): a 4-rule data-access policy with key-value facts. Gemma 4 26B got 10/11 clean and 80/80 under hints, pressure, irrelevant details and counterintuitive rules. One real failure: asked for the smallest change that would get a request approved, it said none exists, then approved the one-change version in a fresh chat.
- Oct 31 meeting with Cyrus: do not rely on z3, any domain, synthetic data should look realistic and be human-validated, a domain where the model cannot answer from prior knowledge, most current model, Unsloth fine, GCP credits via Monica.
- Nov 4: engine and generator built. First smoke run: 320 items x 3 views, 39/47/14 approve/deny/cannot-determine, 0.15 s per case for exact sufficiency, all flips certified within radius 2.

## 3. Decisions and why

### 3.1 Task: invented-domain policies, three views of each case

- A policy is 8-15 numbered rules over 12 source facts (ints bucketed to at most 8 values, enums, bools) plus 1-2 derived facts (a date gap, a sum) computed from sources and never edited directly, with 2-4 exceptions, 1-2 defaults and near-miss distractor rules (rules that bind in other cases of the same policy but not this one).
- Three aligned views with identical facts and gold: `table` (derived values supplied), `prose` (derived values stated), `prose_derive` (only source facts). They are diagnostic contrasts about reading and calculation bottlenecks, not exact causal decompositions, since supplying a derived value also changes salience. Citations are scored at the source-fact level in every view so minimality is comparable.
- Prose is written by an LLM from the fact table and re-extracted by a second call, and mismatches are dropped. Two LLM calls are not independent verification, so both of us annotate the same stratified 100 items blind to engine labels, including flip and missing variants.
- Invented vocabulary protects against memorized policies, not against priors in general.
- Feature roles rotate across policies. Each policy carries a `template_family`, its logical structure before thresholds, rule numbering and vocabulary. All views and intervention relatives of a case stay in one split.
- Difficulty target: base model at 50-75% accuracy on dev base items in the prose view, tuned on dev only.
- Evidence for the axes: policy-compliance scores of about 33-55% across 6 models under the best prompting, on a metric that also requires naming the violated policy (2603.00369). Models fail to follow edits to their own stated structure (2603.16475). RuleArena finds both rule-selection and arithmetic failures (2412.08972). Abstention on missing facts does not improve with scale (2506.09038).

### 3.2 Oracle: a Python rule engine with exact semantics

- Decision over a partial record after defaults: approve if all admissible completions approve, deny if all deny, cannot determine if both occur. An empty admissible set is an invalid-record error, never a vacuous certificate. Exceptions take precedence over their rule and explicit values over defaults, and cycles are disallowed.
- Four fact states (observed, missing, default-applied, derived) and three intervention kinds (replace, remove so defaults may fire, add to reveal a missing fact). Each variant and each search declares its kind.
- Sufficiency of a cited set S: every admissible completion agreeing with the record on S has the same decision. Checked by enumeration over independent groups of omitted facts. Anything over a 2 s budget returns "uncertified" with a reason and is counted, never truncated silently. The worst case is large (12 facts with 8 values each is 8^12 completions), which is why domains are small and facts are capped at 12.
- Approve and deny get all subset-minimal sufficient sets, and scoring accepts any valid one. Cannot determine gets an approving and a denying witness, and its account is scored on whether the cited missing facts could decide the case, without minimality.
- Sufficiency is not individual necessity ("A or B" with both true: citing A is valid and replacing A alone need not flip). Necessity by intervention is scored on single-condition items only, with coverage, plus an interaction subset.
- Minimal flip: replace-edits by increasing count up to radius 4 toward a fixed target per item (approve for deny bases, deny for approve bases). The result is a certified minimum or "no flip within radius 4", never "none". Cannot-determine items get a minimal reveal (add-edits, radius 2).
- `is_valid_justification` checks a submitted account directly (sufficient, subset-minimal, correct rules and defaults), so no gold set has to be matched.
- Mandatory acceptance tests (in `tests/test_all.py`, except the last, which is evaluate's scoring rule):
  - approve iff A, with A missing, gives cannot determine with both witnesses
  - require A and B, with A false and B missing, gives deny
  - (A or not A) with A missing approves, (A and not A) denies
  - A or B with both true gives two valid singletons and no flip from replacing one
  - A and B with both false gives either singleton as a valid denial and a radius-2 flip
  - a threshold fact moved without crossing gives no flip
  - removing A fires a default while replacing A overrides it
  - changing a source fact updates its derived fact and every rendered sentence
  - constraints with no completion raise, a search over budget is flagged uncertified
  - nearest approval at 5 edits returns no flip within radius 4
  - a prediction and a fresh output that both fail to parse count as a failure

### 3.3 Training target and the matched control

- Options: the policy-gold account (the engine's valid minimal account, exact and free), or the model's own reasons as in CREDIT (2610.35295: ablate each fact, mark "relied on" if the decision changes, rewrite, fine-tune). CREDIT's target is legitimate but drifts after each update, costs several queries per fact per item, and on this task would largely replicate CREDIT.
- Decision: train on gold accounts, with decision-only SFT as the matched control. To make "the only difference is the account loss" true:
  - The decision comes first in the target in both conditions, so it has the same preceding context under teacher forcing. Account-first would condition the decision on the gold account in training and on the model's own account at inference, which changes two things at once.
  - Both conditions use the same sequences and cases, and the control masks the account tokens. The loss is L = L_decision + λ L_account with each term normalized separately, as per-token weights in `train.py`. Without this the account condition would give the decision tokens about 1/18 of the gradient weight, since 95% of supervised tokens are account tokens on v1.
  - Exposure is matched in decision cases seen, not steps. Tokens and GPU time are reported separately.
  - The supervised account includes Policy support, Assumptions and Smallest change, so a gain is attributable to account-plus-recourse supervision, not to factual justifications alone.
  - Self-prediction is elicited at evaluation only. The engine's labels are policy predictions, not labels for the model's future behavior, and whether self-prediction improves under policy supervision is the question.
- Account-first generation is a later variant, not part of the primary comparison. One CREDIT-style relabel round on the account-SFT model is the single extension, only if account SFT is not at the accuracy ceiling (at ceiling the model's reliance already matches gold, so relabeling is a near no-op).
- Why the control matters: "Breaking the Chain" reports Qwen3-8B on AVeriTeC going from 0.63 to 0.92 accuracy after DPO while its intervention-faithfulness score moved from 0.31 to 0.29 (2603.16475). Doi et al. (2512.07288) already show that supervision on attribution-derived explanations improves faithfulness with some transfer, so our contribution is the policy-verified account with defaults and interactions, the matched control and the prediction controls, not the bare finding that training helps.

### 3.4 Output format

- Decision first (3.3). "Relied on" became "Policy support", since gold justifications certify policy support, not reliance.
- The prompt never names the target. An earlier line, "Smallest change to make this approve", told the model that gold was deny on every item. The scoring target derives from the model's own decision, and the same numbers against the gold target carry a vs_gold suffix.
- Self-prediction is a separate evaluation-only call returning an Edit ID and a predicted decision. Parse failures and truncations count as failures in every metric they touch.

### 3.5 Conditions

| Row | What |
|---|---|
| prompted base | thinking off, instructions and few-shot examples selected on dev |
| prompted base, thinking on | same, thinking on |
| decision-only SFT | LoRA SFT, account tokens masked out of the loss |
| account SFT | same data and sequences, account tokens in the loss |
| account SFT + relabel | one CREDIT-style round, only if account SFT is not at the accuracy ceiling |
| larger reference models | Gemma 4 26B-A4B and one API model, prompting only, 1 seed, references not ceilings |

All on Qwen3.5-9B with 3 training seeds and the same held-out items. Retention order under the compute budget: the 6 core SFT runs, primary evaluation with both prediction controls, transfer evaluation of the same checkpoints, then the relabel round. Deferred: the domain-mixture table (6 more runs), on-policy RL, the 27B run. RL, if it ever runs, uses a reward that depends on the account's claims, not decision correctness alone, and is gated by a 1-hour throughput pilot. Offline preference optimization on engine-built pairs is labeled as such, not as RL.

### 3.6 Metrics and evaluation protocol

- Every metric is reported on the primary population (prose view, unseen families, training vocabularies) and on each other slice, with 95% bootstrap CIs clustered by template family, paired on shared items when comparing runs, and each training seed shown next to the aggregate (policy resampling does not estimate training-seed variability). Decoding is fixed, stored with every run, and the evaluator refuses to compare runs with different decoding.
- Every flip and invariance number sits next to a repeat-without-edit control, since two samples of an unchanged prompt disagree with probability 1 - sum_y P(y)^2. At temperature 0 that control only measures API nondeterminism, so a paraphrase edit kind (same facts, new wording) is planned as the noise floor.
- Self-prediction: (1) ordinary decision call, account frozen, (2) a prediction call with the case, the model's own answer and one bank edit chosen independently of the account, (3) a fresh decision call on the edited case with no trace of the prediction, (4) compare. The prediction call is a simulator scored against discrete outputs, not an LLM judge.
- External simulation: the same frozen account and bank edit go to a fixed simulator (gemini-3.5-flash-lite, thinking off, pinned) that sees the policy, the model's decision and account and the edit, never the case text. It classifies the trained model's behavior from the account alone and is scored against discrete labels.
- Bank independence, fixed Nov 5: the first bank took every pivotal edit from the flip variant, which equals the gold account's own smallest change, the exact edit the account-SFT model is trained to write. Pivotal edits now come from an engine flip whose fact set differs from the gold minimum flip (radius up to 3), and bases without one leave the pivotal pool and are counted. A non-crossing edit (a necessary fact moved without crossing its threshold) joins the invariant share.
- Shuffled control, fixed Nov 7: the first version swapped the whole answer, Decision line included, so on the pilots 70 of 176 (Gemini) and 30 of 176 (Qwen) partners carried a different decision and most of the pilot dSim came from that mismatch. The control now keeps the item's own Decision line and swaps only the account lines, partners come only from the model's own frozen answers under the same policy (gold accounts are cleaner than a base model's and would favor the account-SFT condition), and every simulator number is tabled on the items all passes share. Pilot dSim values from before this fix are not cited.
- Trivial baselines, added Nov 7: always predicting "unchanged" beat the simulator with the account on both pilots, so the no-account call is a straw man. Constant-unchanged and oracle-label baselines sit next to every simulator number, dSim is split by whether the fresh decision changed, and a claim about dSim requires the simulator with the account to beat constant-unchanged.
- Checkpoint selection: the same fixed epoch for both conditions, chosen on dev decision accuracy of the control before any account metric is read. Best-of-k on dev dSim for the treatment alone was asymmetric and selected on the noisiest metric, so it survives only as a table labelled exploratory. Non-inferiority across seeds uses one family-clustered bootstrap that averages the 3 seeds inside each resample on the full primary slice, since the 150-case pilots (half-width about 7 points) cannot test the margin.
- No LLM judge in the metric path.

| Measure | Definition |
|---|---|
| Decision accuracy | on all items, per class (approve, deny, cannot determine) |
| Counterfactual pair accuracy | base and flip decisions both match gold, a flip must reach the gold target label |
| Invariance pair accuracy | both decisions correct and unchanged when the oracle says unchanged |
| Explanation validity | cited facts, rules and defaults form a valid justification under the engine, minimality and distractor citation separately |
| S, self-prediction validity | predicted label equals the fresh decision on the edited case |
| G | S minus P(oracle label on the edited case equals the fresh decision), an oracle-copying predictor scores 0 |
| dSim, primary | simulator accuracy with the own account minus with another case's account under the same policy, gross gain over decision-and-edit only beside it |
| V, secondary | self-prediction accuracy with the account minus without it, as in Mayne et al.'s simulatability gain |
| Own-boundary outcomes | the proposed smallest change is valid for oracle and model, oracle only, model only, neither, plus oracle-minimality, a "no change within 4 edits" claim is disproved by a certified flip and "unresolved" when the engine is uncertified |
| Necessity by intervention | editing each cited fact flips the fresh run, single-condition items, with coverage |
| Assumption accuracy | on missing items, decision and stated default match the engine |
| Coverage and failures | exclusions per metric, parse failures, truncations, false "no change" claims, share of bank items whose fresh decision is unchanged |

A perfectly accurate model leaves no room for G, a limit of the diagnostic, not a flaw of the model. Correct-vs-wrong base splits are descriptive only.

Pilot evidence on the v1 primary slice (150 stratified base cases, 690 scored items, 72 families, 356 bank items, simulator rerun at commit 52322ce on the 176 bank items all passes share):

- gemini-3.5-flash-lite, thinking off, temperature 0 (logs v1-lite-eval-145ad3c-20261105-1758, v1-lite-simulate-52322ce-20261107-0252, v1-lite-eval-52322ce-20261107-0253): accuracy 0.77 [0.70, 0.83], approve 0.56, deny 0.93, cannot determine 0 of 97, counterfactual pair 0.44, repeat disagreement 0.16, smallest change valid for the model's own target 0.51 (vs gold 0.37), S 0.78 with and without the account, V 0.00 [-0.04, 0.04]. Simulator 0.68 [0.60, 0.74] own, 0.64 [0.55, 0.72] shuffled, engine-label baseline 0.62. dSim 0.15 [0.00, 0.26] on the 55 changed items and -0.01 [-0.13, 0.13] on the 121 unchanged, gross gain 0.24 [0.14, 0.34]. Cost $1.57.
- Qwen3.5-9B base (OpenRouter, PrimeIntellect, logs qwen9b-lite-eval-c479313-20261107-0147, qwen9b-lite-simulate-52322ce-20261107-0253, qwen9b-lite-eval-52322ce-20261107-0254): accuracy 0.60 [0.53, 0.67], approve 0.29, deny 0.95, cannot determine 0, counterfactual pair 0.21, repeat disagreement 0.01, V 0.08 [0.03, 0.13]. Simulator 0.82 [0.76, 0.89] own, 0.73 [0.66, 0.81] shuffled, engine-label baseline 0.52. dSim 0.19 [0.03, 0.40] on 26 changed and 0.07 [0.02, 0.13] on 150 unchanged, gross gain 0.41 [0.33, 0.50]. Cost $0.68.
- Reading: neither model abstains, accounts are mostly invalid, and accuracy has headroom, so the 3-point margin binds. Qwen is deny-biased and near-deterministic at temperature 0, so the repeat control is cheap. The shuffled pass covers only 176 of 356 bank items because a partner needs a second sampled case under the same policy, so dSim's CI is wide until a full-slice run.

### 3.7 Models and stack (verified Nov 4 and Nov 7)

- Qwen3.5-9B (Apache-2.0, Feb 2026, bf16 LoRA about 22 GB, Unsloth advises against 4-bit for this family, thinking off via `enable_thinking: False`). Qwen's card gives mode-specific sampling, and we fix ours from the pilot. Unsloth's "keep 75% reasoning examples" is guidance for preserving thinking mode, and account lines are not reasoning traces.
- Qwen3.8-27B (dense, Aug 2026): deferred. Qwen3-8B and Qwen3.6-27B dropped as stale, not disqualified.
- Stack, verified on PyPI Nov 7: unsloth 2026.11.3 caps trl at 1.15.0 and transformers at 5.17.0, and vllm 0.33.0 needs torch 2.14.0, so the co-installable set is the one in `train.PINS` (newer trl and transformers do not install with unsloth). Unsloth's Qwen3.5 page: r 16, alpha 16, all 7 projections, bf16 LoRA, adamw_8bit, no 9B-specific recipe. TRL masks the prompt by default, and our per-token weights go through a custom collator. Compatibility is verified by a load, train, save, reload, evaluate smoke test before the runs.
- RL: Unsloth documents `fast_inference=False` for Qwen3.5 and 3.8, and a second GPU does not fix an unsupported integration.

### 3.8 Compute

- Evaluation multiplies: 1,000 base cases, a 10-edit bank, prediction call plus fresh call, is about 20,000 generations per checkpoint before repeats, and thinking tokens can dominate.
- Floor: 6 core SFT runs 12-24 GPU-hours, eval and debugging about 30, relabel round 5-10 (one seed), 47-64 hours before anything deferred.
- Options checked Nov 5 and 7: FarmShare (Stanford's free coursework cluster), Modal ($30 free per month, A100 about $2.50/h), RunPod Community A100 80 GB $1.19/h (H100 from $1.99/h), Vast A100 about $0.84/h with less reliable hosts, Colab Pro (A100 not guaranteed), a GCP quota request (often denied, 2 days to a week). Marlowe and Sherlock need a faculty PI, NSF ACCESS Explore needs an advisor letter, and Kaggle, Lightning free and the GitHub pack have no 40 GB GPU. GCP education credits ($50) have GPU quota 0.
- FarmShare, probed Nov 7: 6 GPU nodes with 4 L40S 48 GB each, 4 GPUs and 4 jobs per user, 2-day wall limit (normal partition 1 GPU per user, long QoS 7 days), CUDA 12.9 module, home 50 GB, scratch 81% full cluster-wide, 1-GPU jobs getting start estimates about 2 hours out. Decision: FarmShare is the primary GPU route, RunPod the fallback if the queue exceeds a day.
- Gemini prose and reference runs go through Vertex (ADC, location global, gemini-3.5-flash-lite), billed to the education credits. The AI Studio key is free tier (20 requests a day) and only serves smoke tests. Spend so far: data v1 about $9, the two pilots $2.25 (3.6).

### 3.9 Held-out design and power

| | training vocabularies | permit vocabulary |
|---|---|---|
| seen families, fresh policies and cases | familiar-structure generalization | vocabulary transfer |
| unseen families | structural transfer (primary population, prose view) | combined transfer |

- Plus a structural holdout of 1-2 exception/default combinations, and 40 hand-written items paraphrased from public eligibility text as a descriptive realism check only (no claim rests on them).
- Clusters, not items, set the power. v1.0 had 21 unseen families with 9-12 bases each. With a design effect near 2.3 the detectable difference at 80% power was about 10 points and the accuracy CI half-width about 3.5 points, which fails a 3-point margin even at a true difference of zero. v1 therefore has 72 unseen families (24 per training domain) with 5 bases each and 60 permit families, at about $6 of prose.
- Measured on the v1 reference run by template family, decision correctness has an intra-cluster correlation near 0, so the accuracy CI half-width on the full primary slice (72 families, 1,513 prose items) at 20% discordance is 2.3 points, inside the margin. dSim's correlation is higher, so its power is recomputed with `evaluate.py --power` on the first clean full-bank run before the claim is sized.
- Honest label for the primary slice: every rule template of the unseen families also appears in training families once numbers are abstracted, so "unseen family" is threshold-and-combination transfer, not transfer to new rule shapes. The permit slice is the real transfer test.
- Data validity fixes, Nov 5: the Gemini prose had a seam (a variant's edited sentence was a plain template sentence among Gemini sentences, which marked the edited fact by style), so edited sentences are restyled against the base file and re-extracted. 201 reveal variants per view repeated their base text and were fixed and deduplicated. stated_facts lists what the view states, fact-key leaks are filtered, and the extraction filter drops 2% (grant) to 13% (review) of base families, shared by both conditions.
- Defensible claim: transfer across held-out policy structures and one held-out vocabulary within one schema.

## 4. Split of work

- Jon: engine, generator, prose pipeline, SFT runs, repo.
- Eitan: eval harness, intervention bank, prompted baselines and reference models, the blind annotation pass, related work.
- Both: error analysis of 50 failures into a taxonomy, report, slides.

## 5. Open questions for Cyrus

- Does he accept the Python engine as the oracle, cross-checked by brute-force enumeration instead of z3?
- Does paraphrased real policy text count as "realistic" for the 40-item check?
- Is a documented negative result (account supervision improves validity but not dSim) acceptable?
- Does he accept an external frozen simulator as the primary scorer, given that it classifies the trained model's behavior and does not judge text quality?

## 6. Sources

- VERDICT 2609.03366. CREDIT 2610.35295, github.com/stanford-oval/CREDIT.
- Chen et al. 2024 2307.08678. Chua et al. 2024 2403.05518. Hase and Potts 2026 CST 2602.20710. Jia, Benton, Easley 2026 2605.24286. Mayne et al. 2509.09396 and 2602.02639. Cheah et al. 2026 2607.21090. Doi et al. 2025 2512.07288. Irpan et al. 2025 2510.27062. Anthropic 2025 2505.05410.
- Guo, Ruis, Andreas, Li 2026, Introspective Coupling 2606.32038 (explanations trained on fixed counterfactual targets track the drifted model, so accounts are scored against the trained model's own behavior and against gold separately). Karvonen et al. 2026 CHIVE 2608.16747 (no-uplift baseline for simulation gain). Yu et al. 2026, One Frozen Simulator Is Not Enough 2608.12253 (dSim on a second simulator family if anything selects on the first). Hong and Roth 2026 2606.01148 (account format changes simulation gain). Zhai et al. 2026 Abstain-R1 2604.17073 and 2507.16199 (abstention as a prompt artifact: a prompt-only control for cannot-determine gains).
- Self-prediction: Binder et al. ICLR 2025 2410.13787. Zeng, Assis, Wang EMNLP 2026 2608.30980 (github.com/safety-research/self-modeling-eval, a candidate external comparison for S). Blandfort et al. 2026 2609.09899.
- Benchmarks: policy compliance 2603.00369, Breaking the Chain 2603.16475, RuleArena 2412.08972, AbstentionBench 2506.09038, NoLiMa 2502.05167, ConditionalQA 2110.06884.
- Model and tooling: huggingface.co/Qwen/Qwen3.5-9B, huggingface.co/Qwen/Qwen3.8-27B, unsloth.ai/docs/models/qwen3.5/fine-tune, docs.cloud.google.com/free/docs/free-cloud-features.
