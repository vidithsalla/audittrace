# SEED_DATA_SPEC.md

## Goal

Create synthetic notes and question sets that are realistic enough to test the system but clearly not real PHI or medical advice.

Every synthetic note should contain:

```txt
Synthetic data notice: This note is fictional and contains no real patient information.
```

## Providers

Create 8 synthetic providers:

| external_provider_id | name | specialty | state |
|---|---|---|---|
| prov_aba_001 | Synthetic ABA Provider 1 | aba | IN |
| prov_aba_002 | Synthetic ABA Provider 2 | aba | IN |
| prov_aba_003 | Synthetic ABA Provider 3 | aba | CA |
| prov_hospice_001 | Synthetic Hospice Provider 1 | hospice | TX |
| prov_hospice_002 | Synthetic Hospice Provider 2 | hospice | FL |
| prov_bh_001 | Synthetic Behavioral Health Provider 1 | behavioral_health | NY |
| prov_bh_002 | Synthetic Behavioral Health Provider 2 | behavioral_health | CA |
| prov_bh_003 | Synthetic Behavioral Health Provider 3 | behavioral_health | PA |

## Question sets

### ABA-97155-v1

Questions:

1. `missing_signature` deterministic critical
2. `missing_credential` deterministic critical
3. `duration_unit_mismatch` deterministic critical
4. `protocol_change_rationale` llm critical
5. `treatment_plan_linkage` llm warning
6. `individualized_observation` llm warning

### ABA-97155-v2

Same as v1 but stricter:

- `protocol_change_rationale` must include why the protocol changed and what observed behavior triggered it.
- `individualized_observation` must include patient-specific response, not generic participation.

### ABA-97156-v1

Questions:

1. `missing_signature` deterministic critical
2. `caregiver_present` deterministic warning
3. `caregiver_training_content` llm critical
4. `caregiver_skill_uptake` llm warning
5. `treatment_plan_linkage` llm warning

### Hospice-Eligibility-v1

Questions:

1. `missing_signature` deterministic critical
2. `face_to_face_documented` deterministic warning
3. `terminal_prognosis_support` llm critical
4. `patient_specific_decline` llm critical
5. `plan_of_care_alignment` llm warning
6. `copy_forward_risk` llm warning

### BehavioralHealth-MedNec-v1

Questions:

1. `missing_signature` deterministic critical
2. `medical_necessity_support` llm critical
3. `session_focus_matches_plan` llm warning
4. `risk_or_symptom_update` llm warning

## Synthetic note categories

Create 30-50 notes.

Minimum distribution:

| Category | Count |
|---|---:|
| ABA 97155 clean pass | 4 |
| ABA 97155 missing rationale | 5 |
| ABA 97155 duration mismatch | 4 |
| ABA 97155 v1 pass but v2 fail | 4 |
| ABA 97156 caregiver training missing uptake | 5 |
| Hospice vague prognosis | 5 |
| Hospice plan-of-care mismatch | 4 |
| Behavioral health weak medical necessity | 4 |
| Adversarial invalid evidence | 3 |

## Example synthetic note template: ABA 97155 missing rationale

```txt
Synthetic data notice: This note is fictional and contains no real patient information.

Service Code: 97155
Date of Service: 2026-05-10
Provider: Synthetic ABA Provider 1, BCBA
Client: SYN-ABA-001
Duration: 60 minutes
Billed Units: 4

Session Summary:
The provider observed the technician implementing the current behavior reduction protocol during table work and transition activities.

Intervention:
Protocol was adjusted during the session. The technician was instructed to use a shorter prompt delay and provide reinforcement after two consecutive correct responses.

Response:
The client completed several transition tasks with fewer prompts by the end of session.

Plan:
Continue monitoring protocol response during the next session.

Provider Signature: Synthetic ABA Provider 1, BCBA
```

Expected:
- protocol_change_rationale fails because note says protocol changed but does not explain why clinically necessary.

## Example synthetic note template: ABA 97155 clean pass

```txt
Synthetic data notice: This note is fictional and contains no real patient information.

Service Code: 97155
Date of Service: 2026-05-11
Provider: Synthetic ABA Provider 2, BCBA
Client: SYN-ABA-002
Duration: 45 minutes
Billed Units: 3

Session Summary:
The provider observed increased refusal behavior during transition from preferred to non-preferred tasks compared with the prior two sessions.

Intervention:
The transition protocol was modified because the prior prompt delay led to escalation and task refusal. The provider shortened the initial demand interval and added a visual countdown before the transition.

Response:
After the modification, the client completed two transitions with one verbal prompt and no escalation.

Plan:
Review transition data next session and continue the modified protocol if refusal remains below baseline.

Provider Signature: Synthetic ABA Provider 2, BCBA
```

Expected:
- pass for rationale and individualized observation.

## Example synthetic note template: hospice vague prognosis

```txt
Synthetic data notice: This note is fictional and contains no real patient information.

Note Type: Hospice Eligibility Review
Date of Service: 2026-05-12
Provider: Synthetic Hospice Provider 1, RN
Patient: SYN-HOSP-001

Summary:
Patient remains appropriate for hospice services. Patient is weak and needs support with daily activities.

Nursing Visit:
Patient was resting in bed. Family reports patient is tired. No new measurements were documented.

Plan of Care:
Continue current plan.

Electronically signed by Synthetic Hospice Provider 1, RN
```

Expected:
- fail patient_specific_decline
- fail terminal_prognosis_support or needs_review depending question wording

## Example adversarial invalid evidence case

Create one note where mock model returns a quote not present in text.

Expected:
- finding should be downgraded to insufficient_evidence.

## Seed script requirements

Seed script should:

1. Clear existing rows.
2. Insert providers.
3. Insert question sets/versions/questions.
4. Insert documents.
5. Insert eval cases.
6. Print counts.

Example output:

```txt
Seeded 8 providers
Seeded 5 question set versions
Seeded 34 questions
Seeded 42 synthetic documents
Seeded 42 eval cases
```
