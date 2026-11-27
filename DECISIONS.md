# Decisions and results

The design, every result the report cites with its log, and the limits. Short guide in [README.md](README.md), commands and clusters in [OPS.md](OPS.md). Every number comes from a `stamp-run` log at 28ca8c9 (`~/dev/logs/final-*-eval-28ca8c9-*`, JSON in `~/dev/logs/evals-final/`) unless a line names another log. Simulator numbers use the fixed prompts (see Simulator prompt fix). Opus was rerun on the grid only.

## Claim

- Question: can fine-tuning make a model's stated reasons predict what it does when the facts change?
- Claim: on invented rule domains, training on engine-verified explanations makes explanations case-specific and predictive of the model's own post-edit answer, beyond a matched decision-only control, with accuracy non-inferior on the training-domain test (v1).
- Not claimed.
  - That explanations are how the model computes (causal faithfulness needs interpretability tools).
  - That own explanations reveal the model's errors. The check ran before the simulator prompt fix (Controls).
  - Transfer to real rules. The registered real-rules test failed (Row-matched grid).
  - Anything about real clinical, legal or lending use.

## Design

- Invented policy domains with exact labels. A Python rule engine gives the correct decision, every minimal sufficient set of facts, the minimal flip and "cannot determine" witnesses. Brute-force enumeration in the tests cross-checks it. Invented, so nothing leaks from pretraining. Real domains (mortgage, SNAP, IRS dependent) use the same schema with real thresholds, so priors can pull against the text.
- Matched control. Explanation SFT and decision-only SFT see the same cases, prompts and target sequences. Decision-only zeroes the explanation tokens in the loss. Loss = mean decision-token loss + λ x mean explanation-token loss, so decision tokens carry equal weight in both (otherwise 95% of supervised tokens on v1 are explanation tokens). Decision comes first in the target.
- Split by rule family, so test policies are new combinations and thresholds. Every rule shape also appears in training, so "unseen family" is threshold-and-combination transfer. Permit (a whole invented domain never trained on) is the real vocabulary transfer test.
- Endpoint, no LLM judge: simulatability gain. A frozen simulator (Gemini 3.5 Flash-Lite, Claude Opus 5.5 as the 2nd family on the grid) sees the policy, the model's decision, its explanation and an edit, never the case, and predicts the model's fresh post-edit decision. Gain = accuracy with the model's own explanation minus with another case's explanation under the same policy, own Decision line kept.
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

Qwen3.5-9B LoRA, 3 seeds, epoch 2, means over seeds. Paired = explanation minus decision-only, seed by seed (logs `final-v1-gemini-eval-28ca8c9-20261125-0023`, `final-mortgage-gemini-eval-28ca8c9-20261125-0023`).

| v1 unseen families | explanation SFT | decision-only | prompted base | paired |
|---|---|---|---|---|
| accuracy | 0.976 | 0.972 | 0.627 | 0.004 [-0.008, 0.016] |
| explanation validity | 0.773 | 0.000 | 0.067 | 0.773 [0.746, 0.797] |
| decision follows own explanation | 0.968 | | 0.550 | |
| simulatability gain, Gemini | 0.115 | 0.016 | -0.008 | 0.099 [0.066, 0.131] |
| always-"unchanged" baseline | 0.412 | 0.425 | 0.856 | |

- Both SFT conditions fix the base model's failure modes (accuracy 0.63 to 0.97, "cannot determine" 0 to 0.95), so accuracy comes from the shared data and the explanation loss adds predictiveness on top. Gain is 0.09-0.14 in each of the 3 domains (paired +12.8 grant, +8.6 trial, +7.5 review, each CI clear of 0).
- Mortgage (never trained on): validity 0.374, accuracy +0.014 [-0.020, 0.049], gain +0.008 [-0.036, 0.050].
- Permit (never trained on, log `final-permit-gemini-eval-28ca8c9-20261125-0023`): gain +9.9 [6.6, 12.9], validity 43% vs 0, accuracy 93.0% vs 94.6% (-1.6 [-3.5, 0.5]), base 70.4%.
- Power (log `r1-v1-power-1332e96-20261110-1459`, before (1332e96)): minimum detectable gain difference 5-8 points per seed pair.

### Controls

