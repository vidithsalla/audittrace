# Tradeoffs And Limitations

## Why Synthetic Data Only

AuditTrace is a public portfolio prototype. Using real PHI would create privacy, consent, storage, access control, and compliance concerns that are outside the point of this demo.

Synthetic data keeps the project focused on reliability mechanics:

- versioned criteria
- structured findings
- evidence validation
- fail-closed behavior
- eval metrics

## Why Mock Runner First

The current narrative runner is deterministic and LLM-compatible, but it does not call a real model. This makes the system runnable without API keys and keeps tests stable.

The important design choice is that model-like output is not trusted directly. The same evidence validator and persistence path would sit behind a real structured-output model.

## Why Evidence Validation Matters

Narrative audit findings are useful only if the reviewer can trace them back to the source note. AuditTrace validates direct quotes against the note text. If required evidence is missing or invalid, the finding fails closed to `insufficient_evidence`.

That means unsupported model output is visible but not treated as a supported finding.

## Why No Auth Or EMR Integration

Auth, RBAC, EMR integration, uploads, billing, and patient management would make this look more like a broad healthcare app. The goal is narrower: demonstrate the reliability layer around synthetic AI audits.

## What Production Would Need

A production system would need:

- real security model and access controls
- formal privacy and compliance review
- signed audit trails
- robust migrations
- async job execution
- model/provider observability
- larger labeled eval corpus
- human review workflows
- question-set governance and approval process
- deployment monitoring and rollback plans

AuditTrace intentionally does not claim any of those production properties.
