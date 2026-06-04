# CODEX_BUILD_GUIDE.md

## Build principle

Build the system logic first, then the UI. Do not build a pretty shell around mocked behavior.

The core proof is:

```txt
versioned question sets + evidence-backed findings + fail-closed validation + eval dashboard
```

## Target stack

- Frontend: Next.js 15, TypeScript, Tailwind
- Backend: FastAPI, Python 3.12, Pydantic
- Database: PostgreSQL preferred, SQLite acceptable fallback for local speed
- ORM: SQLAlchemy 2.0
- Tests: pytest for backend, TypeScript typecheck for frontend
- LLM: OpenAI structured outputs or provider abstraction with mock fallback

## Repo structure

Recommended monorepo:

```txt
audittrace/
  apps/
    api/
      audittrace_api/
        main.py
        db.py
        models.py
        schemas.py
        seed.py
        services/
          deterministic_checks.py
          llm_auditor.py
          evidence_validator.py
          audit_runner.py
          eval_runner.py
          feedback.py
        routes/
          documents.py
          question_sets.py
          audits.py
          evals.py
          providers.py
        tests/
    web/
      app/
        dashboard/page.tsx
        documents/page.tsx
        audits/[id]/page.tsx
        question-sets/page.tsx
        evals/page.tsx
        providers/[id]/page.tsx
      components/
      lib/api.ts
  docs/
  seed_data/
  README.md
```

## Implementation phases

### Phase 0: Project bootstrap

Create monorepo structure.

Backend:
- FastAPI app
- health endpoint
- SQLAlchemy DB connection
- pytest setup

Frontend:
- Next.js app
- Tailwind
- API client helper
- basic layout/nav

Done when:
- `GET /health` returns OK
- backend tests run
- frontend typecheck passes

### Phase 1: Schema and seed data

Implement tables from `DATA_SCHEMA.md`.

Seed:
- 30-50 synthetic notes
- 3 question sets
- 2 versions of at least one question set
- providers
- eval cases with expected findings

Done when:
- seed script resets local DB
- `/documents` lists seeded notes
- `/question-sets` lists question sets and versions

### Phase 2: Deterministic checks

Implement objective checks:
- missing signature
- missing credential
- missing date of service
- missing service code
- duration/unit mismatch
- missing required section

Done when:
- deterministic checks produce structured findings
- pytest covers passing and failing cases

### Phase 3: LLM audit runner

Implement provider abstraction:

```python
class ModelClient:
    def audit_question(note_text: str, question: Question) -> LlmFinding: ...
```

Include two modes:
- `mock`: deterministic local outputs for tests/demo
- `openai`: optional, only if `OPENAI_API_KEY` is set

LLM output must be structured with Pydantic.

Done when:
- audit runner can process LLM questions
- mock mode works without API keys
- no raw free-form model output is trusted directly

### Phase 4: Evidence-span validation

Implement quote validation:
- each finding has zero or more evidence spans
- each span quote must exist in the source note, normalized for whitespace/case
- invalid evidence causes finding downgrade to `insufficient_evidence`
- unsupported finding rate is recorded

Done when:
- invalid quote is rejected in tests
- audit UI can show validated and rejected evidence

### Phase 5: Audit runner and persistence

Create `POST /audits/run`.

Flow:
1. Load document.
2. Load selected question-set version.
3. Run deterministic checks.
4. Run LLM checks.
5. Validate evidence.
6. Persist audit run, findings, evidence spans, audit logs.
7. Return audit ID and summary.

Done when:
- audits are persisted
- audit detail endpoint returns complete findings
- audit logs are created

### Phase 6: Eval harness

Implement `POST /evals/run`.

Eval cases compare expected labels to actual findings.

Metrics:
- critical_issue_recall
- false_positive_rate
- unsupported_finding_rate
- evidence_span_match_rate
- insufficient_evidence_rate
- regression_failures_by_question_set_version
- average_audit_latency_ms

Done when:
- evals run on seeded cases
- results persist
- metrics visible through API

### Phase 7: UI

Build only useful screens:

- `/dashboard`: high-level summary
- `/documents`: seeded notes list
- `/audits/[id]`: note, findings, evidence spans, validation state
- `/question-sets`: versions and criteria
- `/evals`: metrics and failed cases

Done when:
- reviewer can complete 90-second demo without reading code

### Phase 8: Provider feedback mini-view

Add lightweight provider trends:
- failing criteria by provider
- generated feedback draft
- before/after synthetic score trend

Keep this secondary.

### Phase 9: Public packaging

Add:
- README
- screenshots
- demo script
- limitations
- architecture diagram text/mermaid
- final verification commands

Done when:
- `make verify` or equivalent runs tests/typecheck/build
- README explains what is real vs simplified

## Hard guardrails

1. Never use real PHI.
2. Never claim medical correctness.
3. Never claim HIPAA compliance.
4. Do not clone Brellium UI.
5. Do not make broad healthcare claims.
6. Do not hide logic behind a model call.
7. Do not trust LLM evidence without validation.
8. Do not cut evals.
9. Do not cut question-set versioning.
10. Do not cut README tradeoffs.

## Environment variables

```txt
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/audittrace
MODEL_MODE=mock
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
CORS_ORIGINS=http://localhost:3000
```

## Verification commands

Backend:

```bash
cd apps/api
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
uvicorn audittrace_api.main:app --reload
```

Frontend:

```bash
cd apps/web
npm install
npm run typecheck
npm run build
npm run dev
```

Full verification goal:

```bash
pytest
npm run typecheck
npm run build
```