- Placeholder confound. Decision-only still prints explanation lines as unlearned placeholders, so the paired gap partly compares well-formed with malformed lines. The 2 controls below remove that.
- Wrong-reason control (`infer.py --wrong-accounts`): keeps decision, format, item count and length, swaps the cited facts for true stated facts that leave the case open. Own minus wrong +7.9 on v1 (seeds 7.9, 6.8, 8.9, each CI clear of 0), +10.7 on answer-changing edits. Mortgage +2.1 (seeds 2.4, 2.8, 1.0, each CI covers 0) of a 2.6 gain, wrong minus shuffled +0.5. So the invented-test gain needs the right reason, while the mortgage gain is too small for the control to read.
- Prompted-explanation control (`--mode explain`, logs `final-v1-peB-gemini-eval-28ca8c9-20261125-0027`, `final-mortgage-split-peB-gemini-eval-28ca8c9-20261125-0030`): the base model writes explanation lines for the SFT model's fixed decision. Trained minus prompted on the same decisions: v1 +4.3 [1.2, 7.5], mortgage -0.8 [-5.4, 3.6]. The edge sits on answer-changing edits (v1 +10.6 [6.0, 15.7]). Prompted lines are 1.7x longer and cite distractors 75% of the time (13% trained).
- Explanation vs none, Gemini on v1: 0.684 with the model's own explanation, 0.569 with a shuffled one, 0.389 with none, so the own explanation informs the simulator, not only the shuffled one misleading it.
- Round 1 Opus passes, the Opus no-explanation passes and the `compare_sims.py` error check (own explanations don't track the model's errors) ran before the prompt fix and were not rerun, so they are no longer cited.

### Round 2 and mortgage-only

- Round 2 trains grant, trial and mortgage (review held out). Mortgage-only is seed 0 only. Paired Gemini gain, v1 / mortgage: round 2 +0.104 / +0.074 [0.015, 0.131], mortgage-only -0.008 / +0.070. Accuracy, v1: round 2 +0.033 [0.020, 0.049].
- Training on mortgage moves the mortgage gain from +0.008 (round 1) to +0.074. Round 2 vs mortgage-only confounds mix with size (3x rows) and seeds, which the grid removes.

### Row-matched grid (pre-registered Nov 12)

- 3 mixes at 3,600 train rows, equal share per domain: `rm-inv` grant + trial, `rm-real` mortgage + SNAP, `rm-mix` all 4. 2 conditions x 3 seeds = 18 runs. Tests: unseen families of the 4 training domains, plus review and IRS dependent, both held out from every mix. Logs `final-<test>-grid-{gemini,opus}[-raw]-eval-28ca8c9-*`.
- Registered main score, paired Gemini gain on IRS dependent: failed. inv -7.9 [-11.2, -4.4], real -4.3 [-9.0, 0.3], mix -3.1 [-8.5, 2.0]. The predicted order (mix >= real > inv) holds for point estimates only, no contrast clears Holm. Opus -1.9 / +0.3 / +2.5, no CI clear of 0. The review prediction also failed (Gemini +1.1 / +4.5 / +2.5, every CI crosses 0).
- Gain by test, Gemini (inv / real / mix): grant 8.0 / 3.3 / 5.5, trial 8.0 / 3.3 / 5.2, review 1.1 / 4.5 / 2.4, mortgage 0.1 / 3.9 / 6.2, SNAP 2.8 / 2.0 / 3.9. No gain contrast clears Holm. Opus agrees except on mortgage: 1.2 / 12.1 / 8.2.
- Explanation correctness, all 18 paired contrasts (explanation vs decision-only) clear Holm: each specialist is best on its own kind (the other trails by 17-47 points), mix is best on review and within 2-8 points elsewhere. Mix accuracy matches or beats decision-only on every test (up to +6.5 on IRS dependent).
- Wrong-reason control on the grid, own minus wrong, Gemini (inv / real / mix): v1 +7.0 / +7.6 / +5.9, mortgage +1.5 / +3.7 / +3.3, SNAP +13.5 / +7.1 / +4.7, IRS dependent +3.5 / +0.5 / +2.4. Opus: v1 +9.7 / +10.1 / +11.4, mortgage +3.4 / +13.4 / +13.6, SNAP +11.0 / +5.6 / +6.0.

#### Post hoc: new test families (registered Nov 14, a robustness check, not a retest)

