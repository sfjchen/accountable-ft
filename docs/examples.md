# Three real prompts and Qwen3.5-9B base answers

From `runs/qwen9b-lite.jsonl` (commit c479313, primary slice, prose view, temperature 0). Gold from `data/v1.jsonl`. The system line on every call: "You decide cases under a written policy. Apply only the numbered rules of the policy, not outside knowledge or common practice. Reply in exactly the requested format with no other text."

## grant-p010-c01-reveal:prose  (gold: approve, Qwen: deny)

Qwen cites R5 and R6. R5 is waived (community laboratory, request at the $120,000 exception limit). R6 holds (Feb 1 is after Jan 14). It missed the exception and misread a date comparison.

### Prompt

```
Policy:
Ostrava-Lune Foundation, Halbrecht Early Inquiry Grants: eligibility rules (2027 cycle)
An application is approved only if it meets every rule below. Rules marked as defaults say what to assume when an application is silent on a point.

R1. Requests above $50,000 must include a letter of support from the host.
R2. The lead applicant must have received a doctorate no more than 6 years before 2027, unless the applicant has a documented Corran career break and the doctorate is at most 10 years old.
R3. Every proposal must include an open data plan. This rule does not apply if the host is a teaching hospital bound by patient privacy rules.
R4. Applications hosted by a teaching hospital may budget at most $10,000 for travel.
R5. The total requested amount may not exceed $90,000. This rule does not apply if the host is a community laboratory and the request is at most $120,000.
R6. No project may begin before January 14, 2027.
R7. The host institution must be a university, a teaching hospital or a community laboratory.
R8. If an application does not mention a career break, assume the applicant took none.
R9. The project period, from start date to end date, may not exceed 39 weeks.
R10. Research with human participants requires approval from the Mereth ethics board.

Case file:
Ostrava-Lune Foundation file reference HEI-8086 contains materials submitted by Dr. Teodor Quayle. One of the academic referees provided in the dossier has recently relocated to a different metropolitan area. Project activities are formally slated to commence on February 1, 2027. The financial breakdown allocates $20,000 specifically for travel expenses. The proposed timeline spans a total duration of 30 weeks. The principal investigator was awarded their doctoral degree 9 years ago. Initial findings were shared by the investigator during a regional workshop held last spring. Combined expenditures for equipment and travel total $30,000. A verified Corran career break is documented, and the corresponding form is filed in the records. The research focus centers on the formation and evolution of seasonal salt crusts across the Vessel Bay flats. The dossier features an official letter of support signed by the host institution's research office. An allotment of $10,000 is designated for necessary equipment acquisitions. Administrators at the host grants office recommended a more concise title prior to submission. No clearance has been issued by the Mereth ethics board. The administering organization is structured as a community laboratory. An attached data management strategy outlines the team's commitment to public release. Fieldwork involves exclusively soil and water samples, entirely omitting human subjects. Operations are projected to conclude on August 30, 2027. The primary funding request submitted to the foundation amounts to 120 thousand dollars.

Reply in exactly these 4 lines, in this order:
Decision: approve | deny | cannot determine
Policy support: <fact>=<value> (R<n>); <fact>=<value> (R<n>); ...
Assumptions: <fact>=<value> (default from R<n>) | none
Smallest change that would reverse this decision: <fact> -> <value>; <fact> -> <value> | no change within 4 edits

The decision is cannot determine when the case file leaves out a fact the outcome turns on and no default in the policy covers it. "Policy support" lists the fewest facts from the case file that by themselves force your decision, each with the rule it triggers: for approve, the facts each rule needs to be met or waived; for deny, the facts of one rule the case fails; for cannot determine, the missing facts as <fact>=not stated. "Assumptions" lists any fact the case file does not state that you filled in from a default in the policy. The last line gives the fewest fact edits that would reverse your decision (approve to deny, deny to approve); for cannot determine it gives instead the fewest facts the case file leaves out, with values, whose addition would settle the decision. All edits on that line are applied together, so list one set of edits, not alternatives. Name every fact by exactly one of these labels: years since the lead applicant's doctorate (counted to 2027); documented Corran career break; type of host institution; total requested amount (dollars); equipment budget (dollars); travel budget (dollars); project start date; project end date; letter of support from the host; open data plan included; research involves human participants; ethics approval from the Mereth board; project length in weeks; equipment plus travel budget (dollars). Give each value as the case file states it (yes or no for yes/no facts).
```

### Qwen output

```
Decision: deny
Policy support: total requested amount (dollars)=120000 (R5); project start date=February 1, 2027 (R6)
Assumptions: none
Smallest change that would reverse this decision: total requested amount (dollars) -> 120000; project start date -> January 14, 2027
```

