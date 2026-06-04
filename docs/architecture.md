# AuditTrace Architecture

AuditTrace is a synthetic audit reliability prototype. It is built to show how AI-style audit findings can be versioned, evidence-backed, fail-closed, and measured with evals.

It does not use real PHI, does not provide medical advice, and does not claim HIPAA compliance.

## System Overview

```txt
Synthetic note
  -> question-set version
  -> deterministic checks
  -> mock narrative checks
  -> evidence-span validation
  -> persisted audit findings
  -> eval metrics
  -> Next.js review UI
```

## Backend

The FastAPI backend owns the reliability logic.

- `models.py`: SQLAlchemy tables for providers, synthetic documents, question sets, versions, questions, audit runs, findings, evidence spans, eval cases, eval runs, eval results, provider feedback, and audit logs.
- `seed.py`: resets and seeds the local SQLite database with synthetic documents, versioned question sets, questions, and eval cases.
- `services/deterministic_checks.py`: pure deterministic checks for objective fields like signature, credential, date, service code, required sections, and duration/unit matching.
- `services/llm_auditor.py`: mock structured narrative runner. This deliberately mirrors a future structured LLM interface but does not call an external API.
- `services/evidence_validator.py`: validates direct quote evidence against the source note and drives fail-closed downgrade behavior.
- `services/audit_runner.py`: orchestrates audits, persists findings/evidence spans/logs, and writes summary counts.
- `services/eval_runner.py`: runs seeded eval cases through the same audit path and computes metrics.
- `routes/`: JSON APIs for documents, question sets, audits, and evals.

## Frontend

The Next.js frontend is intentionally plain. It exposes the existing backend system without adding a fake clinical product surface.

- `/`: dashboard summary, disclaimer, document/question-set counts, latest eval metrics.
- `/documents`: seeded synthetic notes.
- `/documents/[id]`: document body, question-set version selector, mock audit runner, prior audits.
- `/audits/[id]`: audit detail, source note, summary counts, real audit log timeline, findings, evidence spans, and fail-closed labels.
- `/question-sets`: versioned criteria and question details.
- `/evals`: run eval, latest metrics, failures preview, regression failures.

## Data Flow

1. A seeded synthetic document is selected.
2. A question-set version is selected.
3. Deterministic questions run against metadata and note text.
4. Narrative questions run through the mock structured audit runner.
5. Each required evidence quote is validated against the source note.
6. Findings with invalid or missing required evidence are downgraded to `insufficient_evidence`.
7. Audit runs, findings, evidence spans, and audit logs are persisted.
8. Eval cases run through the same audit path and compare expected outcomes to actual findings.
9. Metrics are persisted and displayed in the UI.

## Local Database

SQLite is used by default for local speed:

```txt
sqlite:///./audittrace.db
```

PostgreSQL can be introduced later through `DATABASE_URL` without changing the core service boundaries.
