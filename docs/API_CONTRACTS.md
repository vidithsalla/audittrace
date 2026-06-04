# API_CONTRACTS.md

## API style

Backend is FastAPI. Use JSON responses. Return predictable typed shapes.

Base URL local:

```txt
http://localhost:8000
```

## Health

### GET /health

Response:

```json
{
  "status": "ok",
  "service": "audittrace-api"
}
```

## Documents

### GET /documents

Query params:
- `specialty` optional
- `provider_id` optional
- `service_code` optional

Response:

```json
{
  "documents": [
    {
      "id": "uuid",
      "title": "ABA 97155 note with missing rationale",
      "provider_id": "uuid",
      "provider_name": "Synthetic Provider 1",
      "specialty": "aba",
      "service_code": "97155",
      "state": "IN",
      "date_of_service": "2026-05-10",
      "note_type": "progress_note"
    }
  ]
}
```

### GET /documents/{document_id}

Response:

```json
{
  "id": "uuid",
  "title": "ABA 97155 note with missing rationale",
  "metadata": {
    "provider_id": "uuid",
    "provider_name": "Synthetic Provider 1",
    "specialty": "aba",
    "service_code": "97155",
    "payer": "Synthetic Medicaid MCO",
    "state": "IN",
    "date_of_service": "2026-05-10",
    "note_type": "progress_note"
  },
  "body": "...synthetic note text..."
}
```

### POST /documents

Optional if time allows. Seeded documents are enough for MVP.

Request:

```json
{
  "title": "Synthetic note",
  "provider_id": "uuid",
  "synthetic_patient_id": "syn_pat_001",
  "specialty": "aba",
  "service_code": "97155",
  "payer": "Synthetic Medicaid MCO",
  "state": "IN",
  "date_of_service": "2026-05-10",
  "note_type": "progress_note",
  "body": "..."
}
```

## Question sets

### GET /question-sets

Response:

```json
{
  "question_sets": [
    {
      "id": "uuid",
      "slug": "aba-97155",
      "name": "ABA 97155 Protocol Modification Audit",
      "specialty": "aba",
      "versions": [
        {
          "id": "uuid",
          "version": "v1",
          "status": "active",
          "change_summary": "Initial synthetic 97155 criteria"
        }
      ]
    }
  ]
}
```

### GET /question-sets/{version_id}

Response:

```json
{
  "id": "uuid",
  "question_set": {
    "id": "uuid",
    "slug": "aba-97155",
    "name": "ABA 97155 Protocol Modification Audit"
  },
  "version": "v1",
  "status": "active",
  "questions": [
    {
      "id": "uuid",
      "question_key": "missing_signature",
      "criterion_text": "The note includes a dated provider signature.",
      "severity": "critical",
      "check_type": "deterministic",
      "requires_evidence": false,
      "deterministic_rule": "missing_signature"
    }
  ]
}
```

## Audits

### POST /audits/run

Request:

```json
{
  "document_id": "uuid",
  "question_set_version_id": "uuid",
  "model_mode": "mock"
}
```

Response:

```json
{
  "audit_run_id": "uuid",
  "status": "completed",
  "summary": {
    "total": 8,
    "pass": 3,
    "fail": 3,
    "needs_review": 1,
    "insufficient_evidence": 1,
    "critical_failures": 2,
    "unsupported_findings": 0
  },
  "latency_ms": 842
}
```

### GET /audits/{audit_run_id}

Response:

```json
{
  "id": "uuid",
  "document": {
    "id": "uuid",
    "title": "ABA 97155 note with missing rationale",
    "body": "..."
  },
  "question_set_version": {
    "id": "uuid",
    "slug": "aba-97155",
    "version": "v1"
  },
  "status": "completed",
  "summary": {},
  "logs": [
    {
      "id": "uuid",
      "actor": "system",
      "action": "audit_started",
      "entity_type": "audit_run",
      "entity_id": "uuid",
      "metadata": {},
      "created_at": "2026-06-04T12:00:00"
    }
  ],
  "findings": [
    {
      "id": "uuid",
      "question_key": "protocol_change_rationale",
      "criterion_text": "The note explains why a protocol modification was clinically necessary.",
      "status": "fail",
      "severity": "critical",
      "reason": "The note states a protocol was adjusted but does not explain why the change was clinically necessary.",
      "resolution": "Add patient-specific rationale tied to observed behavior and treatment goals.",
      "source": "llm",
      "evidence_validated": true,
      "evidence_spans": [
        {
          "quote": "Protocol was adjusted during the session.",
          "start_char": 319,
          "end_char": 360,
          "validation_status": "valid"
        }
      ]
    }
  ]
}
```

## Evals

### POST /evals/run

Request:

```json
{
  "question_set_version_id": "uuid",
  "model_mode": "mock"
}
```

If `question_set_version_id` omitted, run all eval cases.

Response:

```json
{
  "eval_run_id": "uuid",
  "status": "completed",
  "metrics": {
    "case_count": 36,
    "critical_issue_recall": 0.94,
    "false_positive_rate": 0.08,
    "unsupported_finding_rate": 0.0,
    "evidence_span_match_rate": 0.97,
    "insufficient_evidence_rate": 0.06,
    "average_audit_latency_ms": 811,
    "regression_failures": 2
  }
}
```

### GET /evals/latest

Response:

```json
{
  "id": "uuid",
  "status": "completed",
  "started_at": "2026-06-04T12:00:00Z",
  "completed_at": "2026-06-04T12:00:12Z",
  "metrics": {},
  "results": [
    {
      "case_key": "aba_97155_missing_rationale_001",
      "passed": true,
      "errors": []
    }
  ]
}
```

## Providers

### GET /providers/{provider_id}/trends

Response:

```json
{
  "provider": {
    "id": "uuid",
    "name": "Synthetic Provider 1",
    "specialty": "aba"
  },
  "trend": {
    "audit_count": 8,
    "top_failing_criteria": [
      {
        "question_key": "protocol_change_rationale",
        "failure_count": 3
      }
    ],
    "quality_score_series": [
      {"date": "2026-05-01", "score": 0.71},
      {"date": "2026-05-15", "score": 0.83}
    ]
  },
  "feedback_preview": "Your recent notes consistently include service activity but sometimes miss patient-specific rationale..."
}
```

## Error shape

Use standard FastAPI HTTP errors, but include useful messages:

```json
{
  "detail": {
    "code": "QUESTION_SET_NOT_FOUND",
    "message": "Question set version not found"
  }
}
```

## Status codes

- 200 success
- 201 created document/audit/eval if async creation is used
- 400 invalid input
- 404 missing document/question set/audit
- 409 incompatible document/question set specialty
- 500 unexpected server error
