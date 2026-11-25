# Source policy: Federal FMLA leave requests, 2026

Built from the Family and Medical Leave Act and its DOL regulations. This is a simplified policy built from real rules, not the full law. It is a held-out test domain: no model trains on it.

## Rules and where they come from

| Rule key | Rule | Source |
|---|---|---|
| employer_coverage | Private employer with 50+ employees on the payroll each working day in 20+ workweeks of this or the last calendar year. Public agencies and schools are covered at any size | 29 USC 2611(4), 29 CFR 825.104, 825.108 |
| tenure | Employed at least 12 months | 29 USC 2611(2), 29 CFR 825.110(a) |
| break_in_service | Employment before a break of 7 years or more does not count, unless the break was USERRA military service or a written agreement says the employer would rehire | 29 CFR 825.110(b) |
| hours | At least 1,250 hours worked in the 12 months before leave | 29 USC 2611(2), 29 CFR 825.110(c) |
| flight_crew | Airline flight crew instead need 504 hours and 60% of the monthly guarantee worked or paid | 29 CFR 825.800-801 |
| worksite | 50+ employees at the worksite or within 75 miles | 29 USC 2611(2)(B)(ii), 29 CFR 825.110(a)(3), 825.108(d) |
| qualifying_reason | Birth bonding, adoption or foster placement, own serious health condition, spouse, child or parent with one, qualifying exigency, military caregiving. Not siblings, grandparents, parents-in-law, minor illness or vacation | 29 USC 2612(a)(1), 29 CFR 825.112-127 |
| bonding_window | Bonding leave within 12 months of the birth or placement | 29 CFR 825.120(a)(2), 825.121(a)(1) |
| military_status | Exigency needs a spouse, child or parent on covered active duty abroad. Caregiver leave needs a covered servicemember with a serious injury or illness | 29 USC 2612(a)(1)(E)-(F), 29 CFR 825.126-127 |
| notice | 30 days of notice, or as soon as practicable when 30 days was not | 29 USC 2612(e), 29 CFR 825.302-303 |
| certification | Return a requested certification within 15 calendar days, unless not practicable despite diligent, good-faith effort | 29 CFR 825.305(b) |
| key_employee | Restoration may be denied to a key employee (salaried, top 10% paid within 75 miles) if it causes substantial and grievous economic injury, and only with timely written notice | 29 USC 2614(b), 29 CFR 825.217-219 |
| entitlement | 12 workweeks per 12-month leave year, 26 for military caregiver leave, minus weeks used | 29 USC 2612(a)(1), 29 CFR 825.200, 825.127 |
| spouse_share | Spouses at the same employer share 12 weeks of bonding leave | 29 USC 2612(f), 29 CFR 825.120(a)(3), 825.121 |

## Simplifications

- Approve means the leave must be granted with job restoration, so the key employee rule (which limits restoration only) denies the whole request.
- Coverage reads 1 headcount. Joint employers and successors are left out. School district headcounts are not pooled.
- Break rule: 825.110(b)(1) says "7 years or more" and (b)(2) says "more than 7 years" for exceptions. Values avoid exactly 7.
- Serious health condition, covered active duty and covered servicemember are folded into reason plus 1 covered_military fact. Children over 18 and incapable adult children are left out.
- A request over the remaining entitlement, or with short notice and no excuse, fails whole. In law the leave is protected up to the entitlement, and the employer may only delay leave on a notice miss.
- Spouse sharing is applied to bonding only. In law it also covers caring for a parent.
- Airline crew entitlement (72 days, 156 for caregiver) is the 12 and 26 week figures. The 26-week combined cap for caregiver plus other leave is 1 number.
- The leave year method, intermittent leave, paid leave substitution, light duty, the 1,250-hour teacher presumption and state laws are left out.
- Integers are bucketed to at most 8 values.

## Why it is a useful held-out domain

- Different shape from SNAP: no money thresholds, instead a stack of eligibility gates with many exceptions (break excused, notice excused, certification excused, key employee notice).
- Facts interact: weeks used moves the limit by reason (12 vs 26), a spouse's weeks reduce bonding weeks, and the flight crew test replaces the hours test.
- Some rules go against common sense: siblings and parents-in-law do not count, the 12-month clock restarts only after a 7-year break, and a key employee with no written notice keeps full protection.

## Sources

- [29 USC 2611-2619](https://uscode.house.gov/view.xhtml?path=/prelim@title29/chapter28&edition=prelim)
- [29 CFR Part 825](https://www.ecfr.gov/current/title-29/subtitle-B/chapter-V/subchapter-C/part-825)
- [DOL Fact Sheet #28 and #28A-#28Q](https://www.dol.gov/agencies/whd/fact-sheets)
