# AuditTrace Codex Build Pack

This folder contains the implementation brief for **AuditTrace**, an independent portfolio prototype for synthetic AI chart-audit reliability.

The project is intentionally narrow:

- Versioned question sets
- Evidence-backed audit findings
- Fail-closed validation
- Eval dashboard
- Synthetic clinical documentation only

It is not affiliated with Brellium, not a Brellium clone, not medical advice, not a clinical compliance product, and makes no HIPAA compliance claim.

## Recommended use with Codex in VS Code

1. Create a fresh repo named `audittrace`.
2. Copy this entire pack into the repo under `/docs` or paste files into the root as needed.
3. Give Codex `CODEX_BUILD_GUIDE.md` first.
4. Ask Codex to implement phase by phase, not all at once.
5. After every phase, run tests/typecheck/build and commit.

## File map

- `PRD.md` - product requirement document and scope
- `CODEX_BUILD_GUIDE.md` - exact build phases and implementation instructions
- `DATA_SCHEMA.md` - database tables, fields, relationships, and indexes
- `API_CONTRACTS.md` - FastAPI endpoint contracts and response shapes
- `EVAL_SPEC.md` - eval cases, metrics, pass/fail definitions, and dashboard requirements
- `SEED_DATA_SPEC.md` - synthetic note and question-set generation plan
- `AI_PIPELINE_SPEC.md` - deterministic checks, LLM audit runner, evidence validation, fail-closed behavior
- `UI_SPEC.md` - Next.js screens and component requirements
- `README_PUBLIC_TEMPLATE.md` - final public README structure
- `DEMO_SCRIPT.md` - 60s, 90s, and 3-minute demo scripts
- `OUTREACH_AFTER_BUILD.md` - messages to send after the repo is ready
- `IMPLEMENTATION_CHECKLIST.md` - done criteria and final verification
- `prompts/CODEX_PHASE_PROMPTS.md` - copy/paste prompts for Codex phase-by-phase
- `seed_specs/synthetic_cases.csv` - seed-case blueprint, not final generated data
