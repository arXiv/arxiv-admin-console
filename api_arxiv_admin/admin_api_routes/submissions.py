"""arXiv paper display routes."""
from arxiv.auth.user_claims import ArxivUserClaims
from fastapi import APIRouter, Depends, HTTPException, Request, Query, Response, status
from typing import Optional, List
from arxiv.base import logging
from arxiv.db.models import Submission, SubmissionCategory
from sqlalchemy.orm import Session
from sqlalchemy import select, update, func, case, Select, distinct, exists, and_
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from .submission_categories import SubmissionCategoryModel
import re

from . import is_admin_user, get_db, datetime_to_epoch, VERY_OLDE, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/submissions", dependencies=[Depends(is_admin_user)])
meta_router = APIRouter(prefix="/submissions/metadata")

class SubmissionStatusModel(BaseModel):
    id: int
    name: str

_VALID_STATUS_LIST: List[SubmissionStatusModel] = [
    SubmissionStatusModel(id=0, name="Working"),
    SubmissionStatusModel(id=1, name="Submitted"),
    SubmissionStatusModel(id=2, name="On hold"),
    SubmissionStatusModel(id=3, name="Unused"),
    SubmissionStatusModel(id=4, name="Next"),
    SubmissionStatusModel(id=5, name="Processing"),
    SubmissionStatusModel(id=6, name="Needs_email"),
    SubmissionStatusModel(id=7, name="Published"),
    SubmissionStatusModel(id=8, name="Processing(submitting)"),
    SubmissionStatusModel(id=9, name="Removed"),
    SubmissionStatusModel(id=10, name="User deleted"),
    SubmissionStatusModel(id=19, name="Error state"),
    SubmissionStatusModel(id=20, name='Deleted(working)'),
    SubmissionStatusModel(id=22, name='Deleted(on hold)'),
    SubmissionStatusModel(id=25, name='Deleted(processing)'),
    SubmissionStatusModel(id=27, name='Deleted(published)'),
    SubmissionStatusModel(id=29, name="Deleted(removed)"),
    SubmissionStatusModel(id=30, name='Deleted(user deleted)'),
]


VALID_STATUS_LIST = {entry.id : entry.name for entry in _VALID_STATUS_LIST}


class SubmissionModel(BaseModel):
    id: int  # submission_id: intpk]
    document_id: Optional[int] #  = mapped_column(ForeignKey('arXiv_documents.document_id', ondelete='CASCADE', onupdate='CASCADE'), index=True)
    doc_paper_id: Optional[str] # = mapped_column(String(20), index=True)
    sword_id: Optional[int] # = mapped_column(ForeignKey('arXiv_tracking.sword_id'), index=True)
    userinfo: Optional[int] # = mapped_column(Integer, server_default=FetchedValue())
    is_author: int # = mapped_column(Integer, nullable=False, server_default=text("'0'"))
    agree_policy: Optional[int] # = mapped_column(Integer, server_default=FetchedValue())
    viewed: Optional[int] # = mapped_column(Integer, server_default=FetchedValue())
    stage: Optional[int] # = mapped_column(Integer, server_default=FetchedValue())
    submitter_id: Optional[int] # = mapped_column(ForeignKey('tapir_users.user_id', ondelete='CASCADE', onupdate='CASCADE'), index=True)
    submitter_name: Optional[str] # = mapped_column(String(64))
    submitter_email: Optional[str] # = mapped_column(String(64))
    created: Optional[datetime]
    updated: Optional[datetime]
    status: int # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    sticky_status: Optional[int] # = mapped_column(Integer)
    must_process: Optional[int] # = mapped_column(Integer, server_default=FetchedValue())
    submit_time: Optional[datetime]
    release_time: Optional[datetime]
    source_size: Optional[int] # = mapped_column(Integer, server_default=FetchedValue())
    source_format: Optional[str] # = mapped_column(String(12))
    source_flags: Optional[str] # = mapped_column(String(12))
    has_pilot_data: Optional[int] # = mapped_column(Integer)
    is_withdrawn: int # = mapped_column(Integer, nullable=False, server_default=text("'0'"))
    title: Optional[str] # = mapped_column(Text)
    authors: Optional[str] # = mapped_column(Text)
    comments: Optional[str] # = mapped_column(Text)
    proxy: Optional[str]
    report_num: Optional[str] # = mapped_column(Text)
    msc_class: Optional[str]
    acm_class: Optional[str]
    journal_ref: Optional[str] # = mapped_column(Text)
    doi: Optional[str]
    abstract: Optional[str] # = mapped_column(Text)
    license: Optional[str] # = mapped_column(ForeignKey('arXiv_licenses.name', onupdate='CASCADE'), index=True)
    version: int # = mapped_column(Integer, nullable=False, server_default=text("'1'"))
    type: Optional[str] # = mapped_column(String(8), index=True)
    is_ok: Optional[int] # = mapped_column(Integer, index=True)
    admin_ok: Optional[int] # = mapped_column(Integer)
    allow_tex_produced: Optional[int] # = mapped_column(Integer, server_default=FetchedValue())
    is_oversize: Optional[int] # = mapped_column(Integer, server_default=FetchedValue())
    remote_addr: str # = mapped_column(String(16), nullable=False, server_default=FetchedValue())
    remote_host: str # = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    package: str # = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    rt_ticket_id: Optional[int] # = mapped_column(Integer, index=True)
    auto_hold: Optional[int] # = mapped_column(Integer, server_default=FetchedValue())
    is_locked: int # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    agreement_id: Optional[int] # mapped_column(ForeignKey('arXiv_submission_agreements.agreement_id'), index=True)
    submission_categories: Optional[List[SubmissionCategoryModel]]

    class Config:
        from_attributes = True

    @staticmethod
    def base_select(db: Session):
        return db.query(
            Submission.submission_id.label("id"),
            Submission.document_id,
            Submission.doc_paper_id,
            Submission.sword_id,
            Submission.userinfo,
            Submission.is_author,
            Submission.agree_policy,
            Submission.viewed,
            Submission.stage,
            Submission.submitter_id,
            Submission.submitter_name,
            Submission.submitter_email,
            Submission.created,
            Submission.updated,
            Submission.status,
            Submission.sticky_status,
            Submission.must_process,
            Submission.submit_time,
            Submission.release_time,
            Submission.source_size,
            Submission.source_format,
            Submission.source_flags,
            Submission.has_pilot_data,
            Submission.is_withdrawn,
            Submission.title,
            Submission.authors,
            Submission.comments,
            Submission.proxy,
            Submission.report_num,
            Submission.msc_class,
            Submission.acm_class,
            Submission.journal_ref,
            Submission.doi,
            Submission.abstract,
            Submission.license,
            Submission.version,
            Submission.type,
            Submission.is_ok,
            Submission.admin_ok,
            Submission.allow_tex_produced,
            Submission.is_oversize,
            Submission.remote_addr,
            Submission.remote_host,
            Submission.package,
            Submission.rt_ticket_id,
            Submission.auto_hold,
            Submission.is_locked,
            Submission.agreement_id
        )


