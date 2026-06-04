from datetime import datetime
from time import perf_counter

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from audittrace_api.models import (
    AuditFinding,
    AuditLog,
    AuditRun,
    EvidenceSpan,
    Question,
    QuestionSetVersion,
    SyntheticDocument,
)
from audittrace_api.services.audit_types import DraftFinding
from audittrace_api.services.deterministic_checks import run_deterministic_check
from audittrace_api.services.evidence_validator import validate_finding_evidence
from audittrace_api.services.llm_auditor import run_mock_narrative_check


class AuditRunError(Exception):
    pass


class DocumentNotFoundError(AuditRunError):
    pass


class QuestionSetVersionNotFoundError(AuditRunError):
    pass


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


def _summary(findings: list[DraftFinding]) -> dict:
    counts = {
        "total": len(findings),
        "pass": 0,
        "fail": 0,
        "needs_review": 0,
        "insufficient_evidence": 0,
        "critical_failures": 0,
        "unsupported_findings": 0,
    }
    for finding in findings:
        if finding.status in counts:
            counts[finding.status] += 1
        if finding.status == "fail" and finding.severity == "critical":
            counts["critical_failures"] += 1
        if finding.unsupported_finding:
            counts["unsupported_findings"] += 1
    return counts


def _persist_finding(db: Session, audit_run: AuditRun, draft: DraftFinding) -> AuditFinding:
    finding = AuditFinding(
        audit_run=audit_run,
        question_id=draft.question_id,
        status=draft.status,
        severity=draft.severity,
        reason=draft.reason,
        resolution=draft.resolution,
        confidence=draft.confidence,
        source=draft.source,
        evidence_validated=draft.evidence_validated,
        unsupported_finding=draft.unsupported_finding,
        validation_notes=draft.validation_notes,
    )
    db.add(finding)
    db.flush()

    for span in draft.evidence_spans:
        db.add(
            EvidenceSpan(
                finding=finding,
                document_id=audit_run.document_id,
                quote=span.quote,
                start_char=span.start_char,
                end_char=span.end_char,
                validation_status=span.validation_status,
            )
        )
    return finding


def run_audit(
    db: Session,
    document_id: str,
    question_set_version_id: str,
    model_mode: str = "mock",
) -> AuditRun:
    if model_mode != "mock":
        raise AuditRunError("Only mock model mode is available in Phase 2.")

    document = db.scalar(select(SyntheticDocument).where(SyntheticDocument.id == document_id))
    if document is None:
        raise DocumentNotFoundError(f"Document not found: {document_id}")

    version = db.scalar(
        select(QuestionSetVersion)
        .options(selectinload(QuestionSetVersion.questions), selectinload(QuestionSetVersion.question_set))
        .where(QuestionSetVersion.id == question_set_version_id)
    )
    if version is None:
        raise QuestionSetVersionNotFoundError(f"Question set version not found: {question_set_version_id}")

    started = perf_counter()
    audit_run = AuditRun(
        document=document,
        question_set_version=version,
        status="running",
        model_mode=model_mode,
        summary={},
    )
    db.add(audit_run)
    db.flush()
    _log(db, "audit_started", "audit_run", audit_run.id, {"document_id": document.id, "question_set_version_id": version.id})

    deterministic_findings: list[DraftFinding] = []
    narrative_findings: list[DraftFinding] = []
    for question in sorted(version.questions, key=lambda item: item.question_key):
        if question.check_type == "deterministic":
            deterministic_findings.append(run_deterministic_check(document, question))
        elif question.check_type == "llm":
            narrative_findings.append(run_mock_narrative_check(document, question))

    _log(
        db,
        "deterministic_checks_completed",
        "audit_run",
        audit_run.id,
        {"finding_count": len(deterministic_findings)},
    )
    _log(
        db,
        "narrative_checks_completed",
        "audit_run",
        audit_run.id,
        {"finding_count": len(narrative_findings), "model_mode": model_mode},
    )

    validated_findings: list[DraftFinding] = []
    downgrade_count = 0
    for finding in deterministic_findings + narrative_findings:
        original_status = finding.status
        validated = validate_finding_evidence(document.body, finding)
        validated_findings.append(validated)
        if original_status != validated.status and validated.status == "insufficient_evidence":
            downgrade_count += 1
            _log(
                db,
                "finding.downgraded.insufficient_evidence",
                "audit_run",
                audit_run.id,
                {"question_id": validated.question_id, "original_status": original_status},
            )

    _log(
        db,
        "evidence_validation_completed",
        "audit_run",
        audit_run.id,
        {"finding_count": len(validated_findings), "downgrade_count": downgrade_count},
    )

    for draft in validated_findings:
        _persist_finding(db, audit_run, draft)

    latency_ms = int((perf_counter() - started) * 1000)
    audit_run.status = "completed"
    audit_run.completed_at = datetime.utcnow()
    audit_run.latency_ms = latency_ms
    audit_run.summary = _summary(validated_findings)
    _log(db, "audit_completed", "audit_run", audit_run.id, {"latency_ms": latency_ms, "summary": audit_run.summary})
    db.commit()
    db.refresh(audit_run)
    return audit_run
