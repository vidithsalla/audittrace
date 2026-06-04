# CODEX_PHASE_PROMPTS.md

Use these prompts one at a time in Codex. Do not ask Codex to build everything in one pass.

## Phase 0 prompt

Read `PRD.md`, `CODEX_BUILD_GUIDE.md`, and `DATA_SCHEMA.md`. Create the initial monorepo structure for AuditTrace with `apps/api` FastAPI backend and `apps/web` Next.js frontend. Implement only bootstrap: health endpoint, DB connection placeholder, pytest setup, frontend layout/nav, and API client helper. Do not implement audit logic yet. After implementation, list commands to run tests/typecheck.

## Phase 1 prompt

Implement the database models from `DATA_SCHEMA.md` using SQLAlchemy 2.0 in the FastAPI app. Add a seed script that clears and inserts providers, synthetic documents, question sets, question-set versions, questions, and eval cases based on `SEED_DATA_SPEC.md`. Add API endpoints for listing documents and question sets. Add tests for seed counts and list endpoints.

## Phase 2 prompt

Implement deterministic audit checks in `services/deterministic_checks.py`: missing_signature, missing_credential, missing_date_of_service, missing_service_code, duration_unit_mismatch, and missing_required_section. Return typed findings using Pydantic schemas. Add pytest coverage for pass/fail cases.

## Phase 3 prompt

Implement the LLM audit layer from `AI_PIPELINE_SPEC.md`. Create a `ModelClient` interface, a deterministic `MockModelClient`, and an optional OpenAI client that is only used when `MODEL_MODE=openai` and `OPENAI_API_KEY` exists. All model outputs must be validated with Pydantic. Add tests for mock LLM output.

## Phase 4 prompt

Implement evidence validation and fail-closed behavior. Every required-evidence finding must include a quote that validates against the source document. If no evidence validates, downgrade the finding to `insufficient_evidence`, preserve the original status in validation metadata, and write an audit log. Add tests for valid quote, invalid quote, and downgrade behavior.

## Phase 5 prompt

Implement `POST /audits/run` and `GET /audits/{id}`. The audit runner should load document and question-set version, run deterministic and LLM checks, validate evidence, persist audit run/findings/evidence spans/audit logs, and return summary counts. Add integration tests for seeded documents.

## Phase 6 prompt

Implement the eval harness from `EVAL_SPEC.md`. Add `POST /evals/run` and `GET /evals/latest`. The eval runner should run seeded eval cases through the same audit pipeline, compare expected vs actual findings, compute metrics, persist eval run/results, and return metrics. Add tests for metric computation.

## Phase 7 prompt

Build the Next.js UI from `UI_SPEC.md`: Dashboard, Documents, Audit Detail, Question Sets, and Evals. The UI should call real API endpoints. It should show evidence validation status and insufficient-evidence downgrades clearly. Keep styling simple and professional. Add TypeScript types for API responses.

## Phase 8 prompt

Add lightweight provider trends and feedback preview. Implement provider trend API and optional `/providers/[id]` page. Keep this secondary. Do not spend time on complex charts if the core audit/eval pages are not complete.

## Phase 9 prompt

Prepare the public repo. Use `README_PUBLIC_TEMPLATE.md` to write the final README. Add screenshots placeholders or generated screenshots if available. Add a demo script, limitations, architecture diagram, and final verification commands. Ensure README does not claim medical correctness, HIPAA compliance, or affiliation with Brellium.

## Final hardening prompt

Review the entire codebase against `IMPLEMENTATION_CHECKLIST.md`. Fix failing tests, broken typecheck, missing README caveats, missing evidence validation, missing eval metrics, and any language that overclaims clinical correctness. Produce a final verification summary with exact commands run and results.
