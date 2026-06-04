from dataclasses import dataclass, field

from pydantic import BaseModel, Field
from typing import Literal


FindingStatus = Literal["pass", "fail", "needs_review", "insufficient_evidence"]


@dataclass
class DraftEvidenceSpan:
    quote: str
    start_char: int | None = None
    end_char: int | None = None
    validation_status: str = "not_required"


@dataclass
class DraftFinding:
    question_id: str
    status: str
    severity: str
    reason: str
    resolution: str | None
    confidence: float | None
    source: str
    requires_evidence: bool
    evidence_spans: list[DraftEvidenceSpan] = field(default_factory=list)
    evidence_validated: bool = False
    unsupported_finding: bool = False
    validation_notes: str | None = None


class LlmEvidenceSpan(BaseModel):
    quote: str = Field(min_length=1)


class LlmAuditFinding(BaseModel):
    status: FindingStatus
    reason: str
    resolution: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    evidence_spans: list[LlmEvidenceSpan] = []
