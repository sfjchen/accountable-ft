# Decisions and results

The design, every result the report cites with its log, and the limits. Short guide in [README.md](README.md), commands and clusters in [OPS.md](OPS.md). Every number comes from a `stamp-run` log at abaa830 (`~/dev/logs/final-*-eval-abaa830-20261120-*`, JSON in `~/dev/logs/evals-final/`) unless a line names another log. These simulator prompts showed an Edit ID that named the edit kind, so every simulator number here is being replaced by a rerun (see Simulator prompt fix).

## Claim

- Question: can fine-tuning make a model's stated reasons predict what it does when the facts change?
- Claim: on invented rule domains, training on engine-verified explanations makes explanations case-specific and predictive of the model's own post-edit answer, beyond a matched decision-only control, with accuracy non-inferior on the training-domain test (v1).
- Not claimed.
  - That explanations are how the model computes (causal faithfulness needs interpretability tools).
  - That own explanations reveal the model's errors. They don't (Controls).
  - Transfer to real rules. The registered real-rules test failed (Row-matched grid).
  - Anything about real clinical, legal or lending use.

## Design

- Invented policy domains with exact labels. A Python rule engine gives the correct decision, every minimal sufficient set of facts, the minimal flip and "cannot determine" witnesses. Brute-force enumeration in the tests cross-checks it. Invented, so nothing leaks from pretraining. Real domains (mortgage, SNAP, IRS dependent) use the same schema with real thresholds, so priors can pull against the text.
- Matched control. Explanation SFT and decision-only SFT see the same cases, prompts and target sequences. Decision-only zeroes the explanation tokens in the loss. Loss = mean decision-token loss + λ x mean explanation-token loss, so decision tokens carry equal weight in both (otherwise 95% of supervised tokens on v1 are explanation tokens). Decision comes first in the target.
- Split by rule family, so test policies are new combinations and thresholds. Every rule shape also appears in training, so "unseen family" is threshold-and-combination transfer. Permit (a whole invented domain never trained on) is the real vocabulary transfer test.
- Endpoint, no LLM judge: simulatability gain. A frozen simulator (Gemini 3.5 Flash-Lite, Claude Opus 5.5 as the 2nd family) sees the policy, the model's decision, its explanation and an edit, never the case, and predicts the model's fresh post-edit decision. Gain = accuracy with the model's own explanation minus with another case's explanation under the same policy, own Decision line kept.
- Edit set (`infer.py --mode bank`): engine-built edits, 40% flip, 30% should not, 15% remove a fact, 15% reveal one. Flip edits differ from the correct smallest change, so a model cannot have memorized them.
- Statistics: 3 training seeds, 95% bootstrap CIs clustered by rule family, paired on shared items, Holm across the 3 mix contrasts per test, greedy decoding, fixed epoch 2 chosen before any explanation metric was read. Every simulator number sits next to an always-"unchanged" baseline.
- Explanation format (4 lines): Decision, Policy support (cited facts and rules), Assumptions (defaults used), Smallest change that would reverse it. "Valid" = the engine certifies the cited set as sufficient and minimal.

| Metric | Definition |
|---|---|
| accuracy | decision matches the engine, 3 classes (approve, deny, cannot determine) |
| explanation validity (correctness) | cited facts, rules and defaults form a valid justification |
| `acct_consistent` | the engine's decision with the model's cited values substituted equals its stated decision |
| simulatability gain | simulator accuracy, own explanation minus shuffled |
| own minus wrong | own explanation minus a wrong-reason explanation (same decision, format, length, true but non-binding facts) |

## Domains and data

| domain | kind | facts / rules / defaults | role |
|---|---|---|---|
| grant, trial, review | invented | 12-16 / 12-14 / 4-6 | train (round 1), review held out from the grid |
| permit | invented | 12 / 10 / 3 | held out from every run |
| mortgage | real, Fannie Mae and FHFA 2026 | 17 / 13 / 7 | held out (round 1), trained (round 2, grid) |
| SNAP | real, FY2027 rules | 20 / 12 / 8 | trained (grid) |
| IRS dependent | real, tax year 2026 | 22 / 13 / 8 | held out from every run |

