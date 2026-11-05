# Plan and decisions (revised Nov 4, 2026, after two external reviews)

CS 224V final project, Jon Chen and Eitan Green, mentor Cyrus Zhou. Presentation Dec 4. Working plan plus the reasoning behind each decision, written so someone outside the project can check it. Changes from the previous draft are marked [rev2].

## 1. Question and claim

Proposal question: can fine-tuning make a model's stated reasons and assumptions actually determine its decisions?

Operational question we can answer by Dec 4: does supervising a verified policy account, on top of decision supervision, improve a model's ability to state valid reasons and to predict its own decisions under specified edits, beyond decision-only fine-tuning, on unseen policy structures and a held-out vocabulary, while keeping decision accuracy within a stated margin?

Three properties we keep apart:

| Property | What it establishes | Test |
|---|---|---|
| Policy-grounded account | the cited facts and defaults justify the decision under the policy | check the account against the rule engine |
| Behavioral faithfulness | the account predicts the model's own answers to specified edits | freeze the account, apply an edit chosen independently of it, rerun the model fresh |
| Causal use of the account | the account is part of the computation that produced the decision | intervene on the intermediate text or representation |

We measure the first two and do not claim the third. Correctness on a case does not show which fact the model used. Agreement over a defined intervention set supports a behavioral claim and nothing more.

[rev2] Primary comparison: account-SFT vs decision-only SFT, same cases, same augmentation, same decision context (section 3.3). Primary endpoint: V, the gain in self-prediction accuracy from having the account in the prediction prompt vs not (section 3.6). Raw self-prediction validity S and its gain G over an oracle-copying predictor are reported next to it, because S alone is matched by a predictor that just outputs the policy answer, and then equals edited-case accuracy. Secondary: explanation validity, counterfactual pair accuracy, own-boundary outcomes. Accuracy is a non-inferiority requirement with a 3-point margin on the primary population (a design choice): the paired CI on the accuracy difference has to exclude a loss larger than 3 points.

Not claimed: cross-schema transfer, causal mediation, introspection, anything about real clinical or legal use.

## 2. What we learned so far

- Oct 25: first generator (`gen_z3_v0.py`), toy trial eligibility, 4-7 flat rules, z3 labels.
- Oct 31 probe (Eitan): a 4-rule data-access policy with key-value facts. Gemma 4 26B got 10/11 clean and 80/80 under hints, pressure, irrelevant details and counterintuitive rules. One real failure: asked for the smallest change that would get a request approved, it said none exists, then approved the one-change version in a fresh chat.
- Oct 31 meeting with Cyrus: do not rely on z3, any domain, synthetic data should look realistic and be human-validated, a domain where the model cannot answer from prior knowledge, most current model, Unsloth fine, GCP credits via Monica.
- Nov 4: engine and generator built (section 3.2). First smoke run: 320 items x 3 views, 39/47/14 approve/deny/cannot-determine, 0.15 s per case for exact sufficiency, all flips certified within radius 2.

## 3. Decisions and why

### 3.1 Task: invented-domain policies, three views of each case

- A policy is 8-15 numbered rules over 12 source facts (ints bucketed to at most 8 values, enums, bools) plus 1-2 derived facts (a date gap, a sum) computed from sources and never edited directly. 2-4 exceptions, 1-2 defaults, near-miss distractor rules (rules that bind in other cases of the same policy but not this one).
- Every case exists in three aligned views with identical facts and gold: `table` (structured list, derived values supplied), `prose` (150-300 word case file, derived values stated), `prose_derive` (prose stating only source facts). The views are diagnostic contrasts about reading and calculation bottlenecks, not exact causal decompositions, since supplying a derived value also changes salience. [rev2] Citations are scored at the source-fact level in every view so minimality is comparable; derived-level numbers are reported separately.
- Prose is written by an LLM from the fact table and re-extracted by a second call; mismatches are dropped and the drop rate is reported by difficulty. Two LLM calls are not independent verification, so both of us annotate the same stratified sample of 100 items blind to engine labels, including flip and missing variants.
- Domains: 4, invented vocabulary. Train on a fictional foundation's grant program, a fictional trial protocol, an invented conference submission policy. The fictional permit office is held out. Invented domains protect against memorized policies, not against priors in general.
- Feature roles rotate across policies. Each policy carries a `template_family`: the logical structure (variable reuse, rule dependencies, exception attachment, default behavior, derivation structure) before thresholds, rule numbering and vocabulary. All views and intervention relatives of a case stay in one split. [rev2] If families can be instantiated across domains, the permit domain reuses training families so vocabulary transfer and structural transfer are separate slices (section 3.9); if not, permit is a combined-transfer slice and we say so.
- Difficulty target: base model at 50-75% accuracy on dev base items in the `prose` view, tuned on dev only.

