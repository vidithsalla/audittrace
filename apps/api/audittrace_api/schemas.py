from datetime import date

from pydantic import BaseModel, ConfigDict


class HealthResponse(BaseModel):
    status: str
    service: str


class DocumentListItem(BaseModel):
    id: str
    title: str
    provider_id: str
    provider_name: str
    specialty: str
    service_code: str | None
    state: str
    date_of_service: date | None
    note_type: str


class DocumentsResponse(BaseModel):
    documents: list[DocumentListItem]


class DocumentMetadata(BaseModel):
    provider_id: str
    provider_name: str
    specialty: str
    service_code: str | None
    payer: str | None
    state: str
    date_of_service: date | None
    note_type: str


class DocumentDetailResponse(BaseModel):
    id: str
    title: str
    metadata: DocumentMetadata
    body: str


class QuestionSetVersionSummary(BaseModel):
    id: str
    version: str
    status: str
    change_summary: str | None


class QuestionSetSummary(BaseModel):
    id: str
    slug: str
    name: str
    specialty: str
    versions: list[QuestionSetVersionSummary]


class QuestionSetsResponse(BaseModel):
    question_sets: list[QuestionSetSummary]


class QuestionSetRef(BaseModel):
    id: str
    slug: str
    name: str


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    question_key: str
    criterion_text: str
    severity: str
    check_type: str
    requires_evidence: bool
    deterministic_rule: str | None


class QuestionSetVersionDetailResponse(BaseModel):
    id: str
    question_set: QuestionSetRef
    version: str
    status: str
    questions: list[QuestionResponse]


class AuditRunRequest(BaseModel):
    document_id: str
    question_set_version_id: str
    model_mode: str = "mock"


class EvidenceSpanResponse(BaseModel):
    quote: str
    start_char: int | None
    end_char: int | None
    validation_status: str


class AuditFindingResponse(BaseModel):
    id: str
    question_id: str
    question_key: str
    criterion_text: str
    status: str
    severity: str
    reason: str
    resolution: str | None
    confidence: float | None
    source: str
    evidence_validated: bool
    unsupported_finding: bool
    validation_notes: str | None
    evidence_spans: list[EvidenceSpanResponse]


class AuditLogResponse(BaseModel):
    id: str
    actor: str
    action: str
    entity_type: str
    entity_id: str | None
    metadata: dict
    created_at: str


class AuditDocumentRef(BaseModel):
    id: str
    title: str
    body: str | None = None


class AuditQuestionSetVersionRef(BaseModel):
    id: str
    slug: str
    version: str


class AuditRunSummaryItem(BaseModel):
    id: str
    status: str
    model_mode: str
    latency_ms: int | None
    summary: dict
    created_at: str


class DocumentAuditsResponse(BaseModel):
    audits: list[AuditRunSummaryItem]


class AuditRunResponse(BaseModel):
    audit_id: str
    audit_run_id: str
    document_id: str
    question_set_version_id: str
    status: str
    summary: dict
    latency_ms: int | None
    findings: list[AuditFindingResponse]


class AuditDetailResponse(BaseModel):
    id: str
    document: AuditDocumentRef
    question_set_version: AuditQuestionSetVersionRef
    status: str
    model_mode: str
    summary: dict
    latency_ms: int | None
    findings: list[AuditFindingResponse]
    logs: list[AuditLogResponse]


class EvalRunRequest(BaseModel):
    question_set_version_id: str | None = None
    specialty: str | None = None
    service_code: str | None = None
    scenario_type: str | None = None
    limit: int | None = None
    model_mode: str = "mock"


class EvalMetricsResponse(BaseModel):
    total_cases: int
    total_questions_evaluated: int
    critical_issue_recall: float | None
    false_positive_rate: float | None
    unsupported_finding_rate: float | None
    evidence_span_match_rate: float | None
    insufficient_evidence_rate: float | None
    regression_failures_by_question_set_version: dict[str, int]
    average_audit_latency_ms: float | None


class EvalFailurePreview(BaseModel):
    eval_case_id: str
    case_key: str
    audit_run_id: str | None
    errors: list[dict]


class EvalRunResponse(BaseModel):
    eval_run_id: str
    status: str
    metrics: EvalMetricsResponse
    failures_preview: list[EvalFailurePreview]
    result_count: int


class EvalCaseResultResponse(BaseModel):
    id: str
    eval_case_id: str
    case_key: str
    audit_run_id: str | None
    passed: bool
    expected: list[dict]
    actual: list[dict]
    errors: list[dict]
    latency_ms: int | None


class EvalRunDetailResponse(BaseModel):
    id: str
    status: str
    started_at: str
    completed_at: str | None
    metrics: EvalMetricsResponse
    failures_preview: list[EvalFailurePreview]
    results: list[EvalCaseResultResponse]
