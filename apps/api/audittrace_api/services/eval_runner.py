from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from audittrace_api.models import (
    AuditFinding,
    AuditLog,
    AuditRun,
    EvalCase,
    EvalResult,
    EvalRun,
    QuestionSetVersion,
    SyntheticDocument,
)
from audittrace_api.services.audit_runner import run_audit


REQUIRED_METRIC_KEYS = (
    "total_cases",
    "total_questions_evaluated",
    "critical_issue_recall",
    "false_positive_rate",
    "unsupported_finding_rate",
    "evidence_span_match_rate",
    "insufficient_evidence_rate",
    "regression_failures_by_question_set_version",
    "average_audit_latency_ms",
)


@dataclass
class EvalFilters:
    question_set_version_id: str | None = None
    specialty: str | None = None
    service_code: str | None = None
    scenario_type: str | None = None
    limit: int | None = None
    model_mode: str = "mock"


@dataclass
class EvalCaseComparison:
    eval_case: EvalCase
    audit_run: AuditRun | None
    expected: list[dict]
    actual: list[dict]
    errors: list[dict]
    passed: bool
    latency_ms: int | None


def _log(db: Session, action: str, entity_type: str, entity_id: str | None, metadata: dict | None = None) -> None:
    db.add(
        AuditLog(
            actor="system",
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata_json=metadata or {},
        )
    )


def select_eval_cases(db: Session, filters: EvalFilters) -> list[EvalCase]:
    stmt = (
        select(EvalCase)
        .join(EvalCase.document)
        .options(
            joinedload(EvalCase.document),
            joinedload(EvalCase.question_set_version).joinedload(QuestionSetVersion.question_set),
        )
        .order_by(EvalCase.case_key)
    )
    if filters.question_set_version_id:
        stmt = stmt.where(EvalCase.question_set_version_id == filters.question_set_version_id)
    if filters.specialty:
        stmt = stmt.where(SyntheticDocument.specialty == filters.specialty)
    if filters.service_code:
        stmt = stmt.where(SyntheticDocument.service_code == filters.service_code)
    if filters.scenario_type:
        stmt = stmt.where(EvalCase.tags["scenario_type"].as_string() == filters.scenario_type)
    if filters.limit is not None:
        stmt = stmt.limit(filters.limit)
    return list(db.scalars(stmt).all())


def _load_audit_run_with_findings(db: Session, audit_run_id: str) -> AuditRun:
    audit_run = db.scalar(
        select(AuditRun)
        .options(
            joinedload(AuditRun.question_set_version).joinedload(QuestionSetVersion.question_set),
            selectinload(AuditRun.findings).joinedload(AuditFinding.question),
            selectinload(AuditRun.findings).selectinload(AuditFinding.evidence_spans),
        )
        .where(AuditRun.id == audit_run_id)
    )
    if audit_run is None:
        raise RuntimeError(f"Audit run disappeared during eval: {audit_run_id}")
    return audit_run


def _actual_findings(audit_run: AuditRun) -> list[dict]:
    actual: list[dict] = []
    for finding in audit_run.findings:
        evidence_spans = [
            {
                "quote": span.quote,
                "validation_status": span.validation_status,
                "start_char": span.start_char,
                "end_char": span.end_char,
            }
            for span in finding.evidence_spans
        ]
        actual.append(
            {
                "question_id": finding.question_id,
                "question_key": finding.question.question_key,
                "status": finding.status,
                "severity": finding.severity,
                "requires_evidence": finding.question.requires_evidence,
                "evidence_validated": finding.evidence_validated,
                "unsupported_finding": finding.unsupported_finding,
                "evidence_spans": evidence_spans,
            }
        )
    return sorted(actual, key=lambda item: item["question_key"])


def compare_eval_case(eval_case: EvalCase, audit_run: AuditRun) -> EvalCaseComparison:
    expected = list(eval_case.expected_findings or [])
    actual = _actual_findings(audit_run)
    actual_by_key = {finding["question_key"]: finding for finding in actual}
    errors: list[dict] = []

    for expected_finding in expected:
        question_key = expected_finding["question_key"]
        expected_status = expected_finding["expected_status"]
        actual_finding = actual_by_key.get(question_key)
        if actual_finding is None:
            errors.append(
                {
                    "type": "missing_actual_finding",
                    "question_key": question_key,
                    "expected_status": expected_status,
                }
            )
            continue

        if actual_finding["status"] != expected_status:
            errors.append(
                {
                    "type": "status_mismatch",
                    "question_key": question_key,
                    "expected_status": expected_status,
                    "actual_status": actual_finding["status"],
                }
            )

        if expected_finding.get("must_have_evidence") and expected_status in {"pass", "fail", "needs_review"}:
            has_valid_span = any(span["validation_status"] == "valid" for span in actual_finding["evidence_spans"])
            if not has_valid_span:
                errors.append(
                    {
                        "type": "missing_valid_evidence",
                        "question_key": question_key,
                        "expected_status": expected_status,
                    }
                )

    # Unsupported required-evidence findings are only eval failures if they were trusted instead of failing closed.
    for actual_finding in actual:
        has_required_evidence_problem = actual_finding["requires_evidence"] and not actual_finding["evidence_validated"]
        if has_required_evidence_problem and actual_finding["status"] != "insufficient_evidence":
            errors.append(
                {
                    "type": "unsupported_finding_trusted",
                    "question_key": actual_finding["question_key"],
                    "actual_status": actual_finding["status"],
                }
            )

    return EvalCaseComparison(
        eval_case=eval_case,
        audit_run=audit_run,
        expected=expected,
        actual=actual,
        errors=errors,
        passed=not errors,
        latency_ms=audit_run.latency_ms,
    )