Evidence for the axes: policy-compliance scores of about 33-55% across 6 models under the best prompting, on a metric that also requires naming the violated policy (arXiv 2603.00369); models fail to follow edits to their own stated structure (2603.16475); RuleArena finds both rule-selection and arithmetic failures (2412.08972); abstention on missing facts does not improve with scale (2506.09038).

### 3.2 Oracle: a Python rule engine with exact semantics

[rev2] What each label certifies, with the bounds that make it tractable:

- Decision over a partial record after defaults: approve if all admissible completions approve, deny if all deny, "cannot determine" if both occur. An empty admissible set is an invalid-record error, never a vacuous certificate. Quantification is over joint assignments to all unresolved facts. Precedence of exceptions over their rule and of explicit values over defaults is fixed in the engine; cycles are disallowed.
- Four fact states: observed, missing, default-applied (with its rule), derived (with its sources). Three intervention kinds: replace a value, remove an observation (defaults may fire), add an observation (reveal a missing fact). Each variant and each search declares its kind.
- Sufficiency of a cited set S at record x: every admissible completion agreeing with x on S has the same decision. Checked by enumeration over the omitted facts' domains after splitting facts into independent groups; measured at 0.15 s per case, verified against literal enumeration on random policies. Anything over a 2 s budget returns "uncertified" with a reason and is counted, never truncated silently. Worst case is large (12 facts with 8 values each is 8^12 completions), which is why domains are small, facts are capped at 12, and timeouts are tracked.
- Certificates by decision: approve and deny get subset-minimal sufficient sets (all of them, with minimum-cardinality ones marked; scoring accepts any valid one). Cannot-determine gets two witnesses, an approving and a denying completion, and its account is scored on whether the cited missing facts could decide the case. No minimality scoring for cannot-determine.
- Sufficiency is not individual necessity ("A or B" with both true: citing A is valid and replacing A alone need not flip). Necessity-by-intervention is scored on single-condition items only, with coverage reported, plus an interaction subset.
- Minimal flip: replace-edits by increasing count up to radius 4, over the declared edit space, toward a fixed target label stored per item (approve for gold-deny bases, deny for gold-approve bases). Result is a certified minimum with its radius or "no flip within radius 4", never "none". For cannot-determine items a bounded "minimal reveal" (add-edits, radius 2) finds what would decide the case.
- `engine.is_valid_justification(policy, facts, cited_facts, cited_rules, assumptions)` verifies a submitted account directly (sufficient, subset-minimal, correct rules and defaults), so no gold set has to be matched.
- [rev2] Mandatory acceptance tests, each asserted exactly: approve iff A with A missing gives cannot-determine with both witnesses; require A and B with A false and B missing gives deny; (A or not A) with A missing approves; (A and not A) with A missing denies; A or B with both true gives two valid singletons and no flip from replacing one; A and B with both false gives either singleton as valid denial and a radius-2 flip; a threshold fact moved without crossing gives no flip; removing A fires a default while replacing A overrides it; changing a source fact updates its derived fact and every rendered sentence; constraints with no completion raise; nearest approval at 5 edits returns uncertified-within-4; prediction and fresh output both failing to parse count as failure.
- `gen_z3_v0.py` is kept as an independent cross-check on a sample.

### 3.3 Training target and the matched control

Options considered:

- Policy-gold account: the engine's valid minimal account (facts, the rule each supports, defaults assumed). Exact and free.
- Model's own reasons (CREDIT, 2610.35295): ablate each fact, mark "relied on" if the model's decision changes, rewrite the account, fine-tune. A legitimate behavioral target, with label drift after each update and several extra queries per fact per item; on this task largely a CREDIT replication.

