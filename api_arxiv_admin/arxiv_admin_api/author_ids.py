"""
arXiv author ID of user
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import Optional, List

from sqlalchemy.orm import Session
from pydantic import BaseModel

from arxiv.base import logging
from arxiv.db.models import AuthorIds

from . import get_db, is_any_user

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_any_user)], prefix="/author_ids")


class AuthorIDModel(BaseModel):

    id: Optional[int]  # User ID
    author_id: Optional[str]
    updated: Optional[datetime]

    class Config:
        from_attributes = True

    @staticmethod
    def base_query(session: Session) -> Query:
        """
        Returns a basic query for author IDs.
        """
        return session.query(
            AuthorIds.user_id.label("id"),
            AuthorIds.author_id,
            AuthorIds.updated,
        )

@router.get('/')
async def list_membership_institutions(
        response: Response,
        _sort: Optional[str] = Query("short_name", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        id: Optional[List[str]] = Query(None, description="User ID"),
        db: Session = Depends(get_db)
    ) -> List[AuthorIDModel]:
    query = AuthorIDModel.base_query(db)

    if id:
        query = query.filter(AuthorIds.user_id.in_(id))
    else:
        if _start < 0 or _end < _start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid start or end index")

        order_columns = []
        if _sort:
            keys = _sort.split(",")
            for key in keys:
                try:
                    order_column = getattr(AuthorIds, key)
                    order_columns.append(order_column)
                except AttributeError:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Invalid start or end index")

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [AuthorIDModel.model_validate(item) for item in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get('/{id:int}')
async def membership_institution_data(id: int, db: Session = Depends(get_db)) -> AuthorIDModel:
    item = AuthorIDModel.base_select(db).filter(AuthorIds.user_id == id).one_or_none()
    if item:
        return AuthorIDModel.model_validate(item)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
