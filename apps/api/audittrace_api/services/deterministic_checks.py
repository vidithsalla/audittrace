import re
from collections.abc import Callable

from audittrace_api.models import Question, SyntheticDocument
from audittrace_api.services.audit_types import DraftFinding


SIGNATURE_PATTERNS = ("Signed:", "Provider Signature:", "Electronically signed by")
CREDENTIALS = ("BCBA", "RBT", "LCSW", "RN", "MD", "DO", "NP")


def has_signature(body: str) -> bool:
    return any(pattern.lower() in body.lower() for pattern in SIGNATURE_PATTERNS)


def has_credential(body: str) -> bool:
    signature_tail = body[-300:]
    return any(re.search(rf"\b{re.escape(credential)}\b", signature_tail, flags=re.IGNORECASE) for credential in CREDENTIALS) or any(
        re.search(rf"\b{re.escape(credential)}\b", body, flags=re.IGNORECASE) for credential in CREDENTIALS
    )


def has_date_of_service(document: SyntheticDocument) -> bool:
    if document.date_of_service is not None:
        return True
    return re.search(r"Date of Service:\s*\d{4}-\d{2}-\d{2}", document.body, flags=re.IGNORECASE) is not None


def has_service_code(document: SyntheticDocument) -> bool:
    if document.service_code:
        return True
    return re.search(r"Service Code:\s*\w+", document.body, flags=re.IGNORECASE) is not None


def parse_duration_and_units(body: str) -> tuple[int | None, int | None]:
    duration_match = re.search(r"Duration:\s*(\d+)\s*minutes?", body, flags=re.IGNORECASE)
    units_match = re.search(r"Billed Units:\s*(\d+)", body, flags=re.IGNORECASE)
    duration = int(duration_match.group(1)) if duration_match else None
    units = int(units_match.group(1)) if units_match else None
    return duration, units


def has_required_section(body: str, label: str) -> bool:
    return re.search(rf"^{re.escape(label)}\s*$", body, flags=re.IGNORECASE | re.MULTILINE) is not None


def has_measurable_decline_indicator(body: str) -> bool:
    lower_body = body.lower()
    measurable_terms = ("weight", "measurement", "decline", "dyspnea", "intake", "pps", "adl", "baseline")
    return any(term in lower_body for term in measurable_terms)


def _base_finding(question: Question, status: str, reason: str, resolution: str | None = None, confidence: float = 1.0) -> DraftFinding:
    return DraftFinding(
        question_id=question.id,
        status=status,
        severity=question.severity,
        reason=reason,
        resolution=resolution,
        confidence=confidence,
        source="deterministic",
        requires_evidence=question.requires_evidence,
        evidence_validated=not question.requires_evidence,
        validation_notes="Evidence not required for this deterministic criterion." if not question.requires_evidence else None,
    )


def check_missing_signature(document: SyntheticDocument, question: Question) -> DraftFinding:
    if has_signature(document.body):
        return _base_finding(question, "pass", "A synthetic provider signature marker is present.")
    return _base_finding(
        question,
        "fail",
        "No accepted synthetic provider signature marker was found.",
        "Add a dated synthetic provider signature marker such as Provider Signature.",
    )


def check_missing_credential(document: SyntheticDocument, question: Question) -> DraftFinding:
    if has_credential(document.body):
        return _base_finding(question, "pass", "An accepted synthetic provider credential is present.")
    return _base_finding(
        question,
        "fail",
        "No accepted synthetic provider credential was found in the note.",
        "Add a synthetic credential such as BCBA, RN, LCSW, MD, DO, NP, or RBT.",
    )


def check_missing_date_of_service(document: SyntheticDocument, question: Question) -> DraftFinding:
    if has_date_of_service(document):
        return _base_finding(question, "pass", "A date of service is present in metadata or source text.")
    return _base_finding(question, "fail", "No date of service was found.", "Add a synthetic date of service.")


def check_missing_service_code(document: SyntheticDocument, question: Question) -> DraftFinding:
    if has_service_code(document):
        return _base_finding(question, "pass", "A service code is present in metadata or source text.")
    return _base_finding(question, "fail", "No service code was found.", "Add the synthetic service code when the question set requires it.")


def check_duration_unit_mismatch(document: SyntheticDocument, question: Question) -> DraftFinding:
    if document.specialty != "aba":
        return _base_finding(question, "pass", "Duration/unit matching is only applied to ABA synthetic notes.")

    duration, units = parse_duration_and_units(document.body)
    if duration is None or units is None:
        return _base_finding(
            question,
            "needs_review",
            "Duration or billed units could not be parsed from the synthetic note.",
            "Document both duration in minutes and billed units.",
            confidence=0.7,
        )
    expected_units = duration // 15 if duration % 15 == 0 else None
    if expected_units == units:
        return _base_finding(question, "pass", f"Duration of {duration} minutes matches {units} billed units.")
    return _base_finding(
        question,
        "fail",
        f"Duration of {duration} minutes does not match {units} billed units using 15-minute units.",
        "Correct the synthetic duration or billed units so they agree.",
    )


def check_missing_required_section(document: SyntheticDocument, question: Question) -> DraftFinding:
    label = question.prompt_hint or "Plan:"
    if has_required_section(document.body, label):
        return _base_finding(question, "pass", f"Required section {label} is present.")
    return _base_finding(question, "fail", f"Required section {label} is missing.", f"Add a {label} section to the synthetic note.")


def check_missing_measurable_decline_indicator(document: SyntheticDocument, question: Question) -> DraftFinding:
    if has_measurable_decline_indicator(document.body):
        return _base_finding(question, "pass", "The note contains a simple measurable decline indicator.")
    return _base_finding(
        question,
        "fail",
        "No simple measurable decline indicator was found in the hospice-style note.",
        "Add synthetic measurable decline detail if this criterion requires it.",
    )


CHECKS: dict[str, Callable[[SyntheticDocument, Question], DraftFinding]] = {
    "missing_signature": check_missing_signature,
    "missing_credential": check_missing_credential,
    "missing_date_of_service": check_missing_date_of_service,
    "missing_date": check_missing_date_of_service,
    "missing_service_code": check_missing_service_code,
    "duration_unit_mismatch": check_duration_unit_mismatch,
    "missing_required_section": check_missing_required_section,
    "missing_caregiver_presence": check_missing_required_section,
    "missing_measurable_decline_indicator": check_missing_measurable_decline_indicator,
}


def run_deterministic_check(document: SyntheticDocument, question: Question) -> DraftFinding:
    if not question.deterministic_rule:
        return _base_finding(question, "needs_review", "No deterministic rule was configured for this question.", confidence=0.5)

    check = CHECKS.get(question.deterministic_rule)
    if check is None:
        return _base_finding(question, "needs_review", f"Unsupported deterministic rule: {question.deterministic_rule}", confidence=0.5)
    return check(document, question)