Decision: train on gold accounts, with decision-only SFT as the matched control. [rev2] To make "the only difference is the account loss" true:

- Decision comes first in the target sequence in both conditions, so the decision token has the same preceding context (prompt + case) under teacher forcing. Putting the account first would condition the decision on the gold account during training and on the model's own account at inference, which changes two things at once.
- Both conditions use the same target sequences and the same cases; the control masks the account tokens out of the loss. The masking is verified on a batch before training. Losses for decision and account are normalized separately: L = L_decision + lambda L_account, lambda = 1 unless the pilot says otherwise.
- Exposure is matched in decision cases seen, not steps; tokens and GPU time are reported separately.
- The treatment's supervised account includes "Policy support", "Assumptions" and "Smallest change", so a gain is attributable to account-plus-recourse supervision, not to factual justifications alone. We say so.
- Self-prediction (section 3.6) is elicited at evaluation only, never trained. The engine's labels are policy predictions, not labels for the model's own future behavior; whether self-prediction improves under policy supervision is the question.

Account-first generation is a later system variant, not part of the primary comparison. One CREDIT-style relabel round on the account-SFT model is the single extension, if the core result is interpretable by Nov 17.

Why the control matters: "Breaking the Chain" reports Qwen3-8B on AVeriTeC going from 0.63 to 0.92 accuracy after DPO while its intervention-faithfulness score moved from 0.31 to 0.29 (2603.16475). Doi et al. (2512.07288) already show that supervision on attribution-derived explanations improves faithfulness with some transfer; our contribution is the policy-verified account with defaults and interactions, the matched control, and the prediction controls, not the bare finding that training helps.

### 3.4 Model output format

[rev2] Decision first (section 3.3). "Relied on" renamed to "Policy support", since gold justifications certify policy support, not reliance.

```
Decision: approve | deny | cannot determine
Policy support: <fact>=<value> (R<n>); <fact>=<value> (R<n>); ...
Assumptions: <fact>=<value> (default from R<n>) | none
Smallest change to make this <target>: <fact> -> <value>; <fact> -> <value> | no change within 4 edits
```

Separate prediction call, evaluation only:

```
Edit ID: E17
Predicted decision after edit: approve | deny | cannot determine
```

Multiple simultaneous edits are allowed. Parse failures and truncations are reported and count as failures in every metric they touch.

### 3.5 Conditions

Primary table, Qwen3.5-9B, 3 training seeds each, same held-out items:

| Row | What |
|---|---|
| prompted base | thinking off, instructions and few-shot examples selected on dev |
| prompted base, thinking on | same, thinking on |
| decision-only SFT | LoRA SFT, account tokens masked out of the loss |
| account SFT | same data and sequences, account tokens in the loss |
| account SFT + relabel | one CREDIT-style round, if the core result is interpretable |
| larger reference models | Gemma 4 26B-A4B and one API model, prompting only, 1 seed, references not ceilings |

[rev2] Retention order under the compute budget: the 6 core SFT runs, then primary evaluation with both prediction controls, then transfer evaluation of the same checkpoints, then the relabel round. Deferred until those are done: the domain-mixture table (account SFT on admin-only vs review-only vs both, 6 more runs), on-policy RL, the 27B run. RL, if it ever runs, uses a reward that depends on the account's claims (explanation validity, self-prediction validity), not decision correctness alone, and is gated by a 1-hour throughput pilot. Offline preference optimization on engine-built pairs is labeled as such, not as RL, and some pairs would hold the decision fixed and differ only in account quality.

### 3.6 Metrics

All reported on the primary population (prose view, unseen families, training vocabularies) and separately on each other slice, with 95% bootstrap CIs clustered by template_family, paired on the same items when comparing two runs, each training seed shown next to the aggregate (policy resampling does not estimate training-seed variability). Decoding is fixed and stored with every run and the evaluator refuses to compare runs with different decoding. Main diagnostic decoding is greedy or the lowest-variance setting from the pilot; sampled runs are a secondary row. Every flip and invariance number sits next to a repeat-without-edit control (same prompt, fresh run), since two samples of an unchanged prompt disagree with probability 1 - sum_y P(y)^2.

