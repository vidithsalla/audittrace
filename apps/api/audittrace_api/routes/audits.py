from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from audittrace_api.db import get_db
from audittrace_api.models import AuditFinding, AuditLog, AuditRun, QuestionSetVersion
from audittrace_api.schemas import (
    AuditDetailResponse,
    AuditDocumentRef,
    AuditFindingResponse,
    AuditQuestionSetVersionRef,
    AuditLogResponse,
    AuditRunRequest,
    AuditRunResponse,
    AuditRunSummaryItem,
    DocumentAuditsResponse,
    EvidenceSpanResponse,
)
from audittrace_api.services.audit_runner import (
    AuditRunError,
    DocumentNotFoundError,
    QuestionSetVersionNotFoundError,
    run_audit,
)

router = APIRouter(tags=["audits"])


def _load_audit_run(db: Session, audit_run_id: str) -> AuditRun | None:
    return db.scalar(
        select(AuditRun)
        .options(
            joinedload(AuditRun.document),
            joinedload(AuditRun.question_set_version).joinedload(QuestionSetVersion.question_set),
            selectinload(AuditRun.findings).joinedload(AuditFinding.question),
            selectinload(AuditRun.findings).selectinload(AuditFinding.evidence_spans),
        )
        .where(AuditRun.id == audit_run_id)
    )


def _finding_response(finding) -> AuditFindingResponse:
    return AuditFindingResponse(
        id=finding.id,
        question_id=finding.question_id,
        question_key=finding.question.question_key,
        criterion_text=finding.question.criterion_text,
        status=finding.status,
        severity=finding.severity,
        reason=finding.reason,
        resolution=finding.resolution,
        confidence=finding.confidence,
        source=finding.source,
        evidence_validated=finding.evidence_validated,
        unsupported_finding=finding.unsupported_finding,
        validation_notes=finding.validation_notes,
        evidence_spans=[
            EvidenceSpanResponse(
                quote=span.quote,
                start_char=span.start_char,
                end_char=span.end_char,
                validation_status=span.validation_status,
            )
            for span in sorted(finding.evidence_spans, key=lambda item: item.created_at)
        ],
    )


def _findings_response(audit_run: AuditRun) -> list[AuditFindingResponse]:
    return [
        _finding_response(finding)
        for finding in sorted(audit_run.findings, key=lambda item: (item.severity, item.question.question_key))
    ]


def _logs_response(db: Session, audit_run_id: str) -> list[AuditLogResponse]:
    logs = db.scalars(
        select(AuditLog)
        .where(AuditLog.entity_id == audit_run_id)
        .order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
    ).all()
    return [
        AuditLogResponse(
            id=log.id,
            actor=log.actor,
            action=log.action,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            metadata=log.metadata_json,
            created_at=log.created_at.isoformat(),
        )
        for log in logs
    ]


@router.post("/audits/run", response_model=AuditRunResponse)
def run_audit_endpoint(request: AuditRunRequest, db: Session = Depends(get_db)) -> AuditRunResponse:
    try:
        audit_run = run_audit(
            db,
            document_id=request.document_id,
            question_set_version_id=request.question_set_version_id,
            model_mode=request.model_mode,
        )
    except DocumentNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Document not found") from exc
    except QuestionSetVersionNotFoundError as exc:
        raise HTTPException(status_code=404, detail="Question set version not found") from exc
    except AuditRunError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    loaded = _load_audit_run(db, audit_run.id)
    if loaded is None:
        raise HTTPException(status_code=500, detail="Audit run could not be reloaded")

    return AuditRunResponse(
        audit_id=loaded.id,
        audit_run_id=loaded.id,
        document_id=loaded.document_id,
        question_set_version_id=loaded.question_set_version_id,
        status=loaded.status,
        summary=loaded.summary,
        latency_ms=loaded.latency_ms,
        findings=_findings_response(loaded),
    )


@router.get("/audits/{audit_run_id}", response_model=AuditDetailResponse)
def get_audit(audit_run_id: str, db: Session = Depends(get_db)) -> AuditDetailResponse:
    audit_run = _load_audit_run(db, audit_run_id)
    if audit_run is None:
        raise HTTPException(status_code=404, detail="Audit run not found")

    return AuditDetailResponse(
        id=audit_run.id,
        document=AuditDocumentRef(id=audit_run.document.id, title=audit_run.document.title, body=audit_run.document.body),
        question_set_version=AuditQuestionSetVersionRef(
            id=audit_run.question_set_version.id,
            slug=audit_run.question_set_version.question_set.slug,
            version=audit_run.question_set_version.version,
        ),
        status=audit_run.status,
        model_mode=audit_run.model_mode,
        summary=audit_run.summary,
        latency_ms=audit_run.latency_ms,
        findings=_findings_response(audit_run),
        logs=_logs_response(db, audit_run.id),
    )


@router.get("/documents/{document_id}/audits", response_model=DocumentAuditsResponse)
def list_document_audits(document_id: str, db: Session = Depends(get_db)) -> DocumentAuditsResponse:
    audits = db.scalars(
        select(AuditRun)
        .where(AuditRun.document_id == document_id)
        .order_by(AuditRun.created_at.desc())
    ).all()
    return DocumentAuditsResponse(
        audits=[
            AuditRunSummaryItem(
                id=audit.id,
                status=audit.status,
                model_mode=audit.model_mode,
                latency_ms=audit.latency_ms,
                summary=audit.summary,
                created_at=audit.created_at.isoformat(),
            )
            for audit in audits
        ]
    )
