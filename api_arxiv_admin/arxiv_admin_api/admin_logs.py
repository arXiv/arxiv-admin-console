"""arXiv admin routes."""

from datetime import datetime, date
from typing import Optional, List

from arxiv.auth.user_claims import ArxivUserClaims
from arxiv_bizlogic.audit_event import admin_audit, AdminAudit_AddComment
from arxiv_bizlogic.fastapi_helpers import get_authn, get_authn_user, get_tapir_tracking_cookie, get_client_host, \
    get_client_host_name
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response

from sqlalchemy.orm import Session

from pydantic import BaseModel
from arxiv.base import logging
from arxiv.db.models import AdminLog, Submission

from . import get_db, datetime_to_epoch, VERY_OLDE, is_any_user, is_admin_user

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
        _start: Optional[int] = Query(0),
        _end: Optional[int] = Query(100),
        submission_id: Optional[int] = Query(None, description="arXid Submission ID"),
        paper_id: Optional[str] = Query(None, description="arXid Paper ID"),
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
        if submission_id is None:
            # Second query: join with submissions where doc_paper_id matches
            query2 = AdminLogModel.base_select(db).join(
                Submission, AdminLog.submission_id == Submission.submission_id,
                isouter=True
            ).filter(Submission.doc_paper_id == paper_id)

            # Union the queries - need to convert to subqueries first
            query = query.union(query2)

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

    if start_date or end_date:
        t_begin = datetime_to_epoch(start_date, VERY_OLDE)
        t_end = datetime_to_epoch(end_date, date.today(), hour=23, minute=59, second=59)
        query = query.filter(AdminLog.logtime.between(t_begin, t_end))


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
                        current_user: ArxivUserClaims = Depends(get_authn_user),
                        db: Session = Depends(get_db)) -> AdminLogModel:
    item: AdminLog = AdminLogModel.base_select(db).filter(AdminLog.id == id).one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin log is not found.")

    if current_user.user_id != item.id and (not (current_user.is_admin or current_user.is_mod)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")
    return AdminLogModel.model_validate(item)



class AdminUserComment(BaseModel):
    class Config:
        from_attributes = True
    user_id: str
    comment: str

@router.post('/user_comment')
async def create_admin_log_user_comment(
        body: AdminUserComment,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        session: Session = Depends(get_db),
        remote_ip: Optional[str] = Depends(get_client_host),
        remote_hostname: Optional[str] = Depends(get_client_host_name),
        tracking_cookie: Optional[str] = Depends(get_tapir_tracking_cookie),
        ) -> AdminLogModel:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    admin_audit(
        session,
        AdminAudit_AddComment(
            current_user.user_id,
            body.user_id,
            current_user.tapir_session_id,
            comment=body.comment,
            remote_ip=remote_ip,
            remote_hostname=remote_hostname,
            tracking_cookie=tracking_cookie,
        )
    )

