# UI_SPEC.md

## Design principle

The UI should prove the system. It should not look like a generic SaaS template.

Keep it clean, plain, and demoable.

## Navigation

Top nav:

- Dashboard
- Documents
- Question Sets
- Evals

## Page: /dashboard

Purpose: quick project overview and latest system status.

Show:
- latest audit count
- latest eval metrics
- critical failures count
- unsupported finding rate
- evidence span match rate
- short explanation of workflow

Primary CTA:
- View documents
- Run latest eval

## Page: /documents

Purpose: list synthetic notes.

Table columns:
- title
- specialty
- service code
- provider
- state
- date of service
- actions: view / run audit

Filters:
- specialty
- service code
- provider

## Page: /documents/[id] or /audits/new

Optional if time allows.

Show document body and let reviewer select a question-set version and run audit.

## Page: /audits/[id]

Most important UI page.

Layout:

Left side:
- synthetic note body
- highlighted evidence spans

Right side:
- audit summary
- findings grouped by severity/status
- each finding card includes:
  - question key
  - criterion text
  - status
  - severity
  - source: deterministic/llm/validator
  - reason
  - resolution
  - evidence validation status
  - evidence quote

Special visual states:
- fail
- needs_review
- insufficient_evidence
- pass

For `insufficient_evidence`, show:

```txt
This finding was downgraded because required evidence did not validate against the source note.
```

## Page: /question-sets

Purpose: show versioned criteria.

Show:
- question set list
- versions
- status
- change summary
- questions table

Include side-by-side v1/v2 diff for ABA-97155 if possible.

## Page: /evals

Second most important page.

Show:
- Run eval button
- latest eval metrics cards
- failed case table
- regression failures by question-set version
- link from failed case to audit run

Metric cards:
- Critical issue recall
- False positive rate
- Unsupported finding rate
- Evidence span match rate
- Insufficient evidence rate
- Avg audit latency

## Page: /providers/[id]

Optional supporting page.

Show:
- top failing criteria
- trend score over synthetic time
- feedback preview

Do not spend too much time here.

## Component guidelines

Use small components:

- FindingCard
- EvidenceQuote
- MetricCard
- QuestionSetVersionBadge
- EvalFailureTable
- DocumentTable

## Copy guidelines

Avoid clinical overclaims.

Use:
- synthetic note
- audit finding
- documentation gap
- evidence-backed
- fail-closed
- needs review

Avoid:
- medically correct
- compliant
- certified
- real patient
- diagnosis

## Demo path

UI must support this path:

1. Open Dashboard.
2. Open Documents.
3. Select ABA 97155 missing rationale note.
4. Run audit.
5. Open audit detail.
6. Show evidence-backed finding.
7. Show insufficient-evidence downgrade.
8. Open Evals.
9. Run latest eval and show metrics.