- Families of review and IRS dependent that no grid model trained on, and new families of the 4 training domains (`data/*-x.jsonl`). Pooled only where old minus new covers 0, which now holds everywhere except Opus SNAP invented-only (+5.6 [1.6, 10.0]).
- Holm-clear pooled gain contrasts, Gemini: mix - inv +5.8 [2.6, 9.1] and real - inv +5.4 on mortgage. On v1 invented-only leads (mix - inv -2.5, real - inv -3.4). None on SNAP, review or IRS dependent.
- Own minus wrong, pooled, Gemini: mortgage +1.6 / +6.5 / +7.2, SNAP +15.1 / +7.4 / +6.4, review +7.1 / +8.8 / +5.9.
- Opus on the new mortgage and SNAP families, registered Nov 20 before any result (`sim.sh` with `SIMS=own+shuf`, own and shuffled passes on all 18 runs). Read: mix - real on mortgage, new alone and pooled. The Opus mortgage gap replicates if the pooled CI stays below 0, and is a small-sample result if it covers 0. SNAP and the other 2 contrasts are secondary.
  - Result after the prompt fix: replicates on the registered paired gain, at half the size. Mortgage mix - real -3.3 [-6.4, -0.3] new alone (Holm 0.064), -3.4 [-6.0, -0.8] pooled (Holm 0.008), accuracy equal (-1.2 [-2.8, 0.3]). SNAP -2.9 [-5.0, -0.7] new alone, -1.8 [-3.9, 0.4] pooled. Mixed beats invented-only on mortgage (+4.5 [1.5, 7.4] pooled). The readout below shows the gap comes from the decision-only subtraction.

#### Simulator prompt fix (registered Nov 21, before any rerun result)

- Flaw: the simulator saw the bank id as Edit ID, which ends in the edit kind (`pivotal_replace`, `noncrossing_replace`). On v1 a rule from that suffix and the original decision predicts 95.5% of explanation-SFT answers, about what Opus got with no explanation. Shuffle partners also had another decision in 483 of 748 v1 seed-0 items, so their Policy support contradicted the Decision line kept.
- Fix (539e723): an opaque Edit ID and a same-decision partner whenever the policy has one. Every simulator pass the cited evals read reran (`resim.py`), and Opus got wrong-reason passes on the 9 grid explanation runs. Scoring reads the opaque id since e6fbbe1.
- Readouts, fixed before the rerun: registered endpoints keep their definitions. Mixed vs real-only reads first own minus wrong-reason on the explanation runs (`--contrast-raw account`, `sim_dwrong`), which stays within a run and avoids the decision-only placeholder lines, then the raw own-minus-shuffled contrast, then the registered paired gain. The simulators disagree only if the primary contrasts clear 0 in opposite directions on mortgage or SNAP (pooled). This order was set after the Nov 20 Opus result above and the pre-fix raw logs had shown the paired gap, so it is a post hoc choice of primary endpoint.
- Result: no disagreement on mix - real by the registered rule, and no difference detected (primary CIs within about 3 points of 0). Mix - real, pooled, Gemini / Opus (logs `final-{mortgage-split,snap}-x-pool-grid-{gemini,opus}[-raw]-eval-28ca8c9-*`):

| contrast | mortgage | SNAP |
|---|---|---|
| own - wrong (primary) | +0.7 [-1.2, 2.6] / +0.8 [-1.0, 2.7] | -1.0 [-2.6, 0.7] / -1.0 [-2.8, 0.8] |
| raw own - shuffled | -0.1 [-2.2, 2.1] / -1.2 [-3.1, 0.8] | -1.4 [-3.1, 0.1] / -0.0 [-1.5, 1.5] |
| paired gain (registered) | +0.5 [-2.0, 3.2] / -3.4 [-6.0, -0.8] | -1.0 [-3.6, 1.7] / -1.8 [-3.9, 0.4] |

- No primary contrast clears 0 under either simulator. The Opus paired mortgage gap splits by arithmetic into -1.2 from the explanation runs and -2.2 from the decision-only runs (their own gain, mix 6.5 vs real 4.3), with no CI on the split. Elsewhere the simulators differ: SNAP own minus wrong, mix - inv, pooled, is -8.5 [-11.6, -5.4] under Gemini and +1.2 [-1.7, 4.1] under Opus.
- On invented tests the raw contrast favors mixed (v1 +5.2 [2.0, 8.3] / +8.2 [5.4, 11.1]), since real-only never trained there, while own minus wrong ties (-1.8 / +1.3).
- Over all 6 tests, own minus wrong averages inv / real / mix 6.6 / 5.7 / 4.6 under Gemini and 6.9 / 8.6 / 9.7 under Opus (log `final-grid-seeds-28ca8c9-20261125-0523`). Opposite order, and for mix - real no test clears Holm under either.
- Before the fix (logs `final-*-grid-{gemini,opus}-raw-eval-b8301d2-*`, before (b8301d2)): the Opus mortgage gap was -6.5, -2.8 from the explanation runs and -3.7 from the subtraction.

#### Mix recommendation

