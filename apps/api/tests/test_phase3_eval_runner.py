from types import SimpleNamespace

from fastapi.testclient import TestClient
from sqlalchemy import select

from audittrace_api.db import SessionLocal
from audittrace_api.main import app
from audittrace_api.models import EvalCase, EvalResult, EvalRun, QuestionSet, QuestionSetVersion
from audittrace_api.seed import seed_database
from audittrace_api.services.eval_runner import EvalCaseComparison, compute_eval_metrics


def reseed() -> None:
    with SessionLocal() as db:
        seed_database(db)


def _version(db, slug: str, version_name: str) -> QuestionSetVersion:
    version = db.scalar(
        select(QuestionSetVersion)
        .join(QuestionSet)
        .where(QuestionSet.slug == slug, QuestionSetVersion.version == version_name)
    )
    assert version is not None
    return version


def test_eval_seed_cases_link_to_real_documents_versions_and_eval_tags() -> None:
    reseed()
    with SessionLocal() as db:
        cases = db.scalars(select(EvalCase)).all()

        assert len(cases) >= 30
        assert all(case.document is not None for case in cases)
        assert all(case.question_set_version is not None for case in cases)
        assert all(case.expected_findings for case in cases)
        assert all("scenario_type" in case.tags for case in cases)
        assert all("specialty" in case.tags for case in cases)
        assert any(expected["expected_status"] == "pass" for case in cases for expected in case.expected_findings)
        assert any(case.tags["scenario_type"] == "aba_97155_v1_pass_v2_fail" for case in cases)


def test_running_eval_persists_eval_run_results_and_required_metrics() -> None:
    reseed()
    client = TestClient(app)

    response = client.post("/evals/run", json={"model_mode": "mock"})

    assert response.status_code == 200
    payload = response.json()
    metrics = payload["metrics"]
    assert payload["status"] == "completed"
    assert payload["result_count"] == metrics["total_cases"]
    assert metrics["total_cases"] == 38
    assert metrics["total_questions_evaluated"] == 42
    assert set(metrics) == {
        "total_cases",
        "total_questions_evaluated",
        "critical_issue_recall",
        "false_positive_rate",
        "unsupported_finding_rate",
        "evidence_span_match_rate",
        "insufficient_evidence_rate",
        "regression_failures_by_question_set_version",
        "average_audit_latency_ms",
    }

    with SessionLocal() as db:
        eval_run = db.scalar(select(EvalRun).where(EvalRun.id == payload["eval_run_id"]))
        assert eval_run is not None
        assert db.scalar(select(EvalResult).where(EvalResult.eval_run_id == eval_run.id)) is not None


def test_eval_metrics_reflect_fail_closed_evidence_behavior() -> None:
    reseed()
    client = TestClient(app)

    response = client.post("/evals/run", json={"model_mode": "mock"})

    assert response.status_code == 200
    metrics = response.json()["metrics"]
    assert metrics["unsupported_finding_rate"] == 0
    assert metrics["evidence_span_match_rate"] is not None
    assert 0 < metrics["evidence_span_match_rate"] < 1
    assert metrics["insufficient_evidence_rate"] is not None
    assert metrics["insufficient_evidence_rate"] > 0


def test_compute_eval_metrics_on_controlled_small_fixture() -> None:
    version_id = "version-under-test"
    comparisons = [
        EvalCaseComparison(
            eval_case=SimpleNamespace(question_set_version_id=version_id),
            audit_run=None,
            expected=[
                {
                    "question_key": "critical_gap",
                    "expected_status": "fail",
                    "severity": "critical",
                    "must_have_evidence": True,
                },
                {
                    "question_key": "expected_pass",
                    "expected_status": "pass",
                    "severity": "warning",
                    "must_have_evidence": True,
                },
            ],
            actual=[
                {
                    "question_key": "critical_gap",
                    "status": "fail",
                    "severity": "critical",
                    "requires_evidence": True,
                    "evidence_validated": True,
                    "evidence_spans": [{"validation_status": "valid"}],
                },
                {
                    "question_key": "expected_pass",
                    "status": "fail",
                    "severity": "warning",
                    "requires_evidence": True,
                    "evidence_validated": True,
                    "evidence_spans": [{"validation_status": "valid"}],
                },
            ],
            errors=[{"type": "status_mismatch"}],
            passed=False,
            latency_ms=10,
        ),
        EvalCaseComparison(
            eval_case=SimpleNamespace(question_set_version_id=version_id),
            audit_run=None,
            expected=[
                {
                    "question_key": "missed_critical",
                    "expected_status": "fail",
                    "severity": "critical",
                    "must_have_evidence": True,
                }
            ],
            actual=[
                {
                    "question_key": "missed_critical",
                    "status": "needs_review",
                    "severity": "critical",
                    "requires_evidence": True,
                    "evidence_validated": False,
                    "evidence_spans": [{"validation_status": "invalid"}],
                }
            ],
            errors=[{"type": "status_mismatch"}, {"type": "unsupported_finding_trusted"}],
            passed=False,
            latency_ms=30,
        ),
    ]

    metrics = compute_eval_metrics(comparisons)

    assert metrics["total_cases"] == 2
    assert metrics["total_questions_evaluated"] == 3
    assert metrics["critical_issue_recall"] == 0.5
    assert metrics["false_positive_rate"] == 1
    assert metrics["unsupported_finding_rate"] == 0.3333
    assert metrics["evidence_span_match_rate"] == 0.6667
    assert metrics["insufficient_evidence_rate"] == 0
    assert metrics["regression_failures_by_question_set_version"] == {version_id: 2}
    assert metrics["average_audit_latency_ms"] == 20


def test_get_latest_eval_returns_newest_eval_run() -> None:
    reseed()
    client = TestClient(app)

    first = client.post("/evals/run", json={"limit": 1})
    second = client.post("/evals/run", json={"limit": 2})

    assert first.status_code == 200
    assert second.status_code == 200
    latest = client.get("/evals/latest")
    assert latest.status_code == 200
    assert latest.json()["id"] == second.json()["eval_run_id"]
    assert len(latest.json()["results"]) == 2


def test_eval_filters_work_for_specialty_and_question_set_version() -> None:
    reseed()
    client = TestClient(app)
    with SessionLocal() as db:
        hospice_version = _version(db, "hospice-eligibility", "v1")

    specialty_response = client.post("/evals/run", json={"specialty": "behavioral_health"})
    assert specialty_response.status_code == 200
    assert specialty_response.json()["metrics"]["total_cases"] == 4

    version_response = client.post("/evals/run", json={"question_set_version_id": hospice_version.id})
    assert version_response.status_code == 200
    assert version_response.json()["metrics"]["total_cases"] == 9

    scenario_response = client.post("/evals/run", json={"scenario_type": "adversarial_invalid_evidence"})
    assert scenario_response.status_code == 200
    assert scenario_response.json()["metrics"]["total_cases"] == 3
