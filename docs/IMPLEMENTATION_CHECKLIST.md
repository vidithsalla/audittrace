# IMPLEMENTATION_CHECKLIST.md

## Core system checklist

- [ ] FastAPI backend runs locally
- [ ] Next.js frontend runs locally
- [ ] Database schema implemented
- [ ] Seed script creates providers
- [ ] Seed script creates synthetic documents
- [ ] Seed script creates question sets
- [ ] Seed script creates question-set versions
- [ ] Seed script creates questions
- [ ] Seed script creates eval cases
- [ ] `/documents` API works
- [ ] `/question-sets` API works
- [ ] Deterministic checks implemented
- [ ] Mock LLM client implemented
- [ ] Optional OpenAI client implemented or stubbed cleanly
- [ ] Evidence validator implemented
- [ ] Fail-closed downgrade implemented
- [ ] Audit run persistence works
- [ ] Audit detail API works
- [ ] Eval runner works
- [ ] Eval metrics persist
- [ ] Audit logs written

## UI checklist

- [ ] Dashboard page
- [ ] Documents page
- [ ] Audit detail page
- [ ] Question sets page
- [ ] Evals page
- [ ] Evidence quote display
- [ ] Insufficient-evidence downgrade visible
- [ ] Eval metric cards
- [ ] Failed eval cases table

## Test checklist

- [ ] Valid evidence quote validates
- [ ] Invalid evidence quote fails
- [ ] Missing evidence downgrades required-evidence finding
- [ ] Missing signature deterministic check fails
- [ ] Duration/unit mismatch deterministic check fails
- [ ] Mock LLM returns typed output
- [ ] Audit runner persists findings
- [ ] Eval runner computes metrics

## Packaging checklist

- [ ] Public README written
- [ ] Limitations section included
- [ ] “What this is not” section included
- [ ] Screenshots added
- [ ] Demo script included
- [ ] Real eval metrics added
- [ ] Final verification commands included

## Final verification

Backend:

```bash
cd apps/api
pytest
```

Frontend:

```bash
cd apps/web
npm run typecheck
npm run build
```

Manual demo:

- [ ] Can run an audit from seeded note
- [ ] Can show valid evidence span
- [ ] Can show insufficient-evidence downgrade
- [ ] Can run evals
- [ ] Can explain the project in 90 seconds

## Do not ship if

- [ ] README implies medical correctness
- [ ] README claims HIPAA compliance
- [ ] App requires real PHI
- [ ] Eval dashboard is missing
- [ ] Evidence validator is missing
- [ ] Question-set versioning is missing
- [ ] Project looks like a Brellium clone
