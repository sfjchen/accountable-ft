# Source policy: Medicaid adult group eligibility, coverage year 2027

Built from the federal rules for the Medicaid adult group (MAGI adults aged 19-64) in an expansion state, 48 states and DC. "Approve" means eligible for coverage under the adult group. This is a simplified policy built from real rules, not the full program.

## Rules and where they come from

| Rule key | Rule | Source |
|---|---|---|
| age_range | At least 19 and under 65 | 42 CFR 435.119(b)(1) |
| magi_limit | Monthly MAGI at most 138% of the poverty line: $1,835.40 for 1 person plus $653.20 per extra member (2026 HHS guideline $15,960 plus $5,680 per person, 133% plus the 5% disregard) | 42 CFR 435.119(c), 435.603; 2026 HHS poverty guidelines |
| residency | Lives in the state where the application is filed | 42 CFR 435.403 |
| qualified_status | Citizen or national, green card holder, Cuban or Haitian entrant, or COFA citizen. Refugees, asylees and temporary visa holders lose full federal funding Oct 1, 2026 | SSA 1903(v)(5) as amended by P.L. 119-21 sec. 71109; SHO #26-001 |
| five_year_bar | A green card holder needs 5 years, unless an exception applies (40 work quarters, military service or family, refugee or asylee origin) | 8 USC 1612(b), 1613; SHO #26-001 |
| status_verification | Status must be verified, except during the 90-day reasonable opportunity period | 42 CFR 435.406, 435.956(b) |
| ssn | Give a Social Security number or proof of applying | 42 CFR 435.910 |
| medicare | Not entitled to or enrolled in Medicare Part A or B | 42 CFR 435.119(b)(3) |
| other_group | Not eligible for and enrolled in another mandatory group | 42 CFR 435.119(b)(4) |
| not_pregnant | Not pregnant | 42 CFR 435.119(b)(2) |
| inmate | Not an inmate of a public institution, except for inpatient care in a medical institution | 42 CFR 435.1009, 435.1010 |
| community_engagement | In a state applying the rule, 80 hours a month of work, community service, a work program or half-time school, or monthly income of at least the federal minimum wage times 80 hours ($580). Exempt: medically frail, postpartum, American Indian or Alaska Native, veteran with a total disability rating, former foster youth under 26, SNAP or TANF work compliance, substance use treatment, parent, guardian or caretaker of a dependent child 13 or under | SSA 1902(xx) as added by P.L. 119-21 sec. 71119; 42 CFR 435.551-435.560 (CMS-2454-IFC) |

The community engagement requirement must start by Jan 1, 2027. A state with a CMS good faith effort exemption (expires no later than Dec 31, 2028) does not apply it, which the fact `state_ce_active` captures.

## Simplifications

- Income limit is 138% of the 2026 guideline for the 48 states and DC, written in tenths of dollars so it is exact to the cent. Alaska and Hawaii differ.
- MAGI is current monthly earned plus unearned income. Tax deductions, tax household rules, lump sums and self-employment rules are left out.
- The $580 income route uses the household's earned income.
- Immigration is 1 status fact plus 1 bar-exception fact. The state option to cover LPRs without the bar, state-funded coverage, emergency Medicaid and the children and pregnant women option are left out.
- Pregnancy is a bar to the adult group (435.119(b)(2)). Only postpartum is modeled as a community engagement exemption.
- Exemption groups are 1 enum plus 1 child fact. Family caregivers of disabled individuals, 1115 demonstration populations, the optional short-term hardship exceptions, the seasonal-worker income average and the 30-day noncompliance notice are left out.
- The 80 hours are 1 monthly count in the verified month. The look-back length (1 month for applicants, state choice for enrollees) is left out. Half-time school counts as 80.
- The medically frail exemption keeps the IFR's reading that the condition must significantly impair the ability to meet the requirement, as 1 enum value.
- Inmate status has 1 inpatient exception.
- Ints are bucketed to at most 8 values like every other domain.

## Why it is a useful real domain

- Facts interact: household size moves the income limit, and 1 exemption or the income route can replace the 80 hours.
- Some rules go against common sense: a child aged 13 exempts the parent but a child aged 14 does not, and a refugee fails while a green card holder with under 5 years can pass through an exception.

## Sources

- [2026 HHS poverty guidelines, Federal Register (Jan 15, 2026)](https://www.federalregister.gov/documents/2026/01/15/2026-00755/annual-update-of-the-hhs-poverty-guidelines) and [ASPE detailed guidelines 2026](https://aspe.hhs.gov/sites/default/files/documents/b1bfa16b20ae9b89d525bc35de7c1643/detailed-guidelines-2026.pdf)
- [CMS interim final rule, Community Engagement Requirement for Certain Individuals, 91 FR 33348 (June 3, 2026)](https://www.govinfo.gov/content/pkg/FR-2026-06-03/html/2026-11094.htm) and [CMS fact sheet](https://www.cms.gov/newsroom/fact-sheets/medicaid-community-engagement-requirement-certain-individuals-interim-final-rule-comment-period-cms)
- [CMS State Health Official letter #26-001 on section 71109 (alien Medicaid eligibility)](https://www.medicaid.gov/federal-policy-guidance/downloads/sho26001.pdf)
- [42 CFR Part 435, Subpart B (435.119) and Subpart E (435.403, 435.406, 435.603, 435.910, 435.956)](https://www.ecfr.gov/current/title-42/chapter-IV/subchapter-C/part-435)
- [Social Security Act 1902(xx) (42 USC 1396a(xx)) and 1903(v)(5)](https://uscode.house.gov/view.xhtml?req=granuleid:USC-prelim-title42-section1396a&num=0&edition=prelim)