[rev2] Self-prediction protocol: (1) ordinary decision call, account frozen; (2) a prediction call with the case, the model's own decision and account, and one edit from a fixed intervention bank chosen independently of the account (40% pivotal replace, 30% invariant replace, 15% remove, 15% add, same bank for every model), returning an explicit label; (3) a fresh ordinary decision call on the edited case with no trace of the prediction; (4) compare. The prediction call is a simulator scored against discrete outputs, not an LLM judge.

| Measure | Definition |
|---|---|
| Decision accuracy | on all items, per class (approve, deny, cannot determine) |
| Counterfactual pair accuracy | base and flip decisions both match gold; a flip must reach the gold target label, deny to cannot-determine is a failure |
| Invariance pair accuracy | both decisions correct and unchanged when the oracle says unchanged |
| Explanation validity | cited facts, rules and defaults form a valid justification under the engine; minimality and distractor citation separately; cannot-determine items scored on whether the cited missing facts could decide the case |
| S, self-prediction validity | predicted label equals the fresh decision on the edited case |
| G | S minus P(oracle label on the edited case equals the fresh decision); an oracle-copying predictor scores 0 |
| V, primary endpoint | accuracy of the prediction call with the account minus the same call without the account (case, own decision, edit only), as in Mayne et al.'s simulatability gain |
| Own-boundary outcomes | the proposed smallest change toward the fixed target is valid for oracle and model, oracle only, model only, neither; oracle-minimality under the declared edit space; a "no change within 4 edits" claim is disproved by a certified engine flip and "unresolved" when the engine is uncertified |
| Necessity by intervention | editing each cited fact flips the fresh run, single-condition items, with coverage |
| Assumption accuracy | on missing items, decision and stated default match the engine |
| Coverage and failures | exclusions per metric, parse failures, truncations, false "no change" claims, fraction of bank items whose fresh decision is unchanged |

A perfectly accurate model leaves no room for G, which is a limitation of the diagnostic, not a flaw in the model. Optional: a single frozen predictor model on a small audit subset, to separate changes in the accounts' usefulness from changes in the trained model's prediction skill. Correct-vs-wrong base splits are descriptive only. The own-boundary metric comes from our probe; whether it is promoted is decided on pilot data.

[rev2] Checkpoint selection: among checkpoints whose dev accuracy is within 3 points of the decision-only control's, pick the best dev V. Then test once.

No LLM judge in the metric path.

### 3.7 Models and stack (verified Nov 4)

- Qwen3.5-9B (Apache-2.0, Feb 2026, bf16 LoRA about 22GB, Unsloth advises against 4-bit for this family, thinking off via `enable_thinking: False`). Qwen's card gives mode-specific sampling; we fix and document ours from the pilot. Unsloth's "keep 75% reasoning examples" is guidance for preserving thinking mode; whether to preserve it is decided in the pilot, and account lines are not reasoning traces.
- Qwen3.8-27B (dense, Aug 2026): deferred. Qwen3-8B and Qwen3.6-27B dropped as stale, not disqualified.
- Stack: unsloth 2026.11.x, trl 1.17, peft 0.21, vllm 0.33, transformers 5.22. Existence verified; compatibility verified by a load, train, save, reload, evaluate smoke test, then pinned.
- RL: Unsloth documents `fast_inference=False` for Qwen3.5 and 3.8; a second GPU does not fix an unsupported integration.

### 3.8 Compute

- Budget from measured throughput. Evaluation multiplies: 1,000 base cases, a 10-edit bank, prediction call plus fresh call, is about 20,000 generations per checkpoint before repeats, and thinking tokens can dominate.
- Floor: 6 core SFT runs 12-24 GPU-hours, eval and debugging about 30, relabel round 5-10 (one seed). 47-64 hours before anything deferred. RunPod or Vast roughly $120-250.
- Have: $50 GCP education credits, GPU quota 0 on the project (Compute Engine API enabled Nov 4). Free-trial accounts cannot attach GPUs; unused trial credit survives an upgrade within its expiry; AI Studio Gemini API costs are excluded from trial credit. Asking Cyrus for credits, RunPod or Vast out of pocket meanwhile.

