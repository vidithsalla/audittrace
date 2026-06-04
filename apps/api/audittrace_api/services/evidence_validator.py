import re
from dataclasses import dataclass

from audittrace_api.services.audit_types import DraftEvidenceSpan, DraftFinding


@dataclass(frozen=True)
class EvidenceValidationResult:
    quote: str
    validation_status: str
    start_char: int | None
    end_char: int | None


def _quote_pattern(quote: str) -> re.Pattern[str]:
    parts = [re.escape(part) for part in quote.strip().split()]
    return re.compile(r"\s+".join(parts), flags=re.IGNORECASE)


def validate_evidence(note_text: str, quote: str) -> EvidenceValidationResult:
    if not quote.strip():
        return EvidenceValidationResult(quote=quote, validation_status="invalid", start_char=None, end_char=None)

    match = _quote_pattern(quote).search(note_text)
    if match is None:
        return EvidenceValidationResult(quote=quote, validation_status="invalid", start_char=None, end_char=None)

    return EvidenceValidationResult(
        quote=quote,
        validation_status="valid",
        start_char=match.start(),
        end_char=match.end(),
    )


def validate_finding_evidence(note_text: str, finding: DraftFinding) -> DraftFinding:
    if not finding.evidence_spans:
        if finding.requires_evidence and finding.status in {"pass", "fail", "needs_review"}:
            finding.status = "insufficient_evidence"
            finding.evidence_validated = False
            finding.unsupported_finding = True
            finding.validation_notes = "Required evidence did not validate against source text: no evidence quote was provided."
        return finding

    validated_spans: list[DraftEvidenceSpan] = []
    for span in finding.evidence_spans:
        result = validate_evidence(note_text, span.quote)
        validated_spans.append(
            DraftEvidenceSpan(
                quote=span.quote,
                start_char=result.start_char,
                end_char=result.end_char,
                validation_status=result.validation_status,
            )
        )

    finding.evidence_spans = validated_spans
    valid_count = sum(1 for span in validated_spans if span.validation_status == "valid")

    if not finding.requires_evidence:
        finding.evidence_validated = valid_count > 0
        finding.validation_notes = "Evidence not required for this deterministic criterion."
        return finding

    if finding.status in {"pass", "fail", "needs_review"} and valid_count == 0:
        original_status = finding.status
        finding.status = "insufficient_evidence"
        finding.evidence_validated = False
        finding.unsupported_finding = True
        finding.validation_notes = (
            "Required evidence did not validate against source text. "
            f"Original status was {original_status}; finding was downgraded to insufficient_evidence."
        )
        return finding

    finding.evidence_validated = valid_count > 0
    invalid_count = len(validated_spans) - valid_count
    if invalid_count:
        finding.validation_notes = f"{valid_count} evidence span(s) validated; {invalid_count} invalid span(s) recorded."
    else:
        finding.validation_notes = "All required evidence spans validated against the source text."
    return finding