- Sources and simplifications for each real domain sit in `domains/<name>.md`.
- v1: about 5,000 cases, 3 views (table, prose, prose with derived facts), 72 unseen families (1,513 prose items) and 60 permit families. Prose by Gemini, with an extraction check that drops prose distorting a fact.
- Data audit: engine labels sound on all 205 checked "cannot determine" pairs. About 10% of "cannot determine" prose was lossy, so 222 flagged items are dropped at export (`data/v1.flagged.txt`).
- Before training (150-case pilots, logs `*-lite-eval-b0b29ad-20261109-2209`, before (b0b29ad)): Gemini 0.77 and Qwen3.5-9B 0.60 accuracy, 0 of 97 "cannot determine" right for both, validity 0.22 and 0.07. 298 of 305 wrong Qwen answers contradict their own explanation: facts read right, rules applied wrong.

## Results

### Round 1: grant, trial, review

Qwen3.5-9B LoRA, 3 seeds, epoch 2, means over seeds. Paired = explanation minus decision-only, seed by seed (logs `final-v1-gemini-eval-abaa830-20261120-1542`, `final-mortgage-gemini-eval-abaa830-20261120-1542`, `final-v1-opus-eval-abaa830-20261120-1542`, `final-mortgage-opus-eval-abaa830-20261120-1542`).

| v1 unseen families | explanation SFT | decision-only | prompted base | paired |
|---|---|---|---|---|
| accuracy | 0.976 | 0.972 | 0.627 | 0.004 [-0.008, 0.016] |
| explanation validity | 0.756 | 0.000 | 0.067 | 0.756 [0.729, 0.781] |
| decision follows own explanation | 0.968 | | 0.550 | |
| simulatability gain, Gemini | 0.106 | 0.025 | 0.048 | 0.081 [0.043, 0.123] |
| simulatability gain, Opus | 0.207 | 0.046 | | 0.161 [0.129, 0.195] |
| always-"unchanged" baseline | 0.412 | 0.425 | 0.856 | |

- Both SFT conditions fix the base model's failure modes (accuracy 0.63 to 0.97, "cannot determine" 0 to 0.95), so accuracy comes from the shared data and the explanation loss adds predictiveness on top. Gain is 0.10-0.11 in each of the 3 domains.
- Mortgage (never trained on): validity 0.374, accuracy +0.014 [-0.020, 0.049], gain +0.038 [-0.018, 0.094] with Gemini, +0.091 [0.048, 0.137] with Opus.
- Permit (never trained on, log `final-permit-gemini-eval-abaa830-20261120-1542`): gain +10.0 [6.5, 13.6] (Opus +13.3 [9.7, 16.8]), validity 43% vs 0, accuracy 93.0% vs 94.6% (-1.6 [-3.5, 0.5]), base 70.4%.
- Power (log `r1-v1-power-1332e96-20261110-1459`, before (1332e96)): minimum detectable gain difference 5-8 points per seed pair.

### Controls

- Placeholder confound. Decision-only still prints explanation lines as unlearned placeholders, so the paired gap partly compares well-formed with malformed lines. The 2 controls below remove that.
- Wrong-reason control (`infer.py --wrong-accounts`): keeps decision, format, item count and length, swaps the cited facts for true stated facts that leave the case open. Own minus wrong +9.1 on v1 (seeds 7.9, 9.0, 10.3, each CI clear of 0), +13.1 on answer-changing edits. Mortgage -0.2, wrong minus shuffled +5.2. So the invented-test gain needs the right reason, while on mortgage format and true facts carry it.
- Prompted-explanation control (`--mode explain`): the base model writes explanation lines for the SFT model's fixed decision. Trained minus prompted on the same decisions: v1 +5.3 [1.8, 9.2] (Opus +11.1 [8.2, 14.1]), mortgage -3.0 [-8.0, 2.3] (Opus +0.9 [-2.6, 4.6]). The edge sits on answer-changing edits (v1 +11.8 [6.7, 17.8]). Prompted lines are 1.6x longer and cite distractors 75% of the time (13% trained).
- What a strong simulator adds. Opus predicts trained models at 0.890 with no explanation (they are 97% right), so a true explanation adds only +0.017 over none and the gain comes from a shuffled one pulling Opus off (0.701). So the gain means "this explanation is specific to this case", not "it tells you more than the policy and edit do". Gemini, which cannot predict alone (0.460), shows both.
- Own explanations don't reveal errors. On post-edit items the model gets wrong, Opus tracks the model's actual answer at 0.367 with its own explanation, 0.342 with none and 0.494 with a shuffled one (79 items, `compare_sims.py`, log `final-v1-simcompare-18e1ab8-20261120-1853`).