def compute_eval_metrics(comparisons: list[EvalCaseComparison]) -> dict:
    expected_critical_failures = 0
    detected_expected_critical_failures = 0
    non_fail_expectations = 0
    false_positive_failures = 0
    findings_requiring_evidence = 0
    trusted_unsupported_findings = 0
    valid_evidence_spans = 0
    total_evidence_spans = 0
    insufficient_evidence_findings = 0
    total_findings = 0
    total_latency = 0
    latency_count = 0
    regression_failures: dict[str, int] = {}

    for comparison in comparisons:
        actual_by_key = {finding["question_key"]: finding for finding in comparison.actual}

        for expected in comparison.expected:
            actual = actual_by_key.get(expected["question_key"])
            expected_status = expected["expected_status"]
            if expected["severity"] == "critical" and expected_status == "fail":
                expected_critical_failures += 1
                if actual and actual["status"] == "fail":
                    detected_expected_critical_failures += 1
            if expected_status != "fail":
                non_fail_expectations += 1
                if actual and actual["status"] == "fail":
                    false_positive_failures += 1

        for actual in comparison.actual:
            total_findings += 1
            if actual["status"] == "insufficient_evidence":
                insufficient_evidence_findings += 1
            if actual["requires_evidence"]:
                findings_requiring_evidence += 1
                if not actual["evidence_validated"] and actual["status"] != "insufficient_evidence":
                    trusted_unsupported_findings += 1
            for span in actual["evidence_spans"]:
                total_evidence_spans += 1
                if span["validation_status"] == "valid":
                    valid_evidence_spans += 1

        if comparison.latency_ms is not None:
            total_latency += comparison.latency_ms
            latency_count += 1

        if not comparison.passed:
            version_id = comparison.eval_case.question_set_version_id
            regression_failures[version_id] = regression_failures.get(version_id, 0) + 1

    # Denominator policy: return None when a metric has no meaningful denominator.
    return {
        "total_cases": len(comparisons),
        "total_questions_evaluated": sum(len(comparison.expected) for comparison in comparisons),
        "critical_issue_recall": _safe_ratio(detected_expected_critical_failures, expected_critical_failures),
        "false_positive_rate": _safe_ratio(false_positive_failures, non_fail_expectations),
        "unsupported_finding_rate": _safe_ratio(trusted_unsupported_findings, findings_requiring_evidence),
        "evidence_span_match_rate": _safe_ratio(valid_evidence_spans, total_evidence_spans),
        "insufficient_evidence_rate": _safe_ratio(insufficient_evidence_findings, total_findings),
        "regression_failures_by_question_set_version": regression_failures,
        "average_audit_latency_ms": _safe_ratio(total_latency, latency_count),
    }


def _safe_ratio(numerator: int | float, denominator: int | float) -> float | None:
    if denominator == 0:
        return None
    return round(numerator / denominator, 4)


def run_eval(db: Session, filters: EvalFilters) -> EvalRun:
    if filters.model_mode != "mock":
        raise ValueError("Only mock model mode is available in Phase 3.")

    eval_cases = select_eval_cases(db, filters)
    eval_run = EvalRun(
        question_set_version_id=filters.question_set_version_id,
        status="running",
        metrics={},
    )
    db.add(eval_run)
    db.flush()
    _log(db, "eval_started", "eval_run", eval_run.id, {"case_count": len(eval_cases), "filters": filters.__dict__})

    comparisons: list[EvalCaseComparison] = []
    for eval_case in eval_cases:
        try:
            audit_run = run_audit(
                db,
                document_id=eval_case.document_id,
                question_set_version_id=eval_case.question_set_version_id,
                model_mode=filters.model_mode,
            )
            audit_run = _load_audit_run_with_findings(db, audit_run.id)
            comparison = compare_eval_case(eval_case, audit_run)
        except Exception as exc:  # noqa: BLE001 - persisted eval errors are useful in this harness.
            comparison = EvalCaseComparison(
                eval_case=eval_case,
                audit_run=None,
                expected=list(eval_case.expected_findings or []),
                actual=[],
                errors=[{"type": "audit_runner_error", "message": str(exc)}],
                passed=False,
                latency_ms=None,
            )
        comparisons.append(comparison)
        db.add(
            EvalResult(
                eval_run=eval_run,
                eval_case=eval_case,
                audit_run_id=comparison.audit_run.id if comparison.audit_run else None,
                passed=comparison.passed,
                expected=comparison.expected,
                actual=comparison.actual,
                errors=comparison.errors,
                latency_ms=comparison.latency_ms,
            )
        )

    eval_run.metrics = compute_eval_metrics(comparisons)
    eval_run.status = "completed"
    eval_run.completed_at = datetime.utcnow()
    _log(db, "eval_completed", "eval_run", eval_run.id, {"metrics": eval_run.metrics})
    db.commit()
    db.refresh(eval_run)
    return eval_run


def latest_eval_run(db: Session) -> EvalRun | None:
    return db.scalar(select(EvalRun).order_by(EvalRun.created_at.desc()).limit(1))
