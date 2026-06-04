# Capture Screenshots

This repo does not add a screenshot automation dependency for Phase 6. Use this manual workflow to capture real screenshots from the seeded local app.

## Start The App

Terminal 1:

```bash
cd apps/api
python3 -m audittrace_api.seed
uvicorn audittrace_api.main:app --reload
```

Terminal 2:

```bash
cd apps/web
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

Open:

```txt
http://localhost:3000
```

## Capture Targets

Save screenshots under `docs/screenshots/`.

1. `dashboard.png`
   - Open `/`.
   - Show the synthetic-only disclaimer and system counts.

2. `document-detail-before-audit.png`
   - Open `/documents`.
   - Select `ABA 97155 missing rationale synthetic note 001`.
   - Show source note text and the question-set version selector.

3. `audit-detail-evidence-backed.png`
   - Run audit with `aba-97155-v1`.
   - Show the audit detail page with a validated evidence quote and audit log timeline.

4. `audit-detail-insufficient-evidence.png`
   - Select `Adversarial invalid evidence synthetic note 001`.
   - Run audit with `aba-97155-v1`.
   - Show `Downgraded: insufficient evidence`.

5. `eval-dashboard.png`
   - Open `/evals`.
   - Run eval in mock mode.
   - Show metric cards and failures preview.

6. `question-sets.png`
   - Open `/question-sets`.
   - Show versioned criteria and question counts.

## Notes

- Do not use fake screenshots.
- Do not include real PHI or local secrets.
- If browser chrome is visible, make sure the URL is local and no personal tabs are included.
