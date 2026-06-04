from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Select, select
from sqlalchemy.orm import Session, joinedload

from audittrace_api.db import get_db
from audittrace_api.models import SyntheticDocument
from audittrace_api.schemas import DocumentDetailResponse, DocumentListItem, DocumentMetadata, DocumentsResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=DocumentsResponse)
def list_documents(
    specialty: str | None = Query(default=None),
    provider_id: str | None = Query(default=None),
    service_code: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> DocumentsResponse:
    stmt: Select[tuple[SyntheticDocument]] = (
        select(SyntheticDocument)
        .options(joinedload(SyntheticDocument.provider))
        .order_by(SyntheticDocument.date_of_service.desc(), SyntheticDocument.title)
    )
    if specialty:
        stmt = stmt.where(SyntheticDocument.specialty == specialty)
    if provider_id:
        stmt = stmt.where(SyntheticDocument.provider_id == provider_id)
    if service_code:
        stmt = stmt.where(SyntheticDocument.service_code == service_code)

    documents = db.scalars(stmt).all()
    return DocumentsResponse(
        documents=[
            DocumentListItem(
                id=document.id,
                title=document.title,
                provider_id=document.provider_id,
                provider_name=document.provider.name,
                specialty=document.specialty,
                service_code=document.service_code,
                state=document.state,
                date_of_service=document.date_of_service,
                note_type=document.note_type,
            )
            for document in documents
        ]
    )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
def get_document(document_id: str, db: Session = Depends(get_db)) -> DocumentDetailResponse:
    document = db.scalar(
        select(SyntheticDocument)
        .options(joinedload(SyntheticDocument.provider))
        .where(SyntheticDocument.id == document_id)
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentDetailResponse(
        id=document.id,
        title=document.title,
        metadata=DocumentMetadata(
            provider_id=document.provider_id,
            provider_name=document.provider.name,
            specialty=document.specialty,
            service_code=document.service_code,
            payer=document.payer,
            state=document.state,
            date_of_service=document.date_of_service,
            note_type=document.note_type,
        ),
        body=document.body,
    )
