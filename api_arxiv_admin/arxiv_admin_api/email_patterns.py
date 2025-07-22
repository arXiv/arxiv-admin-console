"""Provides integration for the external user interface."""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import Optional, List

from sqlalchemy import select
from sqlalchemy.orm import Session
from pydantic import BaseModel

from arxiv.base import logging
from arxiv.db.models import t_arXiv_black_email, t_arXiv_white_email, t_arXiv_block_email
# from arxiv.auth.user_claims import ArxivUserClaims

from . import is_admin_user, get_db

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_admin_user)], prefix="/email_templates")


class EmailPatternModel(BaseModel):
    class Config:
        from_attributes = True
    id: str
    pass

pattern_tables = {
    "black": t_arXiv_black_email,
    "block": t_arXiv_block_email,
    "white": t_arXiv_white_email,
}


@router.get('/')
async def list_email_patterns(
        response: Response,
        _sort: Optional[str] = Query("short_name", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        pattern: Optional[str] = Query(None, description="Email pattern"),
        purpose: Optional[str] = Query("black", description="black, block or white"),
        session: Session = Depends(get_db)
    ) -> List[EmailPatternModel]:

    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    if purpose is None:
        purpose = "black"

    table = pattern_tables.get(purpose)
    if table is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid purpose {purpose}. Allowed values: black, block, white")
    order_columns = []
    if _sort:
        keys = _sort.split(",")
        for key in keys:
            if key == "id":
                key = "pattern"
            try:
                order_column = getattr(table, key)
                order_columns.append(order_column)
            except AttributeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid start or end index")
    query = select(table.c.pattern.label("id")).select_from(table)
    
    if pattern is not None:
        query = query.where(table.c.pattern.contains(pattern))

    for column in order_columns:
        if _order == "DESC":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    count_query = select(table.c.pattern).select_from(table)
    if pattern is not None:
        count_query = count_query.where(table.c.pattern.contains(pattern))
    
    count = len(session.execute(count_query).fetchall())
    response.headers['X-Total-Count'] = str(count)
    
    result_query = query.offset(_start).limit(_end - _start)
    result = [EmailPatternModel.model_validate({"id": item.id}) for item in session.execute(result_query).fetchall()]
    return result

