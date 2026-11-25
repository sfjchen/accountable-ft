# Source policy: WIC participant eligibility, July 2026 to June 2027

Built from the federal WIC rules for the 48 states and DC. This is a simplified policy built from real rules, not the full program.

## Rules and where they come from

| Rule key | Rule | Source |
|---|---|---|
| category | Applicant is a pregnant, postpartum or breastfeeding woman, an infant or a child | 7 CFR 246.2, 246.7(c) |
| postpartum_window | A non-breastfeeding postpartum woman is certified through 6 months after the pregnancy ended | 7 CFR 246.7(g)(1)(ii) |
| breastfeeding_window | A breastfeeding woman is certified until her infant turns 1 (12 months after the birth) | 7 CFR 246.7(g)(1)(iii) |
| child_age | An infant or child is under 5 years (60 months) | 7 CFR 246.7(g)(1)(v) |
| nutritional_risk | A competent professional authority finds nutritional risk, on staff or in outside referral data. Exceptions: an infant under 6 months whose mother was on WIC during pregnancy (or medical records show she qualified), and presumptive certification of a pregnant woman before the risk assessment | 7 CFR 246.7(e)(1)(i), (iv), (v) |
| residency | Applicant lives in the state, with no minimum length of residence. Exception: homeless applicants staying in the state | 7 CFR 246.7(c)(1) |
| proof_docs | Proof of residency and identity at certification. Exception: a signed statement for homeless, migrant farmworker, theft, loss or disaster cases | 7 CFR 246.7(c)(2)(i) |
| presence | Applicant is physically present at each certification. Exceptions: a disability of the applicant or caretaker, and for an infant or child, ongoing health care, a working caretaker, or an infant under 8 weeks | 7 CFR 246.7(o) |
| dual_participation | Not in CSFP or at another WIC clinic at the same time | 7 CFR 246.7(l) |
| income_test | Annual family income at most 185% of the poverty guidelines: $29,526 for 1 person plus $10,508 per extra member. A pregnant woman counts each expected baby as a family member. Waived if the applicant gets SNAP or Medicaid, or is in a TANF family or a family with a pregnant woman or infant on Medicaid | FNS notice, 91 FR doc 2026-08323 (Apr 29, 2026); 7 CFR 246.7(d)(1), (d)(2)(vi)-(vii) |

## Simplifications

- The income limit is 1 base plus a step. It matches the official table for every family size, so nothing is off.
- Expected babies are folded into the family size fact instead of a separate fact.
- Months since birth (women) and age in months (infants and children) are 1 fact.
- Income is 1 annual figure. Income definitions, exclusions and the proof of income documents are left out.
- Adjunctive eligibility covers SNAP, TANF and Medicaid only, not state-administered programs.
- Nutritional risk is 1 enum for the professional's finding. Risk criteria and the priority system are left out.
- The presence exceptions assume the state adopted every optional one, and the prior-visit conditions are dropped.
- State options (citizenship limit, proof of pregnancy, lower income limits, service areas) and public health waivers are left out.

## Why it is a useful real domain

- Rules depend on the applicant type: the same months value passes for a breastfeeding woman at 12 and fails for a postpartum woman at 7.
- Several exceptions sit inside rules, and 2 of them depend on type and age together (infant under 6 months, infant under 8 weeks).
- Some rules go against common sense: a SNAP participant skips the income test entirely, but a family member on SNAP does not count, while a family member on TANF does.

## Sources

- [FNS WIC income eligibility guidelines notice, July 1, 2026 - June 30, 2027 (Federal Register, Apr 29, 2026)](https://www.federalregister.gov/documents/2026/04/29/2026-08323/special-supplemental-nutrition-program-for-women-infants-and-children-wic-20262027-income)
- [7 CFR 246.7, certification of participants](https://www.ecfr.gov/current/title-7/subtitle-B/chapter-II/subchapter-A/part-246/subpart-C/section-246.7)
- [Arkansas WIC income guidelines chart, effective July 1, 2026 (table check)](https://healthy.arkansas.gov/wp-content/uploads/WIC-FY27-Income-Guidelines.pdf)
