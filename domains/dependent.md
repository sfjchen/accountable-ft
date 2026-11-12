# Source policy: claiming a dependent, tax year 2026

Built from the IRS qualifying child and qualifying relative tests. This is a simplified policy built from real rules, not the full tax code.

## Rules and where they come from

| Rule key | Rule | Source |
|---|---|---|
| citizen | U.S. citizen, national or resident alien, or resident of Canada or Mexico, unless a U.S. citizen adopted the person and they lived together all year | Pub. 501, citizen or resident test |
| joint_return | The person may not file a joint return, unless only to claim a refund of withheld tax | Pub. 501, joint return test |
| dependent_taxpayer | A taxpayer who can be claimed as someone else's dependent may not claim anyone | Pub. 501, dependent taxpayer test |
| qc_relationship | A qualifying child is the taxpayer's child, stepchild, placed foster child, sibling, or a descendant of one of them | Pub. 501, relationship test |
| qc_age | Under 19, or a full-time student (5 months) under 24, or permanently and totally disabled | Pub. 501, age test |
| qc_younger | Younger than the taxpayer, unless disabled | Pub. 501, age test |
| qc_residency | Lived with the taxpayer more than half the year. Temporary absences count as time lived together. A signed Form 8332 lets a noncustodial parent claim the child | Pub. 501, residency test and divorced parents rule |
| qc_support | The child did not pay more than half of their own support | Pub. 501, support test |
| qr_not_qc | A qualifying relative is not anyone's qualifying child | Pub. 501, not a qualifying child test |
| qr_household | Someone not on the relative list (a cousin, for example) must live with the taxpayer all year | Pub. 501, member of household or relationship test |
| qr_income | Gross income under $5,300 for 2026 ($5,200 for 2025, $5,050 for 2024). Rent counts before expenses | Rev. Proc. 2025-32, Pub. 501 gross income test |
| qr_support | The taxpayer provides more than half of the support, or more than 10% under a multiple support agreement (Form 2120) | Pub. 501, support test and multiple support agreement |
| tie_break | If a parent also claims the child, a non-parent may not | Pub. 501, tiebreaker rules |

## Simplifications

- 1 policy covers both claim types. Each test is a rule scoped to its claim type, so the other type's tests act as near-miss distractors.
- The claim type is fixed: edits never change it, so flips come from facts about the person.
- A temporary absence waives the residency count outright.
- The tie-breaker keeps only "a parent beats a non-parent".

## Why it is a useful real domain

- Rules go against common sense: rent counts before expenses, in-laws are listed relatives but cousins are not, and a 23-year-old student can still be a qualifying child.
- Missing facts arise naturally: without the person's income, a qualifying relative claim can't be decided.

## Sources

- [IRS Publication 501](https://www.irs.gov/publications/p501)
- [Rev. Proc. 2025-32 (2026 inflation adjustments)](https://www.irs.gov/pub/irs-drop/rp-25-32.pdf)
