# Screenshot Instructions

Do not use fake screenshots. Capture these after starting the seeded backend and frontend.

See also [../../scripts/capture_screenshots.md](../../scripts/capture_screenshots.md) for the public screenshot workflow.

## Automated Local Capture

The project includes a safe Playwright workflow that uses isolated Chromium and refuses non-local app URLs.

Prerequisites:

1. Seed and start the backend:

```bash
cd apps/api
python3 -m audittrace_api.seed
uvicorn audittrace_api.main:app --reload
```

2. Start the frontend:

```bash
cd apps/web
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run dev
```

3. Capture screenshots:

```bash
cd apps/web
AUDITTRACE_BASE_URL=http://localhost:3000 npm run screenshots
```

Optional env vars:

```txt
AUDITTRACE_BASE_URL=http://localhost:3000
AUDITTRACE_API_BASE_URL=http://localhost:8000
```

Safety rules:

- Only `localhost`, `127.0.0.1`, and `::1` URLs are allowed.
- The script uses an isolated Playwright Chromium context.
- The script does not use a persistent browser profile.
- Screenshots are full-page PNGs at a fixed `1440x1100` viewport.
- The script waits for visible UI text before each capture.

## Screenshot Targets

1. `dashboard.png`
   - Dashboard showing synthetic-only disclaimer, document count, question-set count, and latest eval status.

2. `documents.png`
   - Documents list with seeded synthetic notes.

3. `document-detail.png`
   - A seeded document detail page with source note text and question-set version selector.

4. `audit-detail-evidence.png`
   - Audit detail page showing evidence-backed findings, evidence validation status, and audit log timeline.

5. `audit-detail-insufficient-evidence.png`
   - Adversarial audit showing `Downgraded: insufficient evidence`.

6. `evals.png`
   - Evals page after running mock eval, showing metrics and failures preview.

7. `question-sets.png`
   - Question-set versions and criteria table.
