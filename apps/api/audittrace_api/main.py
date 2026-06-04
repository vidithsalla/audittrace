from fastapi import FastAPI

from audittrace_api.db import init_db
from audittrace_api.routes.audits import router as audits_router
from audittrace_api.routes.documents import router as documents_router
from audittrace_api.routes.evals import router as evals_router
from audittrace_api.routes.question_sets import router as question_sets_router
from audittrace_api.schemas import HealthResponse


def create_app() -> FastAPI:
    init_db()
    app = FastAPI(
        title="AuditTrace API",
        description="Synthetic AI audit reliability backend. Uses fictional seed data only.",
        version="0.1.0",
    )

    @app.get("/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="audittrace-api")

    app.include_router(documents_router)
    app.include_router(question_sets_router)
    app.include_router(audits_router)
    app.include_router(evals_router)
    return app


app = create_app()