### Round 2 and mortgage-only

- Round 2 trains grant, trial and mortgage (review held out). Mortgage-only is seed 0 only. Paired gain, v1 / mortgage: round 2 Gemini +0.041 / +0.094, Opus +0.120 / +0.170. Mortgage-only Gemini -0.005 / +0.066, Opus +0.009 / +0.024. Accuracy, v1: round 2 +0.033 [0.020, 0.049].
- Mixing invented and real gives the largest mortgage gain with Opus. Round 2 vs mortgage-only confounds mix with size (3x rows) and seeds, which the grid removes.

### Row-matched grid (pre-registered Nov 12)

- 3 mixes at 3,600 train rows, equal share per domain: `rm-inv` grant + trial, `rm-real` mortgage + SNAP, `rm-mix` all 4. 2 conditions x 3 seeds = 18 runs. Tests: unseen families of the 4 training domains, plus review and IRS dependent, both held out from every mix.
- Registered main score, paired Gemini gain on IRS dependent: failed. inv -6.6 [-11.4, -1.9], real -4.6 [-8.6, -0.8], mix -3.6 [-7.7, 0.4]. The predicted order (mix >= real > inv) holds for point estimates only, no contrast clears Holm. Opus agrees (-2.9 / -0.1 / +1.5, no CI clear of 0). The review prediction also failed (mix highest at +3.7, every CI crosses 0).
- Gain by test, Gemini (inv / real / mix): grant 2.3 / 0.6 / 4.9, trial 6.3 / 0.5 / 4.8, review -0.4 / 0.0 / 3.7, mortgage 1.3 / 8.8 / 8.1, SNAP 2.9 / 8.3 / 9.7. No gain contrast clears Holm.
- Explanation correctness, all 18 contrasts clear Holm: each specialist is best on its own kind (the other trails by 11-38 points), mix is best on review and within 2-10 points elsewhere. Mix accuracy matches or beats decision-only on every test (up to +6.5 on IRS dependent).
- Wrong-reason control on the grid: own minus wrong on v1 +6.1 / +6.3 / +7.5 (every seed clear of 0), mortgage -0.2 / +0.6 / +1.6, SNAP +9.7 / +5.4 / +6.3, IRS dependent +0.9 / -3.6 / +0.7.

#### Post hoc: new test families (registered Nov 14, a robustness check, not a retest)

- Families of review and IRS dependent that no grid model trained on, and new families of the 4 training domains (`data/*-x.jsonl`). Pooled only where old minus new covers 0, so IRS dependent real and mix are not pooled (-5.5 [-10.9, -0.1], -5.7 [-11.3, -0.8]).
- Holm-clear pooled contrasts: mix - inv +6.6 [3.1, 10.1] on mortgage and +8.4 [4.9, 12.0] on SNAP, real - inv +6.7 and +8.1. None on review.
- Own minus wrong, pooled: mortgage +1.1 / +5.0 / +6.7, SNAP +8.8 / +7.2 / +6.9, review +6.8 / +8.0 / +7.7.
- Opus on the new mortgage and SNAP families, registered Nov 20 before any result (`sim.sh` with `SIMS=own+shuf`, own and shuffled passes on all 18 runs). Read: mix - real on mortgage, new alone and pooled. The Opus mortgage gap (-6.5 on the original 24 families) replicates if the pooled CI stays below 0, and is a small-sample result if it covers 0. SNAP and the other 2 contrasts are secondary.
  - Result: replicates. Mortgage mix - real -5.8 [-7.9, -3.8] new alone, -6.0 [-7.9, -4.1] pooled (Holm 0.003 both), accuracy equal (+0.2 [-1.4, 2.1]) (logs `final-mortgage-split-x-grid-opus-eval-4776607-20261121-0450`, `final-mortgage-split-x-pool-grid-opus-eval-4776607-20261121-0500`). SNAP mix - real -2.1 [-4.3, 0.0] new alone, -1.4 [-3.3, 0.3] pooled (logs `final-snap-x-grid-opus-eval-4776607-20261121-0414`, `final-snap-x-pool-grid-opus-eval-4776607-20261121-0423`). Mixed beats invented-only on both (+5.0, +4.2 pooled).