- The pick depends on the workload, not on gain. Mean over all 6 tests, inv / real / mix: correctness 39.8% / 40.2% / 49.4%, accuracy 78.2% / 79.8% / 87.1%. Over the 3 real-rule tests (mortgage, SNAP, IRS dependent): correctness 18.9% / 44.1% / 39.7%, accuracy 67.4% / 82.9% / 84.1% (log `final-grid-seeds-28ca8c9-20261125-0523`). Mixed beats real-only on invented tests (correctness +11 to +29) and trails it by 3-6 points on each real test (point estimates, SNAP and IRS dependent CIs cover 0).
- Pick: mixed for a benchmark that weights invented and real rules equally (best accuracy and correctness), real-only for real-rule use (4 points more correctness, mixed 1 point more accurate). Neither choice changes gain.
- Not more data (log `final-grid-seeds-2005f39-20261120-1856`): every mix has 3,600 rows, 266-270 root cases, the same variant shares and the same steps. Real-only has the most text, 1.49M explanation characters vs 1.28M mixed (5.55M vs 4.76M training tokens in sc's `train_meta.json`). Mixed has 2x the families (120 vs 60) and 1.7x the policies (202 vs 119) at half the rows per domain, so the open confound is diversity vs per-domain dose, not volume.
- Gain does not separate mixed from real-only. The primary contrast shows no difference on mortgage or SNAP under either simulator (Simulator prompt fix). On the paired gain averaged over the 6 tests by seed, mixed is higher in 8 of 9 seed pairs under Gemini (mix 4.1 / 3.5 / 2.6, real 0.5 / 3.4 / 2.5) and 7 of 9 under Opus (7.6 / 5.3 / 5.7 vs 5.0 / 4.2 / 6.7). On the 2 real tests Opus favors real-only in 7 of 9 pairs, mostly through the decision-only runs (above). Opus mortgage mix - real on the 24 original families flips by seed (+3.1, -9.0, -5.6).
- Limits: CIs pool the 3 seeds and resample families only. Holm covers the 3 contrasts within 1 test, metric and simulator, not 6 tests x 2 simulators. 1 held-out domain per kind.

### Real vs invented for real-rule use (registered Nov 24, before any data)

- Question: when the target is real rules, does a real domain beat an invented one at matched structure? The grid could not say, since real-only had 60 families and mixed 120.
- Arms, explanation SFT only, 3,600 train rows, 2 epochs, seeds 0-4. M = `rm-mix` (grant, trial, mortgage, SNAP; seeds 0-2 exist, 3-4 new). R4 = Medicaid (expansion adults) and WIC, both new real domains (WIC at 116 policies and 8 cases per family, 29 train families, the most its rules allow at the family-distance floor; Medicaid 120 policies, 30), plus M's exact mortgage and SNAP rows (`train.py export --reuse`). Each arm has 120 rule families and 900 rows per domain, so R4 - M swaps 2 invented domains for 2 real ones and nothing else.
- Held-out tests, never trained by either arm, equal weight: IRS dependent (original and new families pooled) and FMLA leave, a new real domain outside tax and benefits. Domain files written before any model answers them. Secondary: mortgage-x and SNAP-x, own minus wrong-reason with Gemini.
- Primary endpoint: joint success, the decision is right and the explanation is engine-valid and cites at least 1 binding rule when it denies or cannot determine (`joint`). Uncertified explanations count as failures. Score per seed = mean of the 2 held-out domains' rates.
- Test: R4 - M on per-seed scores, Welch t 95% CI over the 5 + 5 seeds (seeds are the unit, since seed spread exceeds family noise), family-clustered CI reported beside it. R4 better if the CI excludes 0, equivalent if it lies within ±3 points, otherwise inconclusive. Guardrail: the accuracy CI must exclude a 5-point loss for the winner.
- Readout: R4 better -> for real-rule use, train on real domains, invented ones add nothing. Equivalent -> invented domains substitute for real ones of the same structure. M better -> invented domains help real-rule transfer. Each held-out domain is also reported alone, and a split between them is reported as such.

### Error analysis and diagnostics

- IRS dependent failures (`errors.py`, 25 wrong decisions and 25 simulator misses from the 9 explanation-trained grid runs, labels in `data/errors-dependent.jsonl`, log `final-dependent-errors-eval-28ca8c9-20261125-0221`).
  - Wrong decisions cite a rule that an exception waives (690 of 2,309) or that covers the other claim type (757).
  - Simulator misses: the edit fixes the cited reason and the answer stays deny (326 of 549 answer-stays misses).
  - The model says "cannot determine" on 76 of 684 cases that need it. Training taught the format, not the scope and exceptions of the IRS rules.
- Arithmetic: case text states every computed value, so no model computes. Among denials, real and mixed models gain most where the failing rule reads a derived value (original families, paired gain on those denials vs the rest: mortgage real +9.2 vs +0.6 and mixed +20.2 vs +0.6, SNAP mixed +17.1 vs -0.7), invented-trained models don't, so it follows training domain. A diagnostic, not a design axis.

## Limits

- 1 schema, 1 model size (9B), 2 domains per kind. "Unseen family" reuses training rule shapes.
- Real-rules transfer is not shown. Round 1 mortgage gain is near 0 and the registered IRS test is negative.
- Real-only dose arm not run (rm-real at 1,800 rows, matching mixed's real rows). A clean arm filters mixed's own mortgage and SNAP rows (only 1,455 of its 1,800 are in rm-real, and a fresh 900-per-domain export draws other cases), keeps 2 epochs (so half the steps) and reads mixed minus it on mortgage. Neither outcome changes the pick, which rests on correctness, and grid power (5-8 points) could not read a null. After the prompt fix mixed and real-only tie on mortgage on the primary contrast, so the arm has no gap left to explain.
- Opus is not temperature-controlled (Claude Code headless), so a rerun can differ slightly.

## Decision log

- Oct 31: invented domains over real policy text. Real text has no exact labels and leaks from pretraining.
- Nov 5: endpoint moved from self-prediction to the external simulator, since a self-predictor re-solves the case (0.77-0.84 with no explanation). Pivotal edits made independent of the correct smallest change.
- Nov 7: shuffled control keeps the item's own Decision line (the old version made most of the pilot gain), always-"unchanged" baselines added, fixed epoch for every condition, matched loss weighting, "cannot determine" kept as a 3rd class.
- Nov 9: mortgage merged (Eitan), `acct_consistent` added after his pilot showed answers contradicting their own numbers. Round 2 replaces a 2x2 cross-evaluation (1 new mix, reuses round 1).
- Nov 12: row-matched grid pre-registered. Nov 14: new test families registered as post hoc.
- Nov 13-19: prompted-explanation, wrong-reason and permit controls.
- Nov 20: metrics review. Boundary and necessity metrics removed (their GPU pass never ran), repeat and self-prediction passes opt-in. Every report eval rescored at abaa830.
- Nov 21: Edit ID leak and cross-decision shuffle partners found. Fix and readout order registered before any rerun (539e723).
- Nov 22-24: every cited simulator pass rerun (Gemini everywhere, Opus on the grid plus wrong-reason passes). Scoring fixed to read the opaque Edit ID (e6fbbe1), then to map exact enum names (24f596c, 28ca8c9), every report eval rescored at 28ca8c9.
- Nov 24: Medicaid 5-year bar fixed (40 work quarters is not an exception) before any training. Real vs invented arms registered (R4 vs M, 5 seeds, joint success on IRS dependent and FMLA). Medicaid, WIC and FMLA data generated, the arms job submitted on sc (job 18694708, `cluster.sh arms`: R4 s0-4, M s3-4 trained, M s0-2 answer FMLA), with R4 and M s3-4 also queued on FarmShare (job 2020563). Each seed keeps the copy that starts first and the other is cancelled, so no seed mixes clusters. Outcome: sc ran R4 s0-2 and s4 (Nov 26, 2.7-3 h each) and FarmShare ran M s3-4 (Nov 26, 1.6 h each), the other copies were cancelled, and sc R4 s3 was preempted at 85% of training and requeued. Scoring fix before any arms answer: a cited enum value's exact display name now maps to it, since names such as "no SNAP, TANF or Medicaid in the family" tripped the negation guard and scored correct citations as wrong (gold targets scored 0.22-0.80 valid on the real domains, 0.91-1.0 after). A 2nd fix (28ca8c9): exact names keep internal punctuation, and the enum value "none" counts as a value, which restores SNAP and mortgage fact consistency that the 1st fix had dropped. Every report eval rescored at 28ca8c9: SNAP correctness rose 25-26 points for real-only and mixed (real-only 32.0% to 58.2%) and 0 for invented-only, trial rose 4-5 (the old fallback read "a tier A Halvard site" through the article), mean correctness over 6 tests went from 39.0 / 35.8 / 44.5 to 39.8 / 40.2 / 49.4 (inv / real / mix), and mean gain and accuracy did not move. Real-rule pick is a trade-off: real-only explains better (44.1% vs 39.7%), mixed is slightly more accurate (84.1% vs 82.9%).
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
