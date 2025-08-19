"""arXiv paper display routes."""
import re
from datetime import datetime, date, timedelta
from enum import Enum, IntEnum
from typing import Optional, List, Union

from arxiv.auth.user_claims import ArxivUserClaims
from arxiv.base import logging
from arxiv.db.models import Submission, SubmissionCategory
from arxiv_bizlogic.fastapi_helpers import get_authn
from arxiv_bizlogic.latex_helpers import convert_latex_accents
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status as http_status
from pydantic import BaseModel, field_validator
from sqlalchemy import text, cast, LargeBinary, Row, and_  # select, update, func, case, Select, distinct, exists, and_
from sqlalchemy.orm import Session

from . import get_db, VERY_OLDE, is_any_user
from .helpers.mui_datagrid import MuiDataGridFilter
from .submission_categories import SubmissionCategoryModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/submissions", dependencies=[Depends(is_any_user)])
meta_router = APIRouter(prefix="/submissions/metadata")

class SubmissionStatusModel(BaseModel):
    id: int
    name: str
    group: str

_VALID_STATUS_LIST: List[SubmissionStatusModel] = [
    # WORKING
    SubmissionStatusModel(id=0, name="Working", group="current"),

    # SUBMITTED
    SubmissionStatusModel(id=1, name="Submitted", group="current"),

    # ON_HOLD
    SubmissionStatusModel(id=2, name="On hold", group="current"),
    SubmissionStatusModel(id=3, name="Unused", group="unuesd"),

    # NEXT = "4"
    SubmissionStatusModel(id=4, name="Next", group="current"),
    SubmissionStatusModel(id=5, name="Processing", group="processing"),
    SubmissionStatusModel(id=6, name="Needs_email", group="processing"),
    SubmissionStatusModel(id=7, name="Published", group="accepted"),

    # STUCK = "8"
    SubmissionStatusModel(id=8, name="Stuck", group="accepted"),

    # REMOVED = "9"
    SubmissionStatusModel(id=9, name="Removed", group="invalid"),
    SubmissionStatusModel(id=10, name="User deleted", group="invalid"),
    SubmissionStatusModel(id=19, name="Error state", group="invalid"),
    SubmissionStatusModel(id=20, name='Deleted(working)', group='expired'),
    SubmissionStatusModel(id=22, name='Deleted(on hold)', group='expired'),
    SubmissionStatusModel(id=25, name='Deleted(processing)', group='expired'),
    SubmissionStatusModel(id=27, name='Deleted(published)', group='expired'),
    SubmissionStatusModel(id=29, name="Deleted(removed)", group='expired'),
    SubmissionStatusModel(id=30, name='Deleted(user deleted)', group='expired'),
]


VALID_STATUS_LIST = {entry.id : entry.name for entry in _VALID_STATUS_LIST}


class SubmissionType(str, Enum):
    cross = "cross"
    jref = "jref"
    new = "new"
    rep = "rep"
    wdr = "wdr"

class IsAuthorEnum(IntEnum):
    unknown = 0
    original_submitter = 1
    proxy_submitter = 2