#### Simulator prompt fix (registered Nov 21, before any rerun result)

- Flaw: the simulator saw the bank id as Edit ID, which ends in the edit kind (`pivotal_replace`, `noncrossing_replace`). On v1 a rule from that suffix and the original decision predicts 95.5% of explanation-SFT answers, about what Opus gets with no explanation. Shuffle partners also had another decision in 483 of 748 v1 seed-0 items, so their Policy support contradicted the Decision line kept.
- Fix (539e723): an opaque Edit ID and a same-decision partner whenever the policy has one. Every simulator pass the cited evals read reruns (`resim.py`), and Opus gets wrong-reason passes on the 9 grid explanation runs.
- Readouts, fixed now: registered endpoints keep their definitions. Mixed vs real-only reads first own minus wrong-reason on the explanation runs (`--contrast-raw account`, `sim_dwrong`), which stays within a run and avoids the decision-only placeholder lines, then the raw own-minus-shuffled contrast, then the registered paired gain. The simulators disagree only if the primary contrasts clear 0 in opposite directions on mortgage or SNAP (pooled).
- Before the fix (post hoc, logs `final-*-grid-{gemini,opus}-raw-eval-b8301d2-*`): the paired gain subtracts decision-only runs that print placeholder support lines, which name a fact more often in mixed and invented-only runs than in real-only ones and which Opus reads. The Opus mortgage gap of -6.5 splits into -2.8 from the explanation runs and -3.7 from that subtraction. Raw mix - real, Gemini / Opus: mortgage -0.2 [-4.1, 3.2] / -2.8 [-5.8, -0.0], SNAP +1.6 / -0.2, v1 (grant, trial, review) +2.9 [-0.4, 6.3] / +4.0 [1.1, 7.0], IRS dependent +2.4 / +2.8.

#### Post hoc: claim probes (registered Nov 21 by Eitan, before any result)

Mentor feedback (Nov 20) asked whether the kind of training rules decides how far faithful rule-following carries to real rules. These 3 probes test the parts of that claim the grid leaves open: whether models read the stated rule or a remembered one, whether mix beats the specialists only because it sees 4 domains, and a solver-style faithfulness score. All are post hoc, with their own Holm families, and none changes the registered grid reads.

