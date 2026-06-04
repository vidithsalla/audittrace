# EVAL_SPEC.md

## Goal

The eval harness proves that AuditTrace measures reliability instead of trusting model output blindly.

The eval system should run synthetic notes through the same audit path used by the app and compare actual findings against expected findings.

## Eval case design

Each eval case includes:

- case_key
- document_id
- question_set_version_id
- tags
- expected findings

Expected finding format:

```json
[
  {
    "question_key": "protocol_change_rationale",
    "expected_status": "fail",
    "severity": "critical",
    "must_have_evidence": true
  }
]
```

## Required metrics

### critical_issue_recall

Measures how many expected critical failures were detected.

```txt
critical_issue_recall = detected_expected_critical_failures / total_expected_critical_failures
```

### false_positive_rate

Measures how many failures were returned where the expected label was pass.

```txt
false_positive_rate = false_positive_failures / total_expected_passes
```

### unsupported_finding_rate

Measures how many findings claimed support without valid source evidence.

```txt
unsupported_finding_rate = findings_with_invalid_required_evidence / findings_requiring_evidence
```

Goal: 0.0 in mock mode.

### evidence_span_match_rate

Measures how many evidence quotes were found in source text.

```txt
evidence_span_match_rate = valid_evidence_spans / total_evidence_spans
```

### insufficient_evidence_rate

Measures how often the system failed closed.

```txt
insufficient_evidence_rate = insufficient_evidence_findings / total_findings
```

This is not automatically bad. It can be desirable when source support is missing.

### regression_failures_by_question_set_version

Groups failed eval cases by question-set version.

Example:

```json
{
  "ABA-97155-v1": 1,
  "Hospice-Eligibility-v1": 2
}
```

### average_audit_latency_ms

Average end-to-end audit time per case.

## Pass/fail definitions

An eval case passes if:

1. All expected critical failures are detected.
2. No unsupported required-evidence finding is trusted.
3. Evidence spans validate when required.
4. Actual status matches expected status for required question keys.

An eval case can fail for:

- missed critical finding
- false positive critical finding
- invalid evidence not downgraded
- wrong status
- audit runner error

## Seed eval target

Minimum:
- 30 eval cases

Preferred:
- 50 eval cases

Distribution:

| Category | Count |
|---|---:|
| ABA 97155 | 12 |
| ABA 97156 | 10 |
| Hospice eligibility | 10 |
| Behavioral health medical necessity | 8 |
| Adversarial evidence validation | 5 |
| Question-set version regression | 5 |

## Adversarial cases

Include cases where:

1. LLM mock returns a quote that does not exist.
2. Note has generic language that should be `needs_review`, not `pass`.
3. Note has all objective fields but weak narrative support.
4. Note has good narrative support but missing signature.
5. v1 passes but v2 fails because criterion became stricter.

## UI requirements

Eval dashboard should show:

- latest eval run metrics
- metric cards
- failed cases table
- failed case reason
- link to audit run
- regression failures grouped by question-set version

## README reporting

In README, include real local output like:

```txt
Eval run: 36 cases
critical_issue_recall: 0.94
evidence_span_match_rate: 0.97
unsupported_finding_rate: 0.00
average_audit_latency_ms: 811
```

Never invent metrics. If metrics are imperfect, report them honestly and explain tradeoffs.
