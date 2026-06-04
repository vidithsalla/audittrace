# Eval Results

Latest local eval output from the mock runner and seeded synthetic corpus:

```json
{
  "status": "completed",
  "metrics": {
    "total_cases": 38,
    "total_questions_evaluated": 42,
    "critical_issue_recall": 1.0,
    "false_positive_rate": 0.0,
    "unsupported_finding_rate": 0.0,
    "evidence_span_match_rate": 0.8211,
    "insufficient_evidence_rate": 0.1023,
    "regression_failures_by_question_set_version": {},
    "average_audit_latency_ms": 4.9474
  },
  "result_count": 38,
  "failures_preview": []
}
```

## Metric Definitions

- `total_cases`: eval cases selected and executed.
- `total_questions_evaluated`: expected finding rows compared across selected cases.
- `critical_issue_recall`: expected critical failures found divided by expected critical failures.
- `false_positive_rate`: unexpected fail findings divided by explicit non-fail expectations.
- `unsupported_finding_rate`: required-evidence findings with invalid or missing evidence that were trusted instead of downgraded, divided by findings requiring evidence.
- `evidence_span_match_rate`: valid produced evidence spans divided by all produced evidence spans.
- `insufficient_evidence_rate`: insufficient-evidence findings divided by all audit findings.
- `regression_failures_by_question_set_version`: failed eval comparisons grouped by question-set version ID.
- `average_audit_latency_ms`: average audit-run latency across eval cases.

Metrics with a zero denominator return `null`.

## Why Some Metrics Are Perfect In Mock Mode

The current narrative runner is deterministic and intentionally aligned with the seeded synthetic expectations. This makes the harness stable and easy to verify without external API keys. The high `critical_issue_recall` and zero `unsupported_finding_rate` show that the local reliability loop is working, not that the system is clinically correct.

The adversarial cases still matter: the mock runner emits invalid evidence in seeded examples, and the validator downgrades those findings to `insufficient_evidence` instead of trusting them.

## What Would Change With A Real LLM

With a real LLM, expected changes include:

- More variable narrative outputs.
- More unsupported or partially supported evidence quotes.
- More eval failures requiring prompt/schema/check refinements.
- Latency and cost tracking.
- A larger synthetic eval corpus with reviewer-labeled edge cases.

The core rule would stay the same: model output is proposed, not trusted, until source evidence validates.
