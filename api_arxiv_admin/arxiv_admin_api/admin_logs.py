"""arXiv admin routes."""
import re
from datetime import timedelta, datetime, date
from typing import Optional, List

from arxiv.auth.user_claims import ArxivUserClaims
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response

from sqlalchemy import select, update, func, case, Select, distinct, exists, and_
from sqlalchemy.orm import Session, joinedload

from pydantic import BaseModel
from arxiv.base import logging
from arxiv.db.models import AdminLog

from . import get_db, datetime_to_epoch, VERY_OLDE, is_any_user, get_current_user, is_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin_logs", dependencies=[Depends(is_any_user)])


class AdminLogModel(BaseModel):
    class Config:
        from_attributes = True

    id: int
    logtime: Optional[str] = None
    created: datetime
    paper_id: Optional[str] = None
    username: Optional[str] = None
    host: Optional[str] = None
    program: Optional[str] = None
    command: Optional[str] = None
    logtext: Optional[str] = None
    document_id: Optional[int] = None
    submission_id: Optional[int] = None
    notify: Optional[int] = None

    @staticmethod
    def base_select(db: Session):

        return db.query(
            AdminLog.id,
            AdminLog.logtime,
        AdminLog.created,
        AdminLog.paper_id,
        AdminLog.username,
        AdminLog.host,
        AdminLog.program,
        AdminLog.command,
        AdminLog.logtext,
        AdminLog.document_id,
        AdminLog.submission_id,
        AdminLog.notify
        )
    pass



@router.get('/')
async def list_admin_logs(
        response: Response,
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        submission_id: Optional[int] = Query(None, alias="submission_id"),
        paper_id: Optional[str] = Query(None, alias="paper_id"),
        start_date: Optional[date] = Query(None, description="Start date for filtering"),
        end_date: Optional[date] = Query(None, description="End date for filtering"),
        _is_admin_user: ArxivUserClaims = Depends(is_admin_user),
        db: Session = Depends(get_db),

    ) -> List[AdminLogModel]:
    query = AdminLogModel.base_select(db)

    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    if submission_id:
        query = query.filter(AdminLog.submission_id == submission_id)

    if paper_id:
        query = query.filter(AdminLog.paper_id == paper_id)

    order_columns = []
    if _sort:
        keys = _sort.split(",")
        for key in keys:
            try:
                order_column = getattr(AdminLog, key)
                order_columns.append(order_column)
            except AttributeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid start or end index")

    t0 = datetime.now()

    if start_date or end_date:
        t_begin = datetime_to_epoch(start_date, VERY_OLDE)
        t_end = datetime_to_epoch(end_date, date.today(), hour=23, minute=59, second=59)
        query = query.filter(AdminLog.issued_when.between(t_begin, t_end))


    for column in order_columns:
        if _order == "DESC":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [AdminLogModel.model_validate(item) for item in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get('/{id:int}')
async def get_admin_log(id: int,
                        _is_admin_user: ArxivUserClaims = Depends(is_admin_user),
                        current_user: ArxivUserClaims = Depends(get_current_user),
                        db: Session = Depends(get_db)) -> AdminLogModel:
    item: AdminLog = AdminLogModel.base_select(db).filter(AdminLog.id == id).one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin log is not found.")

    if current_user.user_id != item.id and (not (current_user.is_admin or current_user.is_mod)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
    return AdminLogModel.model_validate(item)


@router.put('/{id:int}', dependencies=[Depends(is_any_user)])
async def update_admin_log(
        request: Request,
        id: int,
        _is_admin_user: ArxivUserClaims = Depends(is_admin_user),
        session: Session = Depends(get_db)) -> AdminLogModel:
    body = await request.json()

    item = session.query(AdminLog).filter(AdminLog.id == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Admin log not found")

    #
    flag_open = body.gep("flag_open")
    if flag_open == False and item.point_value == 0:
        item.point_value = 10

    item.flag_valid = body.gep("flag_valid", item.flag_valid)
    session.commit()
    session.refresh(item)  # Refresh the instance with the updated data
    updated = AdminLogModel.base_select(session).filter(AdminLog.id == id).one_or_none()
    return AdminLogModel.model_validate(updated)


@router.post('/')
async def create_admin_log(
        request: Request,
        _is_admin_user: ArxivUserClaims = Depends(is_admin_user),
        session: Session = Depends(get_db)) -> AdminLogModel:
    body = await request.json()
    # ID is decided after added
    if "id" in body:
        del body["id"]

    item = AdminLog(**body)
    session.add(item)
    session.commit()
    session.refresh(item)
    return AdminLogModel.model_validate(item)


@router.delete('/{id:int}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin_log(
        id: int,
        _is_admin_user: ArxivUserClaims = Depends(is_admin_user),
        current_user: ArxivUserClaims = Depends(get_current_user),
        session: Session = Depends(get_db)) -> Response:

    item: AdminLog = session.query(AdminLog).filter(AdminLog.id == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.user_id != item.endorsee_id and (not (current_user.is_admin or current_user.is_mod)):
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    item.delete_instance()
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
