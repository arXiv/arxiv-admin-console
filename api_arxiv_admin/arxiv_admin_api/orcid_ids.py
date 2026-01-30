"""
ORCID ID of user
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import Optional, List

from sqlalchemy.orm import Session, Query as OrmQuery
from pydantic import BaseModel

from arxiv.base import logging
from arxiv.db.models import OrcidIds

from . import get_db, is_any_user

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_any_user)], prefix="/orcid_ids")


class OrcidIDModel(BaseModel):

    id: Optional[int]  # User ID
    orcid: Optional[str]
    authenticated: Optional[bool]
    updated: Optional[datetime]

    class Config:
        from_attributes = True

    @staticmethod
    def base_query(session: Session) -> OrmQuery:
        """
        Returns a basic query for ORCID IDs.
        """
        return session.query(
            OrcidIds.user_id.label("id"),
            OrcidIds.orcid,
            OrcidIds.authenticated,
            OrcidIds.updated,
        )

@router.get('/')
async def list_membership_institutions(
        response: Response,
        _sort: Optional[str] = Query("short_name", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        id: Optional[List[int]] = Query(None, description="User ID"),
        db: Session = Depends(get_db)
    ) -> List[OrcidIDModel]:
    query = OrcidIDModel.base_query(db)

    if id:
        query = query.filter(OrcidIds.user_id.in_(id))
    else:
        if _start < 0 or _end < _start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid start or end index")

        order_columns = []
        if _sort:
            keys = _sort.split(",")
            for key in keys:
                if key == "id":
                    key = "user_id"
                try:
                    order_column = getattr(OrcidIds, key)
                    order_columns.append(order_column)
                except AttributeError:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Invalid start or end index")

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [OrcidIDModel.model_validate(item) for item in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get('/{id:int}')
async def membership_institution_data(id: int, db: Session = Depends(get_db)) -> OrcidIDModel:
    item = OrcidIDModel.base_query(db).filter(OrcidIds.user_id == id).one_or_none()
    if item:
        return OrcidIDModel.model_validate(item)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