### Gold

- decision: approve
- rule trace: {'R1': 'pass', 'R2': 'waived', 'R3': 'pass', 'R4': 'pass', 'R5': 'waived', 'R6': 'pass', 'R7': 'pass', 'R9': 'pass', 'R10': 'pass'}
- minimum sufficient facts: ['pi_years_since_phd', 'career_break', 'institution_type', 'requested_amount', 'start_day', 'end_day', 'letter_of_support', 'open_data_plan', 'human_subjects']
- defaults applied: {}
- smallest flip: {'pi_years_since_phd': 11} (target deny)

## grant-p000-c02-miss:prose  (gold: cannot determine, Qwen: deny)

The decisive fact is not stated and no default covers it, so the gold is cannot determine. Qwen filled the gap with an assumption and denied.

### Prompt

```
Policy:
Ostrava-Lune Foundation, Halbrecht Early Inquiry Grants: eligibility rules (2027 cycle)
An application is approved only if it meets every rule below. Rules marked as defaults say what to assume when an application is silent on a point.

R1. The project period, from start date to end date, may not exceed 39 weeks.
R2. Applications hosted by a teaching hospital may budget at most $5,000 for travel.
R3. The lead applicant must have received a doctorate no more than 6 years before 2027. This rule does not apply if the applicant has a documented Corran career break and the doctorate is at most 10 years old.
R4. The application must include a letter of support from the host. This rule does not apply if the host is a university, whose standing agreement with the foundation replaces the letter.
R5. If the type of host institution is not stated, treat the host as an independent institute.
R6. Research with human participants requires approval from the Mereth ethics board.
R7. If ethics approval is not mentioned, assume none was obtained.
R8. Equipment and travel together may not exceed $30,000.
R9. The host institution must be a university, a teaching hospital or a community laboratory.

Case file:
Dr. Ilse Varnholt submitted application HEI-2079 to the Ostrava-Lune Foundation for the current cycle. The ledger allocates exactly $10,000 for acquiring necessary equipment. The financial summary requests a total disbursement of $60,000 from the foundation. A graduate student drafted several sections of the project narrative. The submission package lacks an endorsement letter from the host institution. The accompanying budget justification employs a remarkably casual writing style. Transportation and related transit expenses are set at $5,000. No paperwork has been submitted to the Mereth ethics board by the applicant. An academic institution located in the Vessel Bay region is named as the host. The principal investigator was awarded their doctoral degree 3 years ago. Combined expenditures for apparatus and transit total $15,000. A submitted Corran career break form records a period of absence from active research. Project activities are planned to commence on February 15, 2027. The introductory letter expresses gratitude to two former mentors by name. An appended document pledges that the research team will make all collected data publicly accessible. Operations are projected to conclude on August 30, 2027. The proposed timeline spans a duration of 28 weeks.

Reply in exactly these 4 lines, in this order:
Decision: approve | deny | cannot determine
Policy support: <fact>=<value> (R<n>); <fact>=<value> (R<n>); ...
Assumptions: <fact>=<value> (default from R<n>) | none
Smallest change that would reverse this decision: <fact> -> <value>; <fact> -> <value> | no change within 4 edits

The decision is cannot determine when the case file leaves out a fact the outcome turns on and no default in the policy covers it. "Policy support" lists the fewest facts from the case file that by themselves force your decision, each with the rule it triggers: for approve, the facts each rule needs to be met or waived; for deny, the facts of one rule the case fails; for cannot determine, the missing facts as <fact>=not stated. "Assumptions" lists any fact the case file does not state that you filled in from a default in the policy. The last line gives the fewest fact edits that would reverse your decision (approve to deny, deny to approve); for cannot determine it gives instead the fewest facts the case file leaves out, with values, whose addition would settle the decision. All edits on that line are applied together, so list one set of edits, not alternatives. Name every fact by exactly one of these labels: years since the lead applicant's doctorate (counted to 2027); documented Corran career break; type of host institution; total requested amount (dollars); equipment budget (dollars); travel budget (dollars); project start date; project end date; letter of support from the host; open data plan included; research involves human participants; ethics approval from the Mereth board; project length in weeks; equipment plus travel budget (dollars). Give each value as the case file states it (yes or no for yes/no facts).
```

### Qwen output

```
Decision: deny
Policy support: letter of support from the host=no (R4)
Assumptions: none
Smallest change that would reverse this decision: letter of support from the host -> yes
```

### Gold

