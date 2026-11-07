# Audit of v1 "cannot determine" items

Logs: `audit_cd-e856952-20261107-0241.log` (primary slice, prose) and `audit_cd-train-e856952-20261107-0241.log` (train), from `scripts/audit_cd.py`.

## Counts

- Primary: 205 cd of 1513 items (grant 70, review 76, trial 59). Train: 244 of 1869.
- Engine side is sound: 205/205 witness pairs hold, the removed fact is always needed, and the 4 missing-fact lexicon hits are false positives.
- Text side, primary (train):
  - 7 (2) cd items have a lossy enum sentence.
  - 13 (9) have supp_mb missing but a sentence that presupposes supplementary files exist.

## Enum renderings that lose the value

The yaml strings keep every value. Only grant.institution_type loses it, in Gemini prose: university as "an academic institution" (138 uses), institute (16), hospital (10) and community_lab (8). permit, review and trial have none.

## 30-item read (10 per domain, seed 0)

- 23 clean: trial 10, grant 9, review 4.
- grant-p100-c01 says "an academic institution located in the Vessel Bay region", the reviewer's pattern. On grant-p000-c02 the model denied on the host-type rule.
- 2 labels are wrong to a reader. In review-p023-c01, "Institutional logos belonging to the authors remain visible within the supplementary archive" implies supp_mb > 0.
- 4 items contradict themselves: review-p085-c01 states 0 MB yet "The supplementary documents reveal the names of the contributors".
- The model gave 0 cd answers on 97 cd items. The reviewer's deny is mainly an abstention failure.

## Verdict

The cd labels are trustworthy for training on Nov 9 after a filter. I drop the cd items flagged `zero_guard_presupposed` or carrying a lossy enum sentence (11 train), plus any other item with a lossy enum sentence (27 train in total). Before regenerating, I rewrite the supp_anonymized and artifact_license say_false strings so they don't presuppose supplementary files. I also reject Gemini enum sentences that lack the value's name token.
