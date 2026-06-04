# AI_PIPELINE_SPEC.md

## Goal

Build a reliable AI audit pipeline that does not blindly trust LLM outputs.

Core rule:

> A finding that requires evidence cannot be trusted unless the cited evidence validates against the source note.

## Pipeline

```txt
input document
  -> question-set version
  -> deterministic checks
  -> LLM checks
  -> evidence-span validation
  -> finding normalization
  -> fail-closed downgrade if needed
  -> persistence
  -> eval metrics
```

## Deterministic checks

Implement as pure functions.

Input:
- document metadata
- document body
- question

Output:
- structured finding

Rules:

### missing_signature

Fail if body does not contain a signature pattern.

Accept patterns:
- `Signed:`
- `Provider Signature:`
- `Electronically signed by`

### missing_credential

Fail if provider credential not found near signature or metadata.

Accept simple synthetic credentials:
- BCBA
- RBT
- LCSW
- RN
- MD
- DO
- NP

### missing_date_of_service

Fail if metadata date missing and body has no date marker.

### missing_service_code

Fail if metadata service code missing and body does not mention service code.

### duration_unit_mismatch

For ABA only.

If note has minutes and billed units, verify:

```txt
expected_units = minutes / 15
```

Allow integer match only for MVP.

### missing_required_section

Fail if configured section labels are missing.

Example section labels:
- `Intervention:`
- `Response:`
- `Plan:`
- `Caregiver Training:`

## LLM checks

Use structured output only.

Pydantic schema:

```python
class LlmEvidenceSpan(BaseModel):
    quote: str

class LlmAuditFinding(BaseModel):
    status: Literal["pass", "fail", "needs_review", "insufficient_evidence"]
    reason: str
    resolution: str | None = None
    confidence: float | None = None
    evidence_spans: list[LlmEvidenceSpan] = []
```

Prompt requirements:

- Mention synthetic note only.
- Ask model to answer only the given criterion.
- Require direct quotes if evidence is used.
- Do not allow medical advice.
- Prefer `needs_review` or `insufficient_evidence` over unsupported confidence.

## Mock model mode

Required for deterministic demo and tests.

Implement `MockModelClient` with simple keyword-based rules mapped to synthetic seed cases.

Mock mode should intentionally produce one invalid evidence quote for an adversarial case so the validator downgrade can be demonstrated.

## OpenAI mode

Optional.

Use if `OPENAI_API_KEY` is set. Otherwise default to mock.

Do not block demo on OpenAI.

## Evidence validation

Function:

```python
def validate_evidence(note_text: str, quote: str) -> EvidenceValidationResult:
    ...
```

Validation rules:

1. Normalize whitespace.
2. Case-insensitive exact substring match.
3. Return original start/end char if possible.
4. If no match, mark invalid.

## Fail-closed policy

For each finding:

If `question.requires_evidence` is true and finding status is `pass`, `fail`, or `needs_review`, then:

- If no evidence spans, downgrade to `insufficient_evidence`.
- If all evidence spans invalid, downgrade to `insufficient_evidence`.
- If at least one span validates, keep status but record invalid spans.

Downgrade metadata:

```json
{
  "original_status": "fail",
  "downgraded_to": "insufficient_evidence",
  "reason": "Required evidence did not validate against source text."
}
```

Write audit log:

```txt
finding.downgraded.insufficient_evidence
```

## Finding normalization

All findings must have:

- question_id
- status
- severity
- reason
- resolution
- source
- evidence_validated
- validation_notes

No raw LLM response should be persisted as the canonical finding.

## Safety wording

Do not say:
- compliant
- medically correct
- clinically valid
- HIPAA compliant
- certified

Use:
- audit finding
- synthetic result
- documentation gap
- needs review
- evidence-backed
- insufficient evidence

## Tests

Required tests:

1. Valid quote validates.
2. Invalid quote fails.
3. Required evidence missing downgrades finding.
4. Deterministic missing signature fails.
5. Deterministic duration mismatch fails.
6. Mock LLM returns structured finding.
7. Audit runner persists downgraded finding.
8. Eval runner counts unsupported finding correctly.
