# DATA_SCHEMA.md

## Overview

AuditTrace stores synthetic documents, versioned question sets, audit runs, findings, evidence spans, eval cases, eval results, provider feedback, and audit logs.

Use Postgres if possible. SQLite fallback is acceptable only if it does not compromise demo speed.

## Entity relationships

```txt
Provider 1--N SyntheticDocument
SyntheticDocument 1--N DocumentChunk
QuestionSet 1--N QuestionSetVersion
QuestionSetVersion 1--N Question
SyntheticDocument 1--N AuditRun
QuestionSetVersion 1--N AuditRun
AuditRun 1--N AuditFinding
AuditFinding 1--N EvidenceSpan
EvalCase N--1 SyntheticDocument
EvalRun 1--N EvalResult
Provider 1--N ProviderFeedback
AuditLog belongs to many entity types through entity_type/entity_id
```

## Tables

### providers

Stores synthetic provider profiles.

| Field | Type | Notes |
|---|---|---|
| id | uuid pk | |
| external_provider_id | text unique | e.g. `prov_aba_001` |
| name | text | synthetic |
| specialty | text | `aba`, `hospice`, `behavioral_health` |
| state | text | e.g. `IN`, `CA` |
| created_at | timestamp | |

### synthetic_documents

Stores synthetic notes and metadata.

| Field | Type | Notes |
|---|---|---|
| id | uuid pk | |
| provider_id | uuid fk providers.id | |
| synthetic_patient_id | text | never real patient data |
| title | text | |
| specialty | text | |
| service_code | text nullable | e.g. `97155`, `97156` |
| payer | text nullable | synthetic payer name |
| state | text | |
| date_of_service | date nullable | |
| note_type | text | progress_note, cti, poc, nursing_note |
| body | text | full synthetic note text |
| source_kind | text | `seeded`, `uploaded` |
| created_at | timestamp | |

Indexes:
- provider_id
- specialty
- service_code
- date_of_service

### document_chunks

Optional but useful for evidence and future retrieval.

| Field | Type | Notes |
|---|---|---|
| id | uuid pk | |
| document_id | uuid fk synthetic_documents.id | |
| chunk_index | int | |
| start_char | int | |
| end_char | int | |
| text | text | |
| created_at | timestamp | |

Unique:
- document_id + chunk_index

### question_sets

Logical grouping of audit criteria.

| Field | Type | Notes |
|---|---|---|
| id | uuid pk | |
| slug | text unique | `aba-97155`, `hospice-eligibility` |
| name | text | |
| specialty | text | |
| description | text | |
| created_at | timestamp | |

### question_set_versions

Versioned release of a question set.

| Field | Type | Notes |
|---|---|---|
| id | uuid pk | |
| question_set_id | uuid fk question_sets.id | |
| version | text | `v1`, `v2` |
| status | text | draft, active, archived |
| change_summary | text nullable | |
| active_from | date nullable | |
| active_to | date nullable | |
| created_at | timestamp | |

Unique:
- question_set_id + version

### questions

Individual audit criteria.

| Field | Type | Notes |
|---|---|---|
| id | uuid pk | |
| version_id | uuid fk question_set_versions.id | |
| question_key | text | stable key across versions |
| criterion_text | text | |
| severity | text | critical, warning, info |
| check_type | text | deterministic, llm |
| requires_evidence | boolean | default true |
| expected_answer_type | text | pass_fail, classification, numeric, text |
| deterministic_rule | text nullable | e.g. `missing_signature` |
| prompt_hint | text nullable | for LLM checks |
| created_at | timestamp | |

Indexes:
- version_id
- question_key
- severity
- check_type

### audit_runs

One audit execution against one document and one question-set version.

| Field | Type | Notes |
|---|---|---|
| id | uuid pk | |
| document_id | uuid fk synthetic_documents.id | |
| question_set_version_id | uuid fk question_set_versions.id | |
| status | text | pending, running, completed, failed |
| model_mode | text | mock, openai |
| started_at | timestamp | |
| completed_at | timestamp nullable | |
| latency_ms | int nullable | |
| summary | jsonb | counts by status/severity |
| created_at | timestamp | |