- E4, engine-scored faithfulness (`faith.py`, no new passes). For each edit-bank item, it reads the model's sample-0 explanation of the base case, its answer on the edited case and the Gemini prediction.
  - `engine_faithful`: the decision `engine.implied_decision` reaches from the explanation's cited facts and assumptions, with the edit applied (cited values of edited facts dropped, a cited derived fact dropped when a source is edited), equals the answer. Split by `cited` (the edit touches a cited fact, derived facts counted as their sources) and `uncited`, and by edit kind. Unscored when a cited label maps to no fact or the account cannot be applied.
  - `changed[cited|uncited][kind]`: the answer differs from the base answer, with no engine.
  - `engine_sim_agree`, `engine_acc`, `sim_acc`: agreement of the engine's implied decision with the simulator's prediction, and each one's accuracy against the answer on the same items.
  - `abstain[cd|default|partial|irrelevant]`: on remove edits, the answer is "cannot determine", by the gold effect of the removal (cannot determine, default applied, unchanged but in a sufficient set, unchanged and in none).
  - Every metric also split `|correct` and `|wrong` by the base decision. CIs resample template families. Seeds pooled.
  - Read: `engine_faithful[cited]` and `[uncited]` per mix on each test file, explanation-trained grid runs. Descriptive, no contrast family. Decision-only runs print placeholder explanations, so only `changed` and `abstain` apply to them.
  - Code smoke-tested on `base-thinkoff` (untrained, v1) before this entry. No grid run was scored.
  - Result (Nov 22, b8fd2fe, `outputs/faith/<file>.json`, seeds pooled, explanation runs, simulator passes from before the prompt fix). `engine_faithful[cited]` inv / real / mix: v1 .88 / .76 / .87, mortgage .74 / .95 / .91, SNAP .58 / .86 / .84, review (new families) .66 / .64 / .68, IRS dependent .28 / .43 / .50. Faithfulness follows the kind trained on, like correctness: each specialist is high on its own kind and low on the other, and mix matches the better specialist on all 3 training files. On the held-out tests there is no clear order: review is flat, and on IRS dependent mix is highest but its CI overlaps real-only ([.42, .57] vs [.33, .51]).
  - IRS dependent is the failure case for every mix. When an edit changes a cited fact the answer moves only 17 / 37 / 48% of the time, and when the removed fact decides the case the model says cannot determine 1 / 7 / 21% of the time (v1 75 / 70 / 84%). So the models do not act on their own stated reasons there.
  - Caveat: the engine fills uncited facts with their true values, so `engine_faithful` also rewards answering correctly, and `[uncited]` tracks `[cited]`. `changed[cited]` against `changed[uncited]` is the score that needs no engine.
- E1, prior-conflict probe (`probe.py`, `data/{mortgage-split,snap,dependent}-pc.jsonl`). Real-domain test cases decided by one threshold moved off its value, alternating up and down by case so that following the original threshold is not one decision bias:
  - mortgage `min_score` up 60 (640 to 700, 660 to 720) or down 20 (to 620, the real Fannie Mae minimum, and 640), its exception (t - 20 with reserves) with it
  - SNAP `resource_limit` for households without an elderly or disabled member, $3,000 to $4,500 or $1,500
  - IRS dependent `qc_age`, under 19 to under 23 or under 17 (student exception, under 24, unchanged)
  - Design change (Nov 22, before any answer on a probe file): moving the threshold on the unchanged test cases gave too few conflicts, since other rules decide most cases. Base conflicts, mortgage / SNAP / IRS: 33 / 0 / 2 at the first moves, at most 42 / 4 / 4 for any single threshold tried, and 44 / 5 / 8 even with a threshold chosen per case. So each test-slice prose base case is edited: its threshold fact set between the original and moved threshold, the rule's other facts searched, and other rules that would decide the case repaired with the fewest fact changes. Only the sentences of changed facts are re-rendered (template prose), the rest of the case wording kept.
  - Each edited case gives 2 base records: `-pc` with the moved rule (`prior_conflict`, `orig_decision` the decision under the original rule) and `-pcc` with the original rule, a control on the same facts. Gold from `gen.gold_for`. Conflict cases, mortgage / SNAP / IRS: 115 / 86 / 138 (up 58 / 45 / 69, down 57 / 41 / 69), each with its control, so 230 / 172 / 276 records. SNAP leaves out the 82 cases whose policies have no $3,000 rule. Facts changed per case: none in 3 / 1 / 1, one in 14 / 12 / 21, two in 42 / 28 / 46, three or more in 56 / 45 / 70.
  - Edit banks (`probe.py --bank`): only the kinds a base record alone gives, pivotal_replace and noncrossing_replace at 4:3, since the probe has no missing or invariant variants: 402 / 301 / 425 items (IRS drops 33 cases with no certified flip within radius 3). So the paired gain on the probe files has no remove or add edits and is not comparable in level to the original files.
  - All 18 grid models answer the 3 files (no training), Gemini own, shuffled and no-explanation passes.
  - Primary read: `prior_follow` (answer equals `orig_decision`) on the `-pc` records, per mix, pooled over the 3 files, the 3 pairwise mix contrasts Holm-adjusted. Read with control accuracy on the `-pcc` records: a mix that follows the original threshold but also misses the controls is not reading either rule. Secondary: accuracy, validity and paired gain split by `prior_conflict` (evaluate.py), per file and by move direction.
  - Prediction (from the claim that real rules let a remembered threshold stand in for reading): real-only follows the original threshold most, invented-only least, mixed in between. If real-only is not above invented-only, the claim fails.
