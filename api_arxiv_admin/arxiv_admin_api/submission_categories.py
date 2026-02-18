"""arXiv submission routes."""
from typing import Optional, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from pydantic import BaseModel, ConfigDict
from arxiv.base import logging
from arxiv.db.models import SubmissionCategory

from . import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/submission_categories")

class SubmissionCategoryModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    model_config = ConfigDict(from_attributes=True)

    id: int
    categories: List[SubmissionCategoryModel]

    pass

@router.get('/{id:int}')
async def get_submission_categories(id: int,
                                    db: Session = Depends(get_db)) -> SubmissionCategoryResultModel:
    cats = SubmissionCategoryModel.base_select(db).filter(SubmissionCategory.submission_id == id).order_by(SubmissionCategory.is_primary.desc()).all()
    categories = [SubmissionCategoryModel.model_validate(item) for item in cats]
    result = SubmissionCategoryResultModel(id=id, categories=categories)
    return result
