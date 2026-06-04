from fastapi.testclient import TestClient
from sqlalchemy import select

from audittrace_api.db import SessionLocal
from audittrace_api.main import app
from audittrace_api.models import AuditFinding, AuditLog, AuditRun, Question, QuestionSet, QuestionSetVersion, SyntheticDocument
from audittrace_api.seed import seed_database
from audittrace_api.services.deterministic_checks import run_deterministic_check
from audittrace_api.services.evidence_validator import validate_evidence
from audittrace_api.services.llm_auditor import MockModelClient


def reseed() -> None:
    with SessionLocal() as db:
        seed_database(db)


def _document_by_title(db, title_fragment: str) -> SyntheticDocument:
    document = db.scalar(select(SyntheticDocument).where(SyntheticDocument.title.contains(title_fragment)).limit(1))
    assert document is not None
    return document


def _version(db, slug: str, version_name: str) -> QuestionSetVersion:
    version = db.scalar(
        select(QuestionSetVersion)
        .join(QuestionSet)
        .where(QuestionSet.slug == slug, QuestionSetVersion.version == version_name)
    )
    assert version is not None
    return version


def test_valid_evidence_quote_records_original_span() -> None:
    note = "Synthetic note.\nProtocol was adjusted during the session.\nProvider Signature: Synthetic, BCBA"

    result = validate_evidence(note, "Protocol was adjusted during the session.")

    assert result.validation_status == "valid"
    assert result.start_char == note.index("Protocol")
    assert result.end_char == result.start_char + len("Protocol was adjusted during the session.")


def test_invalid_evidence_quote_fails_validation() -> None:
    result = validate_evidence("Synthetic note with no matching sentence.", "This quote is absent.")

    assert result.validation_status == "invalid"
    assert result.start_char is None
    assert result.end_char is None


def test_deterministic_missing_signature_fails() -> None:
    document = SyntheticDocument(
        provider_id="provider-id",
        synthetic_patient_id="SYN-TEST-001",
        title="Synthetic missing signature unit note",
        specialty="aba",
        service_code="97155",
        payer="Synthetic Payer",
        state="IN",
        date_of_service=None,
        note_type="progress_note",
        body="Synthetic data notice: This note is fictional and contains no real patient information.\nService Code: 97155",
        source_kind="seeded",
    )
    question = Question(
        version_id="version-id",
        question_key="missing_signature",
        criterion_text="The note includes a dated provider signature.",
        severity="critical",
        check_type="deterministic",
        requires_evidence=False,
        expected_answer_type="pass_fail",
        deterministic_rule="missing_signature",
    )

    finding = run_deterministic_check(document, question)

    assert finding.status == "fail"
    assert finding.source == "deterministic"


def test_deterministic_duration_unit_mismatch_fails_on_seeded_case() -> None:
    reseed()
    with SessionLocal() as db:
        document = _document_by_title(db, "duration mismatch")
        question = db.scalar(select(Question).where(Question.question_key == "duration_unit_mismatch").limit(1))
        assert question is not None

        finding = run_deterministic_check(document, question)

    assert finding.status == "fail"
    assert "does not match" in finding.reason


def test_mock_model_returns_typed_structured_finding() -> None:
    reseed()
    with SessionLocal() as db:
        document = _document_by_title(db, "missing rationale")
        question = db.scalar(select(Question).where(Question.question_key == "protocol_change_rationale").limit(1))
        assert question is not None

        finding = MockModelClient().audit_question(document, question)

    assert finding.status == "fail"
    assert finding.evidence_spans
    assert finding.evidence_spans[0].quote == "Protocol was adjusted during the session."


