"""arXiv submission routes."""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response

from sqlalchemy import select, update, func, case, Select, distinct, exists, and_
from sqlalchemy.orm import Session, joinedload

from pydantic import BaseModel
from arxiv.base import logging
from arxiv.db import transaction
from arxiv.db.models import Submission, Demographic, TapirUser, Category, SubmissionCategory

from . import get_db, is_any_user, get_current_user, is_admin_user
from .categories import CategoryModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/submission_categories", dependencies=[Depends(is_admin_user)])

class SubmissionCategoryModel(BaseModel):
    class Config:
        from_attributes = True

    category: str
    is_primary: bool
    is_published: Optional[bool]

    @staticmethod
    def base_select(db: Session):
        return db.query(
            SubmissionCategory.category,
            SubmissionCategory.is_primary,
            SubmissionCategory.is_published
        )


class SubmissionCategoryResultModel(BaseModel):
    class Config:
        from_attributes = True

    id: int
    categories: List[SubmissionCategoryModel]

    pass

@router.get('/{id:int}')
async def get_submission_categories(id: int,
                                    db: Session = Depends(get_db)) -> SubmissionCategoryResultModel:
    cats = SubmissionCategoryModel.base_select(db).filter(SubmissionCategory.submission_id == id).order_by(SubmissionCategory.is_primary.desc()).all()
    categories = [SubmissionCategoryModel.from_orm(item) for item in cats]
    result = SubmissionCategoryResultModel(id=id, categories=categories)
    return result