- E2, mixed-2 arm. 2 new mixes at the specialists' dose: `rm-gm` (grant + mortgage) and `rm-ts` (trial + SNAP), 3,600 train rows at 1,800 per domain, same export, epoch 2, 3 seeds x (explanation, decision-only), 12 runs (`cluster.sh grid` array 18-29). They answer the same 9 test files and the 3 probe files. Gemini all passes plus wrong-reason, Opus own and shuffled on the 4 originals.
  - Primary read: explanation correctness and the simulator readouts in the order the prompt-fix entry above sets (own minus wrong-reason on the explanation runs, then raw own minus shuffled, then the paired gain), on each test and on the 6-test mean. Contrasts gm and ts each vs real-only and invented-only, and mix vs each of gm and ts. evaluate.py Holm-adjusts all 10 pairs of the 5 mixes per test (`score.sh` `grid2`), more conservative than the 6 named.
  - Decision rule: gm and ts both above real-only and invented-only on held-out tests means mixing kinds matters at equal domain count. Tied with real-only means real rules alone are enough. Mix above gm and ts means its edge was domain variety, not mixing. Grid power (5-8 points) cannot read a null, so a tie is reported as no detected difference.

#### Mix recommendation

- Train on the mixed set, on correctness and accuracy, not on gain. Mean over all 6 tests, inv / real / mix: correctness 39% / 36% / 44%, accuracy 78% / 80% / 87%. Mixed beats real-only on invented tests (correctness +12 to +27) and trails it by 2-6 points on real tests.
- Not more data (log `final-grid-seeds-2005f39-20261120-1856`): every mix has 3,600 rows, 266-270 root cases, the same variant shares and the same steps. Real-only has the most text, 1.49M explanation characters vs 1.28M mixed (5.55M vs 4.76M training tokens in sc's `train_meta.json`). Mixed has 2x the families (120 vs 60) and 1.7x the policies (202 vs 119) at half the rows per domain, so the open confound is diversity vs per-domain dose, not volume.
- Gain does not separate mixed from real-only. The 2 simulators seemed to disagree, mostly through the decision-only subtraction (Simulator prompt fix). Average over the 6 tests by seed (same log): Gemini mix 4.5 / 4.7 / 4.6, real 2.5 / 2.4 / 1.9, mix higher in 9 of 9 seed pairs. Opus mix 6.1 / 4.4 / 2.3, real 5.9 / 3.5 / 6.4, 3 of 9. On real tests Opus favors real-only (mix higher in 1 of 9 pairs, mortgage -6.5 [-10.5, -2.8] after Holm, and -6.0 [-7.9, -4.1] with the 60 new families pooled in). On the 2 held-out tests mixed is higher in 7 of 9 pairs under both.
- The earlier "+6.9 / +4.5 / +3.2 on trained-on tests" (mix / real / inv) averaged Gemini over 4 tests, 2 of which each specialist never trained on. Opus gives 4.6 / 7.1 / 6.4.
- Limits: CIs pool the 3 seeds and resample families only. Holm covers the 3 contrasts within 1 test, metric and simulator, not 6 tests x 2 simulators. 1 held-out domain per kind.

### Error analysis and diagnostics

- IRS dependent failures (`errors.py`, 25 wrong decisions and 25 simulator misses from the 9 explanation-trained grid runs, labels in `data/errors-dependent.jsonl`, log `final-dependent-errors-eval-abaa830-20261120-1600`).
  - Wrong decisions cite a rule that an exception waives (690 of 2,309) or that covers the other claim type (757).
  - Simulator misses: the edit fixes the cited reason and the answer stays deny (312 of 514 answer-stays misses).
  - The model says "cannot determine" on 76 of 684 cases that need it. Training taught the format, not the scope and exceptions of the IRS rules.
- Arithmetic: case text states every computed value, so no model computes. Among denials, real and mixed models gain most where the failing rule reads a derived value (mortgage +14.5 and +14.9, SNAP mixed +22.9), invented-trained models don't, so it follows training domain. A diagnostic, not a design axis.

## Limits

- 1 schema, 1 model size (9B), 2 domains per kind. "Unseen family" reuses training rule shapes.
- Real-rules transfer is not shown. Mortgage gains on the original families are format-driven, and the registered IRS test is negative.
- Real-only dose arm not run (rm-real at 1,800 rows, matching mixed's real rows). A clean arm filters mixed's own mortgage and SNAP rows (only 1,455 of its 1,800 are in rm-real, and a fresh 900-per-domain export draws other cases), keeps 2 epochs (so half the steps) and reads mixed minus it on mortgage with Opus, the only place the mixes differ. Neither outcome changes the pick, which rests on correctness, and grid power (5-8 points) could not read a null. The cheaper check ran instead: Opus on the 18 runs' new mortgage and SNAP families confirms the mortgage gap (above).
- Opus is not temperature-controlled (Claude Code headless), so a rerun can differ slightly.

## Decision log

- Oct 31: invented domains over real policy text. Real text has no exact labels and leaks from pretraining.
- Nov 5: endpoint moved from self-prediction to the external simulator, since a self-predictor re-solves the case (0.77-0.84 with no explanation). Pivotal edits made independent of the correct smallest change.
- Nov 7: shuffled control keeps the item's own Decision line (the old version made most of the pilot gain), always-"unchanged" baselines added, fixed epoch for every condition, matched loss weighting, "cannot determine" kept as a 3rd class.
- Nov 9: mortgage merged (Eitan), `acct_consistent` added after his pilot showed answers contradicting their own numbers. Round 2 replaces a 2x2 cross-evaluation (1 new mix, reuses round 1).
- Nov 12: row-matched grid pre-registered. Nov 14: new test families registered as post hoc.
- Nov 13-19: prompted-explanation, wrong-reason and permit controls.
- Nov 20: metrics review. Boundary and necessity metrics removed (their GPU pass never ran), repeat and self-prediction passes opt-in. Every report eval rescored at abaa830.
- Not triggered: the CREDIT-style relabel round, planned only below the accuracy ceiling (round 1 is at 0.976).

## Split of work

- Jon: engine, generator, prose pipeline, SFT runs, repo.
- Eitan: eval harness, edit set, prompted baselines, mortgage domain, blind annotation, related work.
- Both: error analysis, report, slides.

## Sources

- Closest work: CREDIT 2610.35295 (model's own reliance as the target), Doi et al. 2512.07288 (attribution-derived explanation supervision), Mayne et al. 2509.09396 and 2602.02639 and Hase and Potts 2602.20710 (simulatability), Karvonen et al. 2608.16747 (no-uplift baseline), Guo et al. 2606.32038 (explanations track the drifted model). No paper found that compares invented and real rule domains for explanation SFT.
- Why the control matters: Breaking the Chain 2603.16475 (accuracy up, faithfulness flat).
- Simulator choice: Yu et al. 2608.12253 is about user-simulator collapse in multi-agent RL. It supports only the general point that 1 frozen simulator can bias results.
- Mixing and priors: Chandra et al. 2512.22255, Yamin et al. 2506.15732, Xu et al. 2601.18352.
- Related benchmarks: RuleArena 2412.08972, AbstentionBench 2506.09038, ConditionalQA 2110.06884, policy compliance 2603.00369.
- Self-prediction: Binder et al. 2410.13787, Chua et al. 2403.05518.