@router.get('/')
async def list_submissions(
        response: Response,
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        preset: Optional[str] = Query(None),
        start_date: Optional[date] = Query(None, description="Start date for filtering"),
        end_date: Optional[date] = Query(None, description="End date for filtering"),
        stage: Optional[List[int]] = Query(None, description="Stage"),
        submission_status: Optional[List[int]] = Query(None, description="Submission status"),
        id: Optional[List[int]] = Query(None, description="List of user IDs to filter by"),
        document_id: Optional[int] = Query(None, description="Document ID"),
        submitter_id: Optional[int] = Query(None, description="Submitter ID"),
        db: Session = Depends(get_db)
    ) -> List[SubmissionModel]:
    query = SubmissionModel.base_select(db)

    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    t0 = datetime.now()

    order_columns = []
    if _sort:
        keys = _sort.split(",")
        for key in keys:
            if key == "id":
                key = "submission_id"
            try:
                order_column = getattr(Submission, key)
                order_columns.append(order_column)
            except AttributeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid start or end index")

    if id is not None:
        query = query.filter(Submission.submission_id.in_(id))
    else:
        if submission_status is not None:
            if isinstance(submission_status, list):
                query = query.filter(Submission.status.in_(submission_status))
            else:
                query = query.filter(Submission.status == submission_status)

        if stage is not None:
            query = query.filter(Submission.stage.in_(stage))

        if document_id is not None:
            query = query.filter(Submission.document_id == document_id)

        if submitter_id is not None:
            query = query.filter(Submission.submitter_id == submitter_id)

        if preset is not None:
            matched = re.search(r"last_(\d+)_days", preset)
            if matched:
                t_begin = t0 - timedelta(days=int(matched.group(1)))
                t_end = t0
                query = query.filter(Submission.submit_time.between(t_begin, t_end))
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid preset format")
        else:
            if start_date or end_date:
                t_begin = start_date if start_date else VERY_OLDE
                # t_end = datetime_to_epoch(end_date, date.today(), hour=23, minute=59, second=59)
                t_end = end_date if end_date else datetime.now()
                query = query.filter(Submission.submit_time.between(t_begin, t_end))

    for column in order_columns:
        if _order == "DESC":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [SubmissionModel.from_orm(item) for item in query.offset(_start).limit(_end - _start).all()]
    for sub in result:
        sub.submission_categories = [SubmissionCategoryModel.from_orm(cat) for cat in SubmissionCategoryModel.base_select(db).filter(SubmissionCategory.submission_id == sub.id).all()]
    return result


@router.get("/paper/{paper_id:str}")
async def get_submission_by_paper_id(
        paper_id:str,
        session: Session = Depends(get_db)) -> SubmissionModel:
    """Display a paper."""
    query = SubmissionModel.base_select(session).filter(Submission.doc_paper_id == paper_id)
    doc = query.one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Paper not found")
    return doc

@router.get("/{id:int}")
async def get_submission(
        id:int,
        session: Session = Depends(get_db)) -> SubmissionModel:
    """Display a paper."""
    sub = SubmissionModel.base_select(session).filter(Submission.submission_id == id).one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    submission: SubmissionModel = SubmissionModel.from_orm(sub)
    submission.submission_categories = [SubmissionCategoryModel.from_orm(cat) for cat in SubmissionCategoryModel.base_select(session).filter(SubmissionCategory.submission_id == id).all()]
    return submission


@router.put("/{id:int}", response_model=SubmissionModel)
async def update_submission(
        request: Request,
        id: int,
        session: Session = Depends(get_db)):
    """Display a paper."""
    sub = SubmissionModel.base_select(session).filter(Submission.submission_id == id).one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Paper not found")
    body = await request.body()
    status = body.get("status")
    if status in VALID_STATUS_LIST:
        sub.status = status

    return SubmissionModel.from_orm(sub)

@router.get("/document/{document_id:str}")
async def get_submission_by_document_id(
        document_id: str,
        session: Session = Depends(get_db)) -> SubmissionModel:
    """Display a paper."""
    query = SubmissionModel.base_select(session).filter(Submission.document_id == document_id)
    doc = query.one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


def is_good():
    return True

@meta_router.get("/status-list")
async def list_submission_status() -> List[SubmissionStatusModel]:
    return _VALID_STATUS_LIST