### 3.9 Held-out design and what "domain-agnostic" means here

[rev2] Evaluation matrix, slices not training runs:

| | training vocabularies | permit vocabulary |
|---|---|---|
| seen families, fresh policies and cases | familiar-structure generalization | vocabulary transfer |
| unseen families | structural transfer (primary population, prose view) | combined transfer |

Plus a structural holdout of 1-2 exception/default combinations, and 40 hand-written items paraphrased from public eligibility text as a descriptive realism check only (a margin near 15 points, no claim rests on them). The vocabulary-transfer cell exists only if families instantiate across domains (section 3.1).

Sample size: for paired items with 20% discordance and a true difference near zero, about 850 items give a 95% half-width of 3 points before clustering, so the primary population needs at least 20 held-out families with about 45 prose items each, which means at least 100 families generated. The planned clustered paired analysis is simulated on pilot data before the split is frozen.

Defensible claim: transfer across held-out policy structures and one held-out vocabulary within one schema.

## 4. Split of work

- Jon: engine, generator, prose pipeline, SFT runs, repo.
- Eitan: eval harness, intervention bank, prompted baselines and reference models, the blind annotation pass, related work.
- Both: error analysis of 50 failures into a taxonomy, report, slides.

## 5. Timeline

- Nov 5-9: freeze oracle semantics and acceptance tests, intervention kinds, family splits, prediction protocol. Pilot difficulty on dev. Measure training and eval throughput for 1 hour. Simulate the primary analysis on pilot data.
- Nov 10-16: prompted baselines, decision-only and account SFT (3 seeds each), blind annotation. RL go/no-go.
- Nov 17-23: primary and transfer evaluation, paired CIs, error analysis. Relabel round only if the core result is interpretable.
- Nov 24-30: uncertainty, limitations, report, slides.
- Dec 1-4: rehearse, freeze repo.

## 6. Risks and mitigations

- Saturation or floor: pilot on dev, tune per view.
- Gains from accuracy, data, format or leakage rather than account supervision: matched control with shared decision context and verified masks, family-grouped splits, paired metrics, prediction controls G and V, prespecified selection rule.
- Sampling noise read as flips: greedy main diagnostic, repeat-without-edit control.
- Oracle errors or intractability: acceptance tests, timeouts counted as uncertified, z3 cross-check, blind annotation including edited items.
- Compute shortfall: retention order in 3.5.
- Overreach: claims as in section 1 and 3.9.

## 7. Open questions

- Does Cyrus accept the Python engine as the oracle with z3 as a cross-check?
- Does paraphrased real policy text count as "realistic" for the 40-item check?
- GPU credits: how many, on which provider?
- Is a documented negative result (account supervision improves validity but not V) acceptable?

## 8. Sources

- VERDICT 2609.03366. CREDIT 2610.35295, github.com/stanford-oval/CREDIT.
- Chen et al. 2024 2307.08678. Chua et al. 2024 2403.05518. Hase and Potts 2026 CST 2602.20710. Jia, Benton, Easley 2026 2605.24286. Mayne et al. 2509.09396 and 2602.02639. Cheah et al. 2026 2607.21090. Doi et al. 2025 2512.07288. Irpan et al. 2025 2510.27062. Anthropic 2025 2505.05410.
- Self-prediction: Binder et al. ICLR 2025 2410.13787. Zeng, Assis, Wang EMNLP 2026 2608.30980 (github.com/safety-research/self-modeling-eval, a candidate external comparison for S). Blandfort et al. 2026 2609.09899.
- Benchmarks: policy compliance 2603.00369, Breaking the Chain 2603.16475, RuleArena 2412.08972, AbstentionBench 2506.09038, NoLiMa 2502.05167, ConditionalQA 2110.06884.
- Model and tooling: huggingface.co/Qwen/Qwen3.5-9B, huggingface.co/Qwen/Qwen3.8-27B, unsloth.ai/docs/models/qwen3.5/fine-tune, docs.cloud.google.com/free/docs/free-cloud-features.
