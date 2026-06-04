# Recommended Demo Cases

Seeded document UUIDs are regenerated every time `python3 -m audittrace_api.seed` resets the database, so use these stable titles and question-set versions.

## 1. Passing Audit With Validated Evidence

- Document title: `ABA 97155 clean pass synthetic note 001`
- Question-set version: `aba-97155-v1`
- What it shows:
  - deterministic objective checks passing
  - narrative findings with valid source quotes
  - evidence span offsets on the audit detail page

## 2. Evidence-Backed Failing Finding

- Document title: `ABA 97155 missing rationale synthetic note 001`
- Question-set version: `aba-97155-v1`
- What it shows:
  - `protocol_change_rationale` fails
  - finding cites `Protocol was adjusted during the session.`
  - evidence validates against the source note

## 3. Fail-Closed Downgrade

- Document title: `Adversarial invalid evidence synthetic note 001`
- Question-set version: `aba-97155-v1`
- What it shows:
  - mock narrative runner proposes a finding with a quote that is not in the note
  - evidence validator records the invalid span
  - finding is downgraded to `insufficient_evidence`
  - audit log timeline records validation and completion

## 4. Eval Metrics

- Page: `/evals`
- Action: Run eval in mock mode
- What it shows:
  - seeded cases run through the same audit path
  - metrics persisted on `eval_runs`
  - unsupported finding rate remains zero when fail-closed behavior works