class SubmissionModel(BaseModel):
    id: int  # submission_id: intpk]
    document_id: Optional[int] = None #  = mapped_column(ForeignKey('arXiv_documents.document_id', ondelete='CASCADE', onupdate='CASCADE'), index=True)
    doc_paper_id: Optional[str] = None # = mapped_column(String(20), index=True)
    sword_id: Optional[int] = None  # = mapped_column(ForeignKey('arXiv_tracking.sword_id'), index=True)
    userinfo: Optional[int] = None  # = mapped_column(Integer, server_default=FetchedValue())
    is_author: IsAuthorEnum # = mapped_column(Integer, nullable=False, server_default=text("'0'"))
    agree_policy: Optional[bool] = None  # = mapped_column(Integer, server_default=FetchedValue())
    viewed: Optional[bool] = None  # = mapped_column(Integer, server_default=FetchedValue())
    stage: Optional[int] = None  # = mapped_column(Integer, server_default=FetchedValue())
    submitter_id: Optional[int] = None  # = mapped_column(ForeignKey('tapir_users.user_id', ondelete='CASCADE', onupdate='CASCADE'), index=True)
    submitter_name: Optional[str] = None  # = mapped_column(String(64))
    submitter_email: Optional[str] = None  # = mapped_column(String(64))
    created: Optional[datetime] = None
    updated: Optional[datetime] = None
    status: int # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    sticky_status: Optional[int] = None  # = mapped_column(Integer)
    must_process: Optional[bool] = None  # = mapped_column(Integer, server_default=FetchedValue())
    submit_time: Optional[datetime] = None
    release_time: Optional[datetime] = None
    source_size: Optional[int] = None  # = mapped_column(Integer, server_default=FetchedValue())
    source_format: Optional[str] = None  # = mapped_column(String(12))
    source_flags: Optional[str] = None  # = mapped_column(String(12))
    has_pilot_data: Optional[bool] = None  # = mapped_column(Integer)
    is_withdrawn: bool # = mapped_column(Integer, nullable=False, server_default=text("'0'"))
    title: Optional[str] = None  # = mapped_column(Text)
    authors: Optional[str] = None  # = mapped_column(Text)
    comments: Optional[str] = None  # = mapped_column(Text)
    proxy: Optional[str] = None
    report_num: Optional[str] = None  # = mapped_column(Text)
    msc_class: Optional[str] = None
    acm_class: Optional[str] = None
    journal_ref: Optional[str] = None  # = mapped_column(Text)
    doi: Optional[str] = None
    abstract: Optional[str] = None  # = mapped_column(Text)
    license: Optional[str] = None  # = mapped_column(ForeignKey('arXiv_licenses.name', onupdate='CASCADE'), index=True)
    version: int # = mapped_column(Integer, nullable=False, server_default=text("'1'"))
    type: Optional[SubmissionType] = None  # = mapped_column(String(8), index=True)
    is_ok: Optional[bool] = None  # = mapped_column(Integer, index=True)
    admin_ok: Optional[bool] = None  # = mapped_column(Integer)
    allow_tex_produced: Optional[bool] = None  # = mapped_column(Integer, server_default=FetchedValue())
    is_oversize: Optional[bool] = None  # = mapped_column(Integer, server_default=FetchedValue())
    remote_addr: str # = mapped_column(String(16), nullable=False, server_default=FetchedValue())
    remote_host: str # = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    package: str # = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    rt_ticket_id: Optional[int] = None  # = mapped_column(Integer, index=True)
    auto_hold: Optional[bool] = None  # = mapped_column(Integer, server_default=FetchedValue())
    is_locked: int # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    agreement_id: Optional[int] = None  # mapped_column(ForeignKey('arXiv_submission_agreements.agreement_id'), index=True)
    submission_categories: Optional[List[SubmissionCategoryModel]] = None

    data_version: Optional[int] = None
    metadata_version: int
    data_needed: bool
    data_version_queued: bool
    metadata_version_queued: bool
    data_queued_time: Optional[datetime] = None
    metadata_queued_time: Optional[datetime] = None
    preflight: Optional[bool] = None

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
            cast(Submission.submitter_name, LargeBinary).label("submitter_name"),
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
            cast(Submission.title, LargeBinary).label("title"),
            cast(Submission.authors, LargeBinary).label("authors"),
            cast(Submission.comments, LargeBinary).label("comments"),
            Submission.proxy,
            Submission.report_num,
            Submission.msc_class,
            Submission.acm_class,
            Submission.journal_ref,
            Submission.doi,
            cast(Submission.abstract, LargeBinary).label("abstract"),
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
            Submission.agreement_id,
            Submission.data_version,
            Submission.metadata_version,
            Submission.data_needed,
            Submission.data_version_queued,
            Submission.metadata_version_queued,
            Submission.data_queued_time,
            Submission.metadata_queued_time,
            Submission.preflight,
        )

    @staticmethod
    def to_model(sub: Submission | Row, session: Session) -> "SubmissionModel":
        if hasattr(sub, "_asdict"):  # It's a Row
            row = sub._asdict()
        else:  # It's a model instance
            row = sub.__dict__.copy()
        for field in ["submitter_name", "title", "authors", "comments", "abstract"]:
            row[field] = convert_latex_accents(row[field].decode("utf-8")) if row[field] else None
        sub_id = row.get("id")
        subm = SubmissionModel.model_validate(row)
        subm.submission_categories = [SubmissionCategoryModel.model_validate(cat) for cat in
                                      SubmissionCategoryModel.base_select(session).filter(
                                      SubmissionCategory.submission_id == sub_id).all()]
        return subm

    @field_validator('is_author')
    @classmethod
    def validate_is_author(cls, value):
        if isinstance(value, (str, int)) and not isinstance(value, IsAuthorEnum):
            try:
                return IsAuthorEnum(value)
            except ValueError:
                try:
                    return IsAuthorEnum[value]
                except KeyError:
                    raise ValueError(f"Invalid is_author value: {value}")
        return value


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
        submission_status: Optional[Union[int,List[int]]] = Query(
            None, description="Submission status"),
        submission_status_group: Optional[Union[str,List[str]]] = Query(
            None, description="Submission status group [current|processing|accepted|expired]"),
        title_like: Optional[str]= Query(None, description="Title"),
        type: Optional[List[str]] = Query(None, description="Submission Type list"),
        id: Optional[List[int]] = Query(None, description="List of user IDs to filter by"),
        document_id: Optional[int] = Query(None, description="Document ID"),
        submitter_id: Optional[int] = Query(None, description="Submitter ID"),
        filter: Optional[str] = Query(None, description="MUI DataGrid Filter"),
        start_submission_id: Optional[int] = Query(None, description="Start Submission ID"),
        end_submission_id: Optional[int] = Query(None, description="End Submission ID"),
        db: Session = Depends(get_db),
        current_user: ArxivUserClaims = Depends(get_authn),
    ) -> List[SubmissionModel]:
    datagrid_filter = MuiDataGridFilter(filter) if filter else None
    query = SubmissionModel.base_select(db)
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
                raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid start or end index")

    if id is not None:
        _start = 0
        _end = len(id)
        query = query.filter(Submission.submission_id.in_(id))
        if not current_user.is_admin:
            query = query.filter(Submission.submitter_id == current_user.user_id)
    else:
        if start_submission_id is not None:
            if end_submission_id is not None:
                query = query.filter(Submission.submission_id.between(start_submission_id, end_submission_id))
            else:
                query = query.filter(Submission.submission_id >= start_submission_id)
        elif end_submission_id is not None:
            query = query.filter(Submission.submission_id <= end_submission_id)

        if stage is not None:
            query = query.filter(Submission.stage.in_(stage))

        if submission_status is not None or submission_status_group is not None:
            status_list: List[int] = []
            status_codes: List[int|str] = []
            if isinstance(submission_status, list):
                status_codes.extend(submission_status)
            if isinstance(submission_status, int):
                status_codes.append(submission_status)
            if isinstance(submission_status_group, list):
                status_codes.extend(submission_status_group)
            if isinstance(submission_status_group, str):
                status_codes.append(submission_status_group)

            status_all = False
            for status_code in status_codes:
                if isinstance(status_code, int):
                    status_list.append(status_code)
                    continue
                if not isinstance(status_code, str):
                    continue

                if status_code == "all":
                    status_all = True
                    break
                for status_def in _VALID_STATUS_LIST:
                    if status_def.name.find(status_code) != -1 or status_def.group.find(status_code) != -1:
                        status_list.append(status_def.id)
            if not status_all:
                query = query.filter(Submission.status.in_(status_list))

        if title_like is not None:
            # query = query.filter(Submission.title.like("%" + title_like + "%"))
            query = query.filter(Submission.title.like(text(":title"), escape='\\')).params(title=f"%{title_like}%")

        if document_id is not None:
            query = query.filter(Submission.document_id == document_id)

        if submitter_id is not None:
            query = query.filter(Submission.submitter_id == submitter_id)
        else:
            if not current_user.is_admin:
                query = query.filter(Submission.submitter_id == current_user.user_id)

        if preset is not None:
            matched = re.search(r"last_(\d+)_days", preset)
            if matched:
                t_begin = t0 - timedelta(days=int(matched.group(1)))
                t_end = t0
                query = query.filter(Submission.submit_time.between(t_begin, t_end))
            else:
                raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid preset format")
        else:
            if start_date or end_date:
                t_begin = start_date if start_date else VERY_OLDE
                # t_end = datetime_to_epoch(end_date, date.today(), hour=23, minute=59, second=59)
                t_end = end_date if end_date else datetime.now()
                query = query.filter(Submission.submit_time.between(t_begin, t_end))

        if type is not None:
            if isinstance(type, list):
                query = query.filter(Submission.type.in_(type))
            else:
                query = query.filter(Submission.type == type)

        if datagrid_filter:
            field_name = datagrid_filter.field_name
            if field_name == "id":
                field_name = "submission_id"
            if field_name:
                if hasattr(Submission, field_name):
                    field = getattr(Submission, field_name)
                    query = datagrid_filter.to_query(query, field)
                else:
                    logger.warning(f"{field_name} field not found on Submission, skipping")

    for column in order_columns:
        if _order == "DESC":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    if _start is None:
        _start = 0
    if _end is None:
        _end = 100
    result = [SubmissionModel.to_model(item, db) for item in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get("/paper/{paper_id:str}")
async def get_submission_by_paper_id(
        paper_id:str,
        current_user: ArxivUserClaims = Depends(get_authn),
        session: Session = Depends(get_db)) -> SubmissionModel:
    """Display a paper."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not logged in")
    query = SubmissionModel.base_select(session).filter(Submission.doc_paper_id == paper_id)
    doc = query.one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Paper not found")
    return doc

@router.get("/{id:int}")
async def get_submission(
        id: int,
        current_user: ArxivUserClaims = Depends(get_authn),
        session: Session = Depends(get_db)) -> SubmissionModel:
    """Display a paper."""
    if not current_user:
        raise HTTPException(status_code=401, detail="Not logged in")
    query = SubmissionModel.base_select(session).filter(Submission.submission_id == id)
    if not current_user.is_admin:
        query = query.filter(Submission.submitter_id == current_user.user_id)
    sub = query.one_or_none()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")
    submission: SubmissionModel = SubmissionModel.model_validate(sub)
    submission.submission_categories = [SubmissionCategoryModel.model_validate(cat) for cat in SubmissionCategoryModel.base_select(session).filter(SubmissionCategory.submission_id == id).all()]
    return submission


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

class SubmissionNavi(BaseModel):
    first_id: Optional[int]
    prev_ids: List[int]
    next_ids: List[int]
    last_id: Optional[int]


@router.get("/navigate")
async def navigate(
        id: int,
        submission_status: Optional[List[int]] = Query(None, description="Submission status list"),
        count: Optional[int] = Query(default=2, description="Number of prev/next IDs" ),
        session: Session = Depends(get_db),
    ) -> SubmissionNavi:

    if submission_status is None:
        status_list = [0, 1, 2]
    else:
        status_list = submission_status

    first_pending = session.query(Submission) \
        .filter(Submission.status.in_(status_list)) \
        .order_by(Submission.submission_id.asc()) \
        .first()

    last_pending = session.query(Submission) \
        .filter(Submission.status.in_(status_list)) \
        .order_by(Submission.submission_id.desc()) \
        .first()

    next_pending: List[Submission] = session.query(Submission) \
        .filter(and_(Submission.submission_id > id, Submission.status.in_(status_list))) \
        .order_by(Submission.submission_id.asc()) \
        .limit(count).all()

    prev_pending: List[Submission] = session.query(Submission) \
        .filter(and_(Submission.submission_id < id, Submission.status.in_(status_list))) \
        .order_by(Submission.submission_id.desc()) \
        .limit(count).all()

    return SubmissionNavi(
        first_id=first_pending.submission_id if first_pending else None,
        last_id=last_pending.submission_id if last_pending else None,
        next_ids=[req0.submission_id for req0 in next_pending],
        prev_ids=[req1.submission_id for req1 in reversed(prev_pending)],
    )
