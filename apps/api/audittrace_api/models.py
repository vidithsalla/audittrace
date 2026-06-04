from datetime import date, datetime
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from audittrace_api.db import Base


def new_uuid() -> str:
    return str(uuid4())


def utcnow() -> datetime:
    return datetime.utcnow()


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    external_provider_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    specialty: Mapped[str] = mapped_column(String(80), index=True)
    state: Mapped[str] = mapped_column(String(2))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    documents: Mapped[list["SyntheticDocument"]] = relationship(back_populates="provider")
    feedback: Mapped[list["ProviderFeedback"]] = relationship(back_populates="provider")


class SyntheticDocument(Base):
    __tablename__ = "synthetic_documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    provider_id: Mapped[str] = mapped_column(ForeignKey("providers.id"), index=True)
    synthetic_patient_id: Mapped[str] = mapped_column(String(120))
    title: Mapped[str] = mapped_column(String(240))
    specialty: Mapped[str] = mapped_column(String(80), index=True)
    service_code: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    payer: Mapped[str | None] = mapped_column(String(160), nullable=True)
    state: Mapped[str] = mapped_column(String(2))
    date_of_service: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    note_type: Mapped[str] = mapped_column(String(80))
    body: Mapped[str] = mapped_column(Text)
    source_kind: Mapped[str] = mapped_column(String(40), default="seeded")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    provider: Mapped[Provider] = relationship(back_populates="documents")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    audit_runs: Mapped[list["AuditRun"]] = relationship(back_populates="document")
    eval_cases: Mapped[list["EvalCase"]] = relationship(back_populates="document")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (UniqueConstraint("document_id", "chunk_index", name="uq_document_chunk_index"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    document_id: Mapped[str] = mapped_column(ForeignKey("synthetic_documents.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    start_char: Mapped[int] = mapped_column(Integer)
    end_char: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    document: Mapped[SyntheticDocument] = relationship(back_populates="chunks")


class QuestionSet(Base):
    __tablename__ = "question_sets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    slug: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(240))
    specialty: Mapped[str] = mapped_column(String(80), index=True)
    description: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    versions: Mapped[list["QuestionSetVersion"]] = relationship(back_populates="question_set", cascade="all, delete-orphan")


class QuestionSetVersion(Base):
    __tablename__ = "question_set_versions"
    __table_args__ = (UniqueConstraint("question_set_id", "version", name="uq_question_set_version"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    question_set_id: Mapped[str] = mapped_column(ForeignKey("question_sets.id"), index=True)
    version: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(40), index=True)
    change_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    active_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    active_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    question_set: Mapped[QuestionSet] = relationship(back_populates="versions")
    questions: Mapped[list["Question"]] = relationship(back_populates="version", cascade="all, delete-orphan")
    audit_runs: Mapped[list["AuditRun"]] = relationship(back_populates="question_set_version")
    eval_cases: Mapped[list["EvalCase"]] = relationship(back_populates="question_set_version")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    version_id: Mapped[str] = mapped_column(ForeignKey("question_set_versions.id"), index=True)
    question_key: Mapped[str] = mapped_column(String(160), index=True)
    criterion_text: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(40), index=True)
    check_type: Mapped[str] = mapped_column(String(40), index=True)
    requires_evidence: Mapped[bool] = mapped_column(Boolean, default=True)
    expected_answer_type: Mapped[str] = mapped_column(String(80))
    deterministic_rule: Mapped[str | None] = mapped_column(String(120), nullable=True)
    prompt_hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    version: Mapped[QuestionSetVersion] = relationship(back_populates="questions")
    findings: Mapped[list["AuditFinding"]] = relationship(back_populates="question")


class AuditRun(Base):
    __tablename__ = "audit_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    document_id: Mapped[str] = mapped_column(ForeignKey("synthetic_documents.id"), index=True)
    question_set_version_id: Mapped[str] = mapped_column(ForeignKey("question_set_versions.id"), index=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    model_mode: Mapped[str] = mapped_column(String(40))
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    document: Mapped[SyntheticDocument] = relationship(back_populates="audit_runs")
    question_set_version: Mapped[QuestionSetVersion] = relationship(back_populates="audit_runs")
    findings: Mapped[list["AuditFinding"]] = relationship(back_populates="audit_run", cascade="all, delete-orphan")


class AuditFinding(Base):
    __tablename__ = "audit_findings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    audit_run_id: Mapped[str] = mapped_column(ForeignKey("audit_runs.id"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), index=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    severity: Mapped[str] = mapped_column(String(40), index=True)
    reason: Mapped[str] = mapped_column(Text)
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(40))
    evidence_validated: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    unsupported_finding: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    validation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    audit_run: Mapped[AuditRun] = relationship(back_populates="findings")
    question: Mapped[Question] = relationship(back_populates="findings")
    evidence_spans: Mapped[list["EvidenceSpan"]] = relationship(back_populates="finding", cascade="all, delete-orphan")


class EvidenceSpan(Base):
    __tablename__ = "evidence_spans"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    finding_id: Mapped[str] = mapped_column(ForeignKey("audit_findings.id"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("synthetic_documents.id"), index=True)
    quote: Mapped[str] = mapped_column(Text)
    start_char: Mapped[int | None] = mapped_column(Integer, nullable=True)
    end_char: Mapped[int | None] = mapped_column(Integer, nullable=True)
    validation_status: Mapped[str] = mapped_column(String(40), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    finding: Mapped[AuditFinding] = relationship(back_populates="evidence_spans")


class EvalCase(Base):
    __tablename__ = "eval_cases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    case_key: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("synthetic_documents.id"), index=True)
    question_set_version_id: Mapped[str] = mapped_column(ForeignKey("question_set_versions.id"), index=True)
    expected_findings: Mapped[list] = mapped_column(JSON)
    tags: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    document: Mapped[SyntheticDocument] = relationship(back_populates="eval_cases")
    question_set_version: Mapped[QuestionSetVersion] = relationship(back_populates="eval_cases")
    results: Mapped[list["EvalResult"]] = relationship(back_populates="eval_case")


class EvalRun(Base):
    __tablename__ = "eval_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    question_set_version_id: Mapped[str | None] = mapped_column(ForeignKey("question_set_versions.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(40), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    results: Mapped[list["EvalResult"]] = relationship(back_populates="eval_run", cascade="all, delete-orphan")


class EvalResult(Base):
    __tablename__ = "eval_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    eval_run_id: Mapped[str] = mapped_column(ForeignKey("eval_runs.id"), index=True)
    eval_case_id: Mapped[str] = mapped_column(ForeignKey("eval_cases.id"), index=True)
    audit_run_id: Mapped[str | None] = mapped_column(ForeignKey("audit_runs.id"), nullable=True, index=True)
    passed: Mapped[bool] = mapped_column(Boolean)
    expected: Mapped[dict | list] = mapped_column(JSON)
    actual: Mapped[dict | list] = mapped_column(JSON)
    errors: Mapped[dict | list] = mapped_column(JSON)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    eval_run: Mapped[EvalRun] = relationship(back_populates="results")
    eval_case: Mapped[EvalCase] = relationship(back_populates="results")


class ProviderFeedback(Base):
    __tablename__ = "provider_feedback"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    provider_id: Mapped[str] = mapped_column(ForeignKey("providers.id"), index=True)
    audit_run_id: Mapped[str | None] = mapped_column(ForeignKey("audit_runs.id"), nullable=True, index=True)
    feedback_text: Mapped[str] = mapped_column(Text)
    issue_summary: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    provider: Mapped[Provider] = relationship(back_populates="feedback")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    actor: Mapped[str] = mapped_column(String(120))
    action: Mapped[str] = mapped_column(String(160), index=True)
    entity_type: Mapped[str] = mapped_column(String(80), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
