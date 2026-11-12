# Source policy: SNAP household eligibility, fiscal year 2027

Built from the federal SNAP rules for the 48 contiguous states and DC. This is a simplified policy built from real rules, not the full program.

## Rules and where they come from

| Rule key | Rule | Source |
|---|---|---|
| gross_test | Gross income at most 130% of the poverty line: $1,729 for 1 person plus $616 per extra member. Waived if a member is 60+ or disabled, or the household gets TANF or SSI | FY2027 COLA memo p.3, 7 CFR 273.9(a) |
| net_test | Net income at most 100% of the poverty line: $1,330 plus $474 per extra member. Waived for TANF or SSI households | FY2027 COLA memo p.3, 7 CFR 273.9(a) |
| (deductions) | 20% of earned income, standard deduction $217 (1-3 members), $229 (4), $268 (5), $308 (6), excess shelter costs above half of the remaining income, capped at $769 unless a member is 60+ or disabled | FY2027 COLA memo p.6, 7 CFR 273.9(d) |
| resource_limit | Countable resources at most $3,000, or $4,750 with a member 60+ or disabled. Waived for TANF or SSI households | FY2027 COLA memo p.7, 7 CFR 273.8 |
| abawd | An able-bodied adult 18-64 with no child under 14 must work or train 80 hours a month, after 3 months of benefits in 36 | P.L. 119-21, FNS memo Oct 3, 2025, 7 USC 2015(o) |
| student | A member 18-49 enrolled at least half-time in college is ineligible unless working 20 hours a week or caring for their own child under 6 | 7 CFR 273.5 |
| immigration | Citizens, green card holders of 5+ years (or with 40 work quarters), Cuban or Haitian entrants, and COFA citizens are eligible | P.L. 119-21, FNS memo Oct 31, 2025 |
| ssn | Every member applying gives a Social Security number or proof of applying | 7 CFR 273.6 |
| ipv | No member serving an intentional program violation disqualification | 7 CFR 273.16 |
| striker | A household with a striking member is eligible only if eligible the day before the strike | 7 CFR 273.1 |
| residency | The household lives in the state where it applies | 7 CFR 273.3 |
| fleeing_felon | No member is a fleeing felon or parole violator | 7 CFR 273.11(n) |
| voluntary_quit | No member quit a job in the past 30 days without good cause | 7 CFR 273.7(j) |

## Simplifications

- Income limits are 1 base amount plus a per-person step, so sizes 3-6 are $1-3 off the official table.
- Net income leaves out the dependent care, medical and child support deductions.
- Categorical eligibility is 1 fact (TANF or SSI). Broad-based categorical eligibility, a state option, is left out.
- The work, student and quit rules apply to "a member" instead of removing that member from the household.

## Why it is a useful real domain

- Facts interact: household size moves both income limits, and the shelter deduction depends on income after other deductions.
- Some rules go against common sense: retirement accounts and the home don't count as resources, and a TANF household skips the income tests.

## Sources

- [USDA SNAP FY2027 cost-of-living adjustments memo (Aug 21, 2026)](https://www.usda.gov/sites/default/files/guidance-documents/fna.snap-cola2027.pdf)
- [7 CFR Part 273](https://www.ecfr.gov/current/title-7/subtitle-B/chapter-II/subchapter-C/part-273)
- [FNS memo on P.L. 119-21 work requirement changes (Oct 3, 2025)](https://www.nawdp.org/wp-content/uploads/2025/10/SNAP-OBBB-Memo-on-Policy-Changes.pdf)
- [FNS memo on P.L. 119-21 non-citizen eligibility (Oct 31, 2025)](https://ljfo.vermont.gov/assets/Meetings/Joint-Fiscal-Committee/2025-11-13/OBBB-Implementation-Memo-Alien-SNAP-Eligibility-Oct31.pdf)