def test_running_audit_persists_findings_spans_and_logs() -> None:
    reseed()
    client = TestClient(app)
    with SessionLocal() as db:
        document = _document_by_title(db, "missing rationale")
        version = _version(db, "aba-97155", "v1")

    response = client.post(
        "/audits/run",
        json={"document_id": document.id, "question_set_version_id": version.id},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["summary"]["total"] == 6
    assert payload["findings"]
    protocol_finding = next(finding for finding in payload["findings"] if finding["question_key"] == "protocol_change_rationale")
    assert protocol_finding["status"] == "fail"
    assert protocol_finding["evidence_validated"] is True
    assert protocol_finding["evidence_spans"][0]["validation_status"] == "valid"

    with SessionLocal() as db:
        audit_run = db.scalar(select(AuditRun).where(AuditRun.id == payload["audit_id"]))
        assert audit_run is not None
        assert db.scalar(select(AuditFinding).where(AuditFinding.audit_run_id == audit_run.id)) is not None
        actions = set(db.scalars(select(AuditLog.action).where(AuditLog.entity_id == audit_run.id)).all())

    assert {
        "audit_started",
        "deterministic_checks_completed",
        "narrative_checks_completed",
        "evidence_validation_completed",
        "audit_completed",
    }.issubset(actions)


def test_audit_downgrades_unsupported_mock_quote_to_insufficient_evidence() -> None:
    reseed()
    client = TestClient(app)
    with SessionLocal() as db:
        document = _document_by_title(db, "Adversarial invalid evidence")
        version = _version(db, "aba-97155", "v1")

    response = client.post(
        "/audits/run",
        json={"document_id": document.id, "question_set_version_id": version.id},
    )

    assert response.status_code == 200
    protocol_finding = next(
        finding for finding in response.json()["findings"] if finding["question_key"] == "protocol_change_rationale"
    )
    assert protocol_finding["status"] == "insufficient_evidence"
    assert protocol_finding["unsupported_finding"] is True
    assert protocol_finding["evidence_validated"] is False
    assert protocol_finding["evidence_spans"][0]["validation_status"] == "invalid"
    assert "downgraded" in protocol_finding["validation_notes"]


def test_audit_api_returns_persisted_detail_and_document_audit_history() -> None:
    reseed()
    client = TestClient(app)
    with SessionLocal() as db:
        document = _document_by_title(db, "clean pass")
        version = _version(db, "aba-97155", "v1")

    run_response = client.post("/audits/run", json={"document_id": document.id, "question_set_version_id": version.id})
    assert run_response.status_code == 200
    audit_id = run_response.json()["audit_id"]

    detail_response = client.get(f"/audits/{audit_id}")
    assert detail_response.status_code == 200
    detail = detail_response.json()
    assert detail["id"] == audit_id
    assert detail["document"]["body"]
    assert detail["findings"]
    assert [log["action"] for log in detail["logs"][:5]] == [
        "audit_started",
        "deterministic_checks_completed",
        "narrative_checks_completed",
        "evidence_validation_completed",
        "audit_completed",
    ]
    assert detail["logs"] == sorted(detail["logs"], key=lambda log: (log["created_at"], log["id"]))

    history_response = client.get(f"/documents/{document.id}/audits")
    assert history_response.status_code == 200
    assert history_response.json()["audits"][0]["id"] == audit_id


def test_run_audit_returns_clear_errors_for_invalid_inputs() -> None:
    reseed()
    client = TestClient(app)
    with SessionLocal() as db:
        version = _version(db, "aba-97155", "v1")
        document = _document_by_title(db, "clean pass")

    missing_document = client.post(
        "/audits/run",
        json={"document_id": "not-a-document", "question_set_version_id": version.id},
    )
    assert missing_document.status_code == 404
    assert missing_document.json()["detail"] == "Document not found"

    missing_version = client.post(
        "/audits/run",
        json={"document_id": document.id, "question_set_version_id": "not-a-version"},
    )
    assert missing_version.status_code == 404
    assert missing_version.json()["detail"] == "Question set version not found"

    invalid_model_mode = client.post(
        "/audits/run",
        json={"document_id": document.id, "question_set_version_id": version.id, "model_mode": "openai"},
    )
    assert invalid_model_mode.status_code == 422