Indexes:
- document_id
- question_set_version_id
- created_at

### audit_findings

Structured result for each question.

| Field | Type | Notes |
|---|---|---|
| id | uuid pk | |
| audit_run_id | uuid fk audit_runs.id | |
| question_id | uuid fk questions.id | |
| status | text | pass, fail, needs_review, insufficient_evidence |
| severity | text | critical, warning, info |
| reason | text | concise explanation |
| resolution | text nullable | suggested fix |
| confidence | float nullable | 0-1 |
| source | text | deterministic, llm, validator |
| evidence_validated | boolean | |
| validation_notes | text nullable | |
| created_at | timestamp | |

Indexes:
- audit_run_id
- status
- severity
- evidence_validated

### evidence_spans

Source-backed evidence for findings.

| Field | Type | Notes |
|---|---|---|
| id | uuid pk | |
| finding_id | uuid fk audit_findings.id | |
| document_id | uuid fk synthetic_documents.id | |
| quote | text | quoted source text |
| start_char | int nullable | found position |
| end_char | int nullable | found position |
| validation_status | text | valid, invalid, not_required |
| created_at | timestamp | |

Indexes:
- finding_id
- document_id
- validation_status

### eval_cases

Synthetic labeled test case.

| Field | Type | Notes |
|---|---|---|
| id | uuid pk | |
| case_key | text unique | |
| document_id | uuid fk synthetic_documents.id | |
| question_set_version_id | uuid fk question_set_versions.id | |
| expected_findings | jsonb | list of expected question_key/status/severity |
| tags | jsonb | e.g. specialty, failure types |
| created_at | timestamp | |

### eval_runs

One full eval execution.

| Field | Type | Notes |
|---|---|---|
| id | uuid pk | |
| question_set_version_id | uuid fk question_set_versions.id nullable | can run all |
| status | text | running, completed, failed |
| started_at | timestamp | |
| completed_at | timestamp nullable | |
| metrics | jsonb | aggregate metrics |
| created_at | timestamp | |

### eval_results

Per-case eval result.

| Field | Type | Notes |
|---|---|---|
| id | uuid pk | |
| eval_run_id | uuid fk eval_runs.id | |
| eval_case_id | uuid fk eval_cases.id | |
| audit_run_id | uuid fk audit_runs.id nullable | |
| passed | boolean | |
| expected | jsonb | |
| actual | jsonb | |
| errors | jsonb | mismatch details |
| latency_ms | int nullable | |
| created_at | timestamp | |

### provider_feedback

Lightweight generated feedback artifact.

| Field | Type | Notes |
|---|---|---|
| id | uuid pk | |
| provider_id | uuid fk providers.id | |
| audit_run_id | uuid fk audit_runs.id nullable | |
| feedback_text | text | generated or templated |
| issue_summary | jsonb | |
| created_at | timestamp | |

### audit_logs

Append-only log for important operations.

| Field | Type | Notes |
|---|---|---|
| id | uuid pk | |
| actor | text | `system`, `demo_user` |
| action | text | e.g. `audit.run`, `finding.downgraded` |
| entity_type | text | document, audit_run, finding, eval_run |
| entity_id | uuid nullable | |
| metadata | jsonb | |
| created_at | timestamp | |

## Enums

Use DB enums or string constants.

```txt
AuditStatus = pending | running | completed | failed
FindingStatus = pass | fail | needs_review | insufficient_evidence
Severity = critical | warning | info
CheckType = deterministic | llm
EvidenceValidationStatus = valid | invalid | not_required
QuestionSetStatus = draft | active | archived
ModelMode = mock | openai
```

## Migration guidance

For speed, create SQLAlchemy models and generate tables with `metadata.create_all()` for local demo. If time allows, add Alembic.

Do not spend time building complex migration workflows unless the MVP is complete.
