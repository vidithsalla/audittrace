from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from audittrace_api.db import get_db
from audittrace_api.models import QuestionSet, QuestionSetVersion
from audittrace_api.schemas import (
    QuestionResponse,
    QuestionSetRef,
    QuestionSetsResponse,
    QuestionSetSummary,
    QuestionSetVersionDetailResponse,
    QuestionSetVersionSummary,
)

router = APIRouter(prefix="/question-sets", tags=["question_sets"])


@router.get("", response_model=QuestionSetsResponse)
def list_question_sets(db: Session = Depends(get_db)) -> QuestionSetsResponse:
    question_sets = db.scalars(
        select(QuestionSet)
        .options(selectinload(QuestionSet.versions))
        .order_by(QuestionSet.specialty, QuestionSet.slug)
    ).all()

    return QuestionSetsResponse(
        question_sets=[
            QuestionSetSummary(
                id=question_set.id,
                slug=question_set.slug,
                name=question_set.name,
                specialty=question_set.specialty,
                versions=[
                    QuestionSetVersionSummary(
                        id=version.id,
                        version=version.version,
                        status=version.status,
                        change_summary=version.change_summary,
                    )
                    for version in sorted(question_set.versions, key=lambda item: item.version)
                ],
            )
            for question_set in question_sets
        ]
    )


@router.get("/{version_id}", response_model=QuestionSetVersionDetailResponse)
def get_question_set_version(version_id: str, db: Session = Depends(get_db)) -> QuestionSetVersionDetailResponse:
    version = db.scalar(
        select(QuestionSetVersion)
        .options(
            selectinload(QuestionSetVersion.questions),
            selectinload(QuestionSetVersion.question_set),
        )
        .where(QuestionSetVersion.id == version_id)
    )
    if version is None:
        raise HTTPException(status_code=404, detail="Question set version not found")

    return QuestionSetVersionDetailResponse(
        id=version.id,
        question_set=QuestionSetRef(
            id=version.question_set.id,
            slug=version.question_set.slug,
            name=version.question_set.name,
        ),
        version=version.version,
        status=version.status,
        questions=[
            QuestionResponse.model_validate(question)
            for question in sorted(version.questions, key=lambda item: item.question_key)
        ],
    )