- decision: cannot determine
- rule trace: {'R1': 'pass', 'R2': 'pass', 'R3': 'pass', 'R4': 'waived', 'R6': 'unknown', 'R8': 'pass', 'R9': 'pass'}
- minimum sufficient facts: []
- defaults applied: {}
- smallest flip: None (target None)

## grant-p000-c02-flip:prose  (gold: deny, Qwen: deny)

Correct decision. Compare its Policy support line with the gold minimum set: the engine checks whether the cited facts alone force the decision.

### Prompt

```
Policy:
Ostrava-Lune Foundation, Halbrecht Early Inquiry Grants: eligibility rules (2027 cycle)
An application is approved only if it meets every rule below. Rules marked as defaults say what to assume when an application is silent on a point.

R1. The project period, from start date to end date, may not exceed 39 weeks.
R2. Applications hosted by a teaching hospital may budget at most $5,000 for travel.
R3. The lead applicant must have received a doctorate no more than 6 years before 2027. This rule does not apply if the applicant has a documented Corran career break and the doctorate is at most 10 years old.
R4. The application must include a letter of support from the host. This rule does not apply if the host is a university, whose standing agreement with the foundation replaces the letter.
R5. If the type of host institution is not stated, treat the host as an independent institute.
R6. Research with human participants requires approval from the Mereth ethics board.
R7. If ethics approval is not mentioned, assume none was obtained.
R8. Equipment and travel together may not exceed $30,000.
R9. The host institution must be a university, a teaching hospital or a community laboratory.

Case file:
Dr. Ilse Varnholt submitted application HEI-2079 to the Ostrava-Lune Foundation for the current cycle. The ledger allocates exactly $10,000 for acquiring necessary equipment. The financial summary requests a total disbursement of $60,000 from the foundation. A graduate student drafted several sections of the project narrative. The submission package lacks an endorsement letter from the host institution. The accompanying budget justification employs a remarkably casual writing style. Transportation and related transit expenses are set at $5,000. No paperwork has been submitted to the Mereth ethics board by the applicant. An independent institute located in the Vessel Bay region is named as the host. The principal investigator was awarded their doctoral degree 3 years ago. Combined expenditures for apparatus and transit total $15,000. A submitted Corran career break form records a period of absence from active research. The research design excludes any involvement of human participants. Project activities are planned to commence on February 15, 2027. The introductory letter expresses gratitude to two former mentors by name. An appended document pledges that the research team will make all collected data publicly accessible. Operations are projected to conclude on August 30, 2027. The proposed timeline spans a duration of 28 weeks.

Reply in exactly these 4 lines, in this order:
Decision: approve | deny | cannot determine
Policy support: <fact>=<value> (R<n>); <fact>=<value> (R<n>); ...
Assumptions: <fact>=<value> (default from R<n>) | none
Smallest change that would reverse this decision: <fact> -> <value>; <fact> -> <value> | no change within 4 edits

The decision is cannot determine when the case file leaves out a fact the outcome turns on and no default in the policy covers it. "Policy support" lists the fewest facts from the case file that by themselves force your decision, each with the rule it triggers: for approve, the facts each rule needs to be met or waived; for deny, the facts of one rule the case fails; for cannot determine, the missing facts as <fact>=not stated. "Assumptions" lists any fact the case file does not state that you filled in from a default in the policy. The last line gives the fewest fact edits that would reverse your decision (approve to deny, deny to approve); for cannot determine it gives instead the fewest facts the case file leaves out, with values, whose addition would settle the decision. All edits on that line are applied together, so list one set of edits, not alternatives. Name every fact by exactly one of these labels: years since the lead applicant's doctorate (counted to 2027); documented Corran career break; type of host institution; total requested amount (dollars); equipment budget (dollars); travel budget (dollars); project start date; project end date; letter of support from the host; open data plan included; research involves human participants; ethics approval from the Mereth board; project length in weeks; equipment plus travel budget (dollars). Give each value as the case file states it (yes or no for yes/no facts).
```

### Qwen output

```
Decision: deny
Policy support: type of host institution=independent institute (R9)
Assumptions: none
Smallest change that would reverse this decision: type of host institution -> university; type of host institution -> teaching hospital; type of host institution -> community laboratory
```

### Gold

- decision: deny
- rule trace: {'R1': 'pass', 'R2': 'pass', 'R3': 'pass', 'R4': 'fail', 'R6': 'pass', 'R8': 'pass', 'R9': 'fail'}
- minimum sufficient facts: ['institution_type']
- defaults applied: {}
- smallest flip: {'institution_type': 'university'} (target approve)
