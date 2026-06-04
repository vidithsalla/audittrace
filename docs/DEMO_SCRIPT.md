# AuditTrace Demo Script

## 60-Second Demo

1. Open the dashboard.
2. Say: "AuditTrace is synthetic only. It is not medical advice and does not claim compliance. The point is the reliability layer around AI audits."
3. Point to the workflow: versioned question sets, deterministic checks, mock narrative checks, evidence validation, fail-closed findings, eval metrics.
4. Open Documents.
5. Select `ABA 97155 missing rationale synthetic note 001`.
6. Run audit with `aba-97155-v1`.
7. Open the audit detail page.
8. Show the evidence-backed `protocol_change_rationale` finding.
9. Show the real audit log timeline.
10. Open Evals and run eval in mock mode.
11. Point to `unsupported_finding_rate` and `evidence_span_match_rate`.

## 2-Minute Demo

1. Start on Dashboard.
2. Explain the disclaimer: synthetic data only, no real PHI, no medical advice, no HIPAA compliance claim, not affiliated with Brellium.
3. Open Question Sets.
4. Show that `aba-97155` has `v1` and `v2`.
5. Open Documents and choose `ABA 97155 missing rationale synthetic note 001`.
6. Run audit with `aba-97155-v1`.
7. On Audit Detail, show:
   - summary counts
   - audit log timeline
   - deterministic checks
   - mock narrative findings
   - validated evidence quote with character offsets
8. Return to Documents and choose `Adversarial invalid evidence synthetic note 001`.
9. Run audit with `aba-97155-v1`.
10. Show the `insufficient_evidence` downgrade and explain that invalid evidence was stored but not trusted.
11. Open Evals.
12. Run eval in mock mode.
13. Explain that high scores are expected because the mock runner and seeded expectations are deterministic; the point is that metrics are real and persisted.

## What To Say About Limitations

- "The current narrative runner is mock-only. It is shaped like a future structured LLM path, but it does not call an external API."
- "All notes are synthetic and generated for demo reliability testing."
- "This is not a clinical correctness system."
- "There is no auth, EMR integration, billing, or patient management."
- "The next step would be a larger labeled synthetic corpus and real structured-output model mode behind the same evidence validator."
