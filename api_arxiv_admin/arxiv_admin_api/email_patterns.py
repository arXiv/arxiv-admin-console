"""Provides integration for the external user interface."""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import Optional, List

from sqlalchemy import select, delete, insert
from sqlalchemy.orm import Session
from pydantic import BaseModel

from arxiv.base import logging
from arxiv.db.models import t_arXiv_black_email, t_arXiv_white_email, t_arXiv_block_email
# from arxiv.auth.user_claims import ArxivUserClaims

from . import is_admin_user, get_db

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_admin_user)], prefix="/email_patterns")


class EmailPatternModel(BaseModel):
    class Config:
        from_attributes = True
    id: str
    purpose: str
    pass

pattern_tables = {
    "black": t_arXiv_black_email,
    "block": t_arXiv_block_email,
    "white": t_arXiv_white_email,
}


@router.get('/')
async def list_email_patterns(
        response: Response,
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
    if _order:
        order_columns.append(table.c.pattern)

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
    result = [EmailPatternModel.model_validate({"id": item.id, "purpose": purpose}) for item in session.execute(result_query).fetchall()]
    return result


@router.post('/')
async def create_email_pattern(
        body: EmailPatternModel,
        session: Session = Depends(get_db)
) -> EmailPatternModel:

    table = pattern_tables.get(body.purpose)
    if table is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid purpose {body.purpose}. Allowed values: black, block, white")

    if not body.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Pattern ID is required")

    try:
        # Check if pattern already exists
        existing_query = select(table.c.pattern).where(table.c.pattern == body.id)
        existing = session.execute(existing_query).fetchone()
        
        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail=f"Email pattern '{body.id}' already exists in {body.purpose} table")

        # Insert new pattern
        insert_query = insert(table).values(pattern=body.id)
        session.execute(insert_query)
        session.commit()
        
        logger.info(f"Created email pattern '{body.id}' in {body.purpose} table")
        
        return body
    
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating email pattern: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to create email pattern")


class EmailPatternListModel(BaseModel):
    class Config:
        from_attributes = True
    ids: List[str]


@router.delete('/{purpose:str}')
async def delete_email_patterns(
        response: Response,
        purpose: str,
        body: EmailPatternListModel,
        session: Session = Depends(get_db)
) -> Response:

    table = pattern_tables.get(purpose)
    if table is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Invalid purpose {purpose}. Allowed values: black, block, white")

    if not body.ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="No pattern IDs provided")

    try:
        delete_query = delete(table).where(table.c.pattern.in_(body.ids))
        result = session.execute(delete_query)
        session.commit()
        
        logger.info(f"Deleted {result.rowcount} email patterns from {purpose} table")
        
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting email patterns: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Failed to delete email patterns")

