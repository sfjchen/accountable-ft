# Domains and rules: what to decide with Eitan

4 invented domains exist in `domains/*.yaml`. Suggestion: train on grant, trial and review, hold out permit. Below: how a rule becomes logic, what each domain contains, what is open.

## 1. From yaml to logic

- A policy is a conjunction of rules over typed facts.
  - Facts are ints bucketed to at most 8 values, enums, or bools. Small domains keep every check exact.
  - The yaml is the single source. The engine compiles each rule condition to a lambda over a fact dict.
- Conversion table.

| Yaml | Logic | Example (grant) |
|---|---|---|
| `cond` | rule holds iff cond | `requested_amount <= 90000` |
| `unless: cond2` | rule := cond ∨ cond2 (exception waives it) | `… ∨ (institution_type = community_lab ∧ requested_amount <= 120000)` |
| `scoped`, written `A or B` | conditional rule: trigger ¬A, requirement B. `near` marks the distractor (trigger off, B false) | `institution_type ≠ hospital ∨ travel_amount <= 5000` |
| `derived_facts` | named expression over source facts, never edited directly | `duration_weeks = (end_day − start_day) // 7` |
| `defaults` | fill a missing fact before evaluation, the account must cite them as assumptions | `letter_of_support := false` |
| `params` | threshold placeholders | `t ∈ {70000, 90000, 110000}` |

- Family vs policy vs case.
  - Family = which rule templates, exceptions and defaults a policy uses, before thresholds.
  - Policy = a family with thresholds filled in.
  - Case = one applicant's facts under one policy, rendered in 3 views.
- Decision semantics.
  - All facts known: approve if every rule holds, else deny.
  - Facts missing (after defaults): approve if every admissible completion approves, deny if every one denies, else "cannot determine".
  - Gold account = a sufficient set of cited facts, rules and defaults: it fixes the decision under every completion.
  - Smallest flip = fewest fact changes that reverse the decision. All of this is exact backtracking with a time budget.

## 2. The 4 domains

- Grant (Halbrecht Early Inquiry Grants). 12 facts, 12 templates, 5 defaults.
  - Rules: years since PhD cap (career-break exception), amount cap (community-lab exception), letter of support unless university, open-data plan unless hospital, allowed host types, earliest start, equipment cap, ethics approval if human subjects, hospital travel cap, big requests need a letter, project length, equipment plus travel cap.
  - Defaults: no letter, no career break, no data plan, host is an institute, no ethics approval.
- Trial (Protocol VX-118 enrollment). 12 facts, 13 templates, 4 defaults.
  - Rules: age range, biomarker floor (index exception), index ceiling, clearance floor (tier-A exception), washout, no prior drug, no anticoagulant unless tier A, tier-C age cap, no anticoagulant with bleeding history, older patients need higher clearance, heart-rate cap on anticoagulants, consent window, composite score cap.
  - Defaults: no anticoagulant, no prior drug, site tier B, no bleeding history.
- Review (SQM 2027 submissions). 16 facts, 14 templates, 6 defaults.
  - Rules: page limit (position-track exception), anonymity unless position, no dual submission unless non-archival, deadline (extension exception), supplement size (applied exception), anonymized supplement, author cap for position papers, reference cap for applied, no same-institution reviewer, extension page cap, ethics statement if human subjects, artifact license, total pages, coauthor conflict window.
  - Defaults: no ethics statement, no license, no conflict, no extension, supplement not anonymized, venue archival.
- Permit (Marrowgate street equipment), held out. 12 facts, 10 templates, 3 defaults.
  - Rules: weight cap (operator-level exception), insurance floor unless class K1, no night work unless non-residential, operator level, crane needs insurance, sidewalk closure needs notice, residential weight cap, night crew minimum, lead time, placement length.
  - Defaults: no notice, no night work, residential zone.

## 3. Why these 3 for training

- Same rule shapes everywhere (threshold, bool requirement, exception, conditional, derived, default).
  - So a held-out family is a new combination with new thresholds, and permit is the real vocabulary transfer.
- Every domain has 2 derived facts and several defaults.
  - Assumptions and multi-fact reasoning show up in every case, which is where accounts matter.
- Three registers (funding, clinical, academic) keep the prose varied without changing the schema.

## 4. Known data issues (audit Nov 7, `docs/audit_cd.md`)

- Engine labels are sound: every "cannot determine" item has a valid witness pair.
- Gemini prose distorts about 10% of cannot-determine items.
  - "university" rendered as "an academic institution" (lossy enum), and prose implying supplementary files exist when the size fact is missing.
  - Fix in place: 222 items flagged and dropped at export, generator now rejects lossy enum sentences.

## 5. Open with Eitan

- Keep permit as the held-out domain, or add a 5th (housing benefit, visa) and hold out 2. A 5th costs about $3 of prose and an afternoon of yaml.
- Hold whole rule templates out of training too, so "unseen" means new rule shapes. Cheap follow-up.
- Split the 100-item blind labeling.
