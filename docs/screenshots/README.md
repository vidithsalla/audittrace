# Screenshot Instructions

Do not use fake screenshots. Capture these after starting the seeded backend and frontend.

See also [../../scripts/capture_screenshots.md](../../scripts/capture_screenshots.md) for the public screenshot workflow.

Recommended screenshots:

1. `dashboard.png`
   - Dashboard showing synthetic-only disclaimer, document count, question-set count, and latest eval status.

2. `document-detail-run-audit.png`
   - A seeded document detail page with source note text and question-set version selector.

3. `audit-detail-evidence.png`
   - Audit detail page showing evidence-backed findings, evidence validation status, and audit log timeline.

4. `audit-detail-insufficient-evidence.png`
   - Adversarial audit showing `Downgraded: insufficient evidence`.

5. `eval-dashboard.png`
   - Evals page after running mock eval, showing metrics and failures preview.

6. `question-sets.png`
   - Question-set versions and criteria table.

Suggested local flow:

```bash
cd apps/api
python3 -m audittrace_api.seed
uvicorn audittrace_api.main:app --reload
```

In another terminal:

```bash
cd apps/web
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

Open `http://localhost:3000` and capture the screens above.
