# Domains: what we have and what to pick

For the check-in with Eitan. 4 invented domains exist in `domains/*.yaml`. Suggestion: train on grant, trial and review, hold permit out as the transfer domain, which is the current split. Below is what each looks like and how a rule becomes logic the engine checks.

## How a rule becomes formal logic

Every policy is a conjunction of rules over typed facts with small finite domains (ints bucketed to at most 8 values, enums, bools). The yaml is the single source. The engine compiles each rule to a lambda over a fact dict. Conversion rules:

| Yaml | Logic | Example (grant) |
|---|---|---|
| `cond` | the rule holds iff cond | `requested_amount <= 90000` |
| `unless: cond2` | rule := cond ∨ cond2 (exception waives it) | `… ∨ (institution_type = community_lab ∧ requested_amount <= 120000)` |
| `scoped` rule `A or B` | conditional rule, trigger ¬A, requirement B. `near` marks the distractor case (trigger off, B false) | `institution_type ≠ hospital ∨ travel_amount <= 5000` |
| `derived_facts` | named expression over source facts, never edited directly | `duration_weeks = (end_day - start_day) // 7` |
| `defaults` | fill a missing fact before evaluation, the account must cite them as assumptions | `letter_of_support := false` |
| `params` | threshold placeholders, one family = a choice of templates and exceptions, one policy = a choice of thresholds | `t ∈ {70000, 90000, 110000}` |

Decision: approve if every rule holds, deny if some rule fails. With facts missing (after defaults), approve if every admissible completion approves, deny if every one denies, else "cannot determine". A gold account is a sufficient set: the cited facts fix the decision under every completion. The smallest flip is the fewest fact changes that reverse the decision. All checks are exact backtracking searches with a time budget, z3 is a cross check only.

## The 3 training domains

Grant (Halbrecht Early Inquiry Grants). 12 facts, 12 rule templates. Rules: years since PhD cap with a career-break exception, amount cap with a community-lab exception, letter of support unless university host, open data plan unless hospital, allowed host types, earliest start date, equipment cap, ethics approval if human subjects, hospital travel cap, big requests need a letter, project length, equipment plus travel cap. Defaults: no letter, no career break, no data plan, host is an institute, no ethics approval.

Trial (Protocol VX-118 enrollment). 12 facts, 13 templates. Rules: age range, biomarker floor with an index exception, index ceiling, creatinine clearance floor with a tier-A site exception, washout weeks, no prior drug, no anticoagulant unless tier A, tier-C age cap, no anticoagulant with bleeding history, older patients need higher clearance, heart rate cap on anticoagulants, consent window, composite score cap. Defaults: no anticoagulant, no prior drug, site tier B, no bleeding history.

Review (SQM 2027 submissions). 16 facts, 14 templates. Rules: page limit with a position-track exception, anonymity unless position track, no dual submission unless non-archival, deadline with an extension exception, supplement size with an applied-track exception, anonymized supplement, author cap for position papers, reference cap for applied, no same-institution reviewer, extension page cap, ethics statement for human subjects, artifact license, total pages, coauthor conflict window. Defaults: no ethics statement, no license, no conflict, no extension, supplement not anonymized, venue archival.

Permit (Marrowgate street equipment), held out. 12 facts, 10 templates: weight cap with an operator-level exception, insurance floor unless class K1, no night work unless non-residential, operator level, crane needs insurance, sidewalk closure needs notice, residential weight cap, night crew minimum, lead time, placement length. Defaults: no notice, no night work, residential zone.

## Why these 3 for training

- Same rule shapes everywhere (threshold, bool requirement, exception, conditional, derived, default), so a held-out family is a new combination and new thresholds. The permit vocabulary is the real transfer test.
- Each has 2 derived facts and 4 to 6 defaults (permit has 3), so every case can exercise assumptions and multi-fact reasoning, which is where accounts matter.
- Different surface registers (funding, clinical, academic) keep prose variety high without changing the schema.

## What to decide with Eitan

- Keep permit as the held-out domain, or swap in a 5th (for example housing benefit or visa) and hold out 2. A 5th domain costs about $3 of Gemini prose and an afternoon of yaml.
- Whether to hold whole rule templates out of training too (a cheap follow-up that would make "unseen" mean new rule shapes).
- Who labels which half of the 100-item blind sample.
