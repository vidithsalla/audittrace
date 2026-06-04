from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from audittrace_api.db import get_db
from audittrace_api.models import EvalResult, EvalRun
from audittrace_api.schemas import (
    EvalCaseResultResponse,
    EvalFailurePreview,
    EvalMetricsResponse,
    EvalRunDetailResponse,
    EvalRunRequest,
    EvalRunResponse,
)
from audittrace_api.services.eval_runner import EvalFilters, latest_eval_run, run_eval

router = APIRouter(prefix="/evals", tags=["evals"])


def _load_eval_run(db: Session, eval_run_id: str) -> EvalRun | None:
    return db.scalar(
        select(EvalRun)
        .options(selectinload(EvalRun.results).joinedload(EvalResult.eval_case))
        .where(EvalRun.id == eval_run_id)
    )


def _metrics_response(metrics: dict) -> EvalMetricsResponse:
    return EvalMetricsResponse(
        total_cases=metrics.get("total_cases", 0),
        total_questions_evaluated=metrics.get("total_questions_evaluated", 0),
        critical_issue_recall=metrics.get("critical_issue_recall"),
        false_positive_rate=metrics.get("false_positive_rate"),
        unsupported_finding_rate=metrics.get("unsupported_finding_rate"),
        evidence_span_match_rate=metrics.get("evidence_span_match_rate"),
        insufficient_evidence_rate=metrics.get("insufficient_evidence_rate"),
        regression_failures_by_question_set_version=metrics.get("regression_failures_by_question_set_version", {}),
        average_audit_latency_ms=metrics.get("average_audit_latency_ms"),
    )


def _failure_preview(eval_run: EvalRun, limit: int = 10) -> list[EvalFailurePreview]:
    failures = [result for result in eval_run.results if not result.passed]
    return [
        EvalFailurePreview(
            eval_case_id=result.eval_case_id,
            case_key=result.eval_case.case_key,
            audit_run_id=result.audit_run_id,
            errors=result.errors,
        )
        for result in sorted(failures, key=lambda item: item.created_at)[:limit]
    ]


def _detail_response(eval_run: EvalRun) -> EvalRunDetailResponse:
    results = sorted(eval_run.results, key=lambda item: item.created_at)
    return EvalRunDetailResponse(
        id=eval_run.id,
        status=eval_run.status,
        started_at=eval_run.started_at.isoformat(),
        completed_at=eval_run.completed_at.isoformat() if eval_run.completed_at else None,
        metrics=_metrics_response(eval_run.metrics),
        failures_preview=_failure_preview(eval_run),
        results=[
            EvalCaseResultResponse(
                id=result.id,
                eval_case_id=result.eval_case_id,
                case_key=result.eval_case.case_key,
                audit_run_id=result.audit_run_id,
                passed=result.passed,
                expected=result.expected,
                actual=result.actual,
                errors=result.errors,
                latency_ms=result.latency_ms,
            )
            for result in results
        ],
    )


@router.post("/run", response_model=EvalRunResponse)
def run_eval_endpoint(request: EvalRunRequest, db: Session = Depends(get_db)) -> EvalRunResponse:
    if request.limit is not None and request.limit < 1:
        raise HTTPException(status_code=422, detail="limit must be greater than 0")

    try:
        eval_run = run_eval(
            db,
            EvalFilters(
                question_set_version_id=request.question_set_version_id,
                specialty=request.specialty,
                service_code=request.service_code,
                scenario_type=request.scenario_type,
                limit=request.limit,
                model_mode=request.model_mode,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    loaded = _load_eval_run(db, eval_run.id)
    if loaded is None:
        raise HTTPException(status_code=500, detail="Eval run could not be reloaded")
    return EvalRunResponse(
        eval_run_id=loaded.id,
        status=loaded.status,
        metrics=_metrics_response(loaded.metrics),
        failures_preview=_failure_preview(loaded),
        result_count=len(loaded.results),
    )


@router.get("/latest", response_model=EvalRunDetailResponse)
def get_latest_eval(db: Session = Depends(get_db)) -> EvalRunDetailResponse:
    eval_run = latest_eval_run(db)
    if eval_run is None:
        raise HTTPException(status_code=404, detail="No eval runs found")
    loaded = _load_eval_run(db, eval_run.id)
    if loaded is None:
        raise HTTPException(status_code=404, detail="No eval runs found")
    return _detail_response(loaded)


@router.get("/{eval_run_id}", response_model=EvalRunDetailResponse)
def get_eval(eval_run_id: str, db: Session = Depends(get_db)) -> EvalRunDetailResponse:
    eval_run = _load_eval_run(db, eval_run_id)
    if eval_run is None:
        raise HTTPException(status_code=404, detail="Eval run not found")
    return _detail_response(eval_run)
