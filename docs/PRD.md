# PRD: AuditTrace

## Product name

AuditTrace

## Tagline

Synthetic AI chart-audit reliability system with versioned question sets, evidence-backed findings, fail-closed validation, and eval metrics.

## Goal

Build a focused, production-shaped AI engineering prototype that demonstrates reliable clinical-document audit workflows without using real PHI or making medical/compliance claims.

The project should show how an AI system can:

1. Apply evolving audit criteria to synthetic clinical notes.
2. Combine deterministic checks with LLM-based narrative judgment.
3. Return structured findings with source evidence.
4. Validate every evidence quote against the source document.
5. Fail closed when evidence does not validate.
6. Measure reliability through an eval harness and dashboard.

## Why this exists

Clinical documentation review is not a simple summarization task. Requirements can be objective, subjective, payer-specific, specialty-specific, and versioned over time. AI outputs are useful only if they are grounded, auditable, and measurable.

AuditTrace is built to demonstrate that engineering pattern.

## What this is not

AuditTrace is not:

- Medical advice
- A clinical decision system
- A compliance-certified product
- A system making a HIPAA compliance claim
- A Brellium clone
- Affiliated with Brellium
- A system using real PHI

All data must be synthetic.

## Target reviewer

Primary reviewer: engineering leader or AI/full-stack engineer at Brellium.

Secondary reviewer: recruiter or founder who wants to understand whether the candidate can build real AI product systems, not toy demos.

## Primary user in the prototype

A compliance/quality lead reviewing synthetic clinical documentation for documentation gaps.

## Core workflow

```txt
Synthetic note + metadata
  -> select question-set version
  -> run deterministic checks
  -> run LLM narrative checks
  -> validate evidence spans
  -> persist audit findings
  -> display audit detail
  -> run eval harness
  -> display reliability metrics
```

## MVP scope

### Must have

1. Synthetic notes seeded locally.
2. Versioned question sets.
3. Deterministic checks for objective requirements.
4. LLM audit runner with structured output.
5. Evidence-span validator.
6. Fail-closed output downgrade to `insufficient_evidence`.
7. Audit detail UI.
8. Eval harness with 30-50 synthetic cases.
9. Eval dashboard with clear metrics.
10. Public README with limitations and tradeoffs.

### Should have

1. Provider trend mini-view.
2. Generated provider feedback draft.
3. Question-set version comparison.
4. Markdown export of audit packet.

### Nice to have only if time remains

1. Upload flow.
2. PDF export.
3. Basic auth.
4. Async background jobs.
5. Docker Compose for local Postgres.

## Non-goals

1. Full EMR integration.
2. Real clinical correctness.
3. Medical diagnosis.
4. Real payer rules.
5. Real patient data.
6. Full enterprise RBAC.
7. Billing system.
8. Brellium UI clone.

## Success criteria

The project is successful if a reviewer can understand in under 3 minutes that it proves:

- AI outputs are not blindly trusted.
- Question criteria are versioned.
- Findings are source-backed.
- Unsupported claims fail closed.
- Reliability is measured with evals.
- The system is built with a real backend, database, tests, and UI.

## Demo acceptance flow

1. Open dashboard.
2. Open seeded synthetic ABA note.
3. Run audit using `ABA-97155-v1`.
4. Show one deterministic finding.
5. Show one LLM narrative finding with evidence span.
6. Show one rejected/insufficient-evidence finding.
7. Open question-set version history.
8. Run evals.
9. Show metrics and regression failures.

## Positioning language

Use this in README and outreach:

> AuditTrace is a synthetic engineering prototype. It does not try to recreate Brellium or make medical claims. It focuses on the reliability layer around AI audits: versioned criteria, evidence validation, fail-closed outputs, and eval metrics.
