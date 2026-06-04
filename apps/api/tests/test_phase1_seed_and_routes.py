from fastapi.testclient import TestClient
from sqlalchemy import select

from audittrace_api.db import SessionLocal
from audittrace_api.main import app
from audittrace_api.models import EvalCase, Provider, Question, QuestionSetVersion, SyntheticDocument
from audittrace_api.seed import SYNTHETIC_NOTICE, seed_database


def reseed() -> dict[str, int]:
    with SessionLocal() as db:
        return seed_database(db)


def test_seed_inserts_phase1_minimum_counts() -> None:
    counts = reseed()

    assert counts["providers"] == 8
    assert counts["question_set_versions"] == 5
    assert counts["questions"] == 27
    assert 30 <= counts["synthetic_documents"] <= 50
    assert counts["eval_cases"] == counts["synthetic_documents"]

    with SessionLocal() as db:
        assert db.scalar(select(Provider).where(Provider.external_provider_id == "prov_aba_001")) is not None
        assert db.scalar(select(QuestionSetVersion).where(QuestionSetVersion.version == "v2")) is not None
        assert db.scalar(select(Question).where(Question.question_key == "protocol_change_rationale")) is not None
        document = db.scalar(select(SyntheticDocument).limit(1))
        assert document is not None
        assert SYNTHETIC_NOTICE in document.body
        assert db.scalar(select(EvalCase).limit(1)) is not None


def test_documents_api_lists_and_returns_seeded_note_detail() -> None:
    reseed()
    client = TestClient(app)

    response = client.get("/documents", params={"specialty": "aba", "service_code": "97155"})
    assert response.status_code == 200
    documents = response.json()["documents"]
    assert documents
    assert documents[0]["provider_name"].startswith("Synthetic")

    detail = client.get(f"/documents/{documents[0]['id']}")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["metadata"]["specialty"] == "aba"
    assert SYNTHETIC_NOTICE in payload["body"]


def test_question_sets_api_exposes_versions_and_questions() -> None:
    reseed()
    client = TestClient(app)

    response = client.get("/question-sets")
    assert response.status_code == 200
    question_sets = response.json()["question_sets"]
    aba_97155 = next(item for item in question_sets if item["slug"] == "aba-97155")
    assert {version["version"] for version in aba_97155["versions"]} == {"v1", "v2"}

    version_id = next(version["id"] for version in aba_97155["versions"] if version["version"] == "v1")
    detail = client.get(f"/question-sets/{version_id}")
    assert detail.status_code == 200
    question_keys = {question["question_key"] for question in detail.json()["questions"]}
    assert "missing_signature" in question_keys
    assert "protocol_change_rationale" in question_keys
