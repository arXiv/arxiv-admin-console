"""arXiv paper display routes."""
from __future__ import annotations

from enum import Enum

from arxiv.auth.user_claims import ArxivUserClaims
from arxiv_bizlogic.fastapi_helpers import get_authn
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import Optional, List
from arxiv.base import logging
from arxiv.db.models import Document, Submission, Metadata, PaperOwner, Demographic, TapirUser
from sqlalchemy import func, and_, desc, cast, LargeBinary, Row
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, date, timedelta
# from .models import CrossControlModel
import re
import time

from arxiv_bizlogic.latex_helpers import convert_latex_accents
from sqlalchemy_helper import sa_model_to_pydandic_model
from starlette.responses import RedirectResponse

from . import get_db, datetime_to_epoch, VERY_OLDE, get_current_user
from .helpers.mui_datagrid import MuiDataGridFilter
from .metadata import MetadataModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents")

yymm_re = re.compile(r"^\d{4}\.\d{0,5}")

class TimedCache:
    def __init__(self, expiration_seconds=60):
        self.cache = {}
        self.expiration_seconds = expiration_seconds

    def set(self, key, value):
        self.cache[key] = (value, time.time() + self.expiration_seconds)

    def get(self, key):
        # Check if the key exists and is not expired
        if key in self.cache:
            value, expiry = self.cache[key]
            if time.time() < expiry:
                return value
            else:
                # Remove expired key
                del self.cache[key]
        return None  # Return None if not found or expired

    def __contains__(self, key):
        return self.get(key) is not None

    def clear(self):
        self.cache.clear()

last_submission_cache = TimedCache()

class DocumentModel(BaseModel):
    id: int # document_id
    paper_id: str
    title: str
    authors: Optional[str] = None
    submitter_email: str
    submitter_id: Optional[int] = None
    dated: datetime
    primary_subject_class: Optional[str] = None
    created: Optional[datetime] = None

    last_submission_id: Optional[int] = None

    abs_categories: Optional[str] = None

    author_ids: Optional[List[int]] = None

    class Config:
        from_attributes = True

    @staticmethod
    def base_select(db: Session):

        return db.query(
            Document.document_id.label("id"),
            Document.paper_id,
            cast(Document.title, LargeBinary).label("title"),
            cast(Document.authors, LargeBinary).label("authors"),
            Document.submitter_email,
            Document.submitter_id,
            Document.dated,
            Document.primary_subject_class,
            Document.created,
        )

    @staticmethod
    def to_model(session: Session, row: Row | dict | DocumentModel) -> DocumentModel:
        if isinstance(row, Row):
            data = sa_model_to_pydandic_model(row, DocumentModel, name_map={"document_id": "id"})
        elif isinstance(row, dict):
            data = row
        else:
            data = row.model_dump()
        model_data = DocumentModel.model_validate(data)
        return model_data.populate_remaining_fields(session)


    def populate_remaining_fields(self, session: Session) -> DocumentModel:
        last_submission_id = last_submission_cache.get(self.id)
        if last_submission_id is None:
            last_submission_id = (
                session.query(func.max(Submission.submission_id))
                .filter(Submission.document_id == self.id)
                .scalar()
            )
            if last_submission_id is None:
                last_submission_id = 0
            last_submission_cache.set(self.id, last_submission_id)

        if last_submission_id != 0:
            self.last_submission_id = last_submission_id

        metadata: Metadata | None = session.query(Metadata).filter(
            and_(Metadata.document_id == self.id,
                 Metadata.is_current == 1,
                 Metadata.is_withdrawn == 0)).order_by(desc(Metadata.metadata_id)).first()
        if metadata:
            self.abs_categories = metadata.abs_categories

        owner: PaperOwner
        self.author_ids = [owner.user_id for owner in session.query(
            PaperOwner).filter(PaperOwner.document_id == self.id).join(Demographic, and_(
            Demographic.user_id == PaperOwner.user_id,
            Demographic.flag_proxy == 0)).all()]

        return self

    def current_version(self, session: Session) -> Optional[MetadataModel]:
        """Get the current version of the document"""
        metadata = session.query(Metadata).filter(Metadata.document_id == self.id).order_by(desc(Metadata.version)).first()
        if not metadata:
            return None
        return MetadataModel.model_validate(sa_model_to_pydandic_model(metadata, MetadataModel, name_map={"metadata_id": "id"}))


@router.get('/')
async def list_documents(
        response: Response,
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("DESC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        id: Optional[List[int]] = Query(None, description="List of document IDs to filter by"),
        submitter_id: Optional[str] = Query(None, description="Submitter ID"),
        submitter_name: Optional[str] = Query(None, description="Submitter Name"),
        filter: Optional[str] = Query(None, description="MUI datagrid filter"),
        preset: Optional[str] = Query(None),
        start_date: Optional[date] = Query(None, description="Start date for filtering"),
        end_date: Optional[date] = Query(None, description="End date for filtering"),
        paper_id: Optional[str] = Query(None, description="arXiv ID"),
        db: Session = Depends(get_db)
    ) -> List[DocumentModel]:
    query = DocumentModel.base_select(db)

    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    if submitter_id is not None:
        query = query.filter(Document.submitter_id == submitter_id)

    datagrid_filter = MuiDataGridFilter(filter) if filter is not None else None

    if id is None:
        t0 = datetime.now()
        order_columns = []
        if _sort:
            keys = _sort.split(",")
            for key in keys:
                if key == "id":
                    key = "document_id"
                try:
                    order_column = getattr(Document, key)
                    order_columns.append(order_column)
                except AttributeError:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Invalid start or end index")

        if preset is not None:
            matched = re.search(r"last_(\d+)_days", preset)
            if matched:
                t_begin = datetime_to_epoch(None, t0 - timedelta(days=int(matched.group(1))))
                t_end = datetime_to_epoch(None, t0)
                query = query.filter(Document.dated.between(t_begin, t_end))
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid preset format")
        else:
            if start_date or end_date:
                t_begin = datetime_to_epoch(start_date, VERY_OLDE)
                t_end = datetime_to_epoch(end_date, date.today(), hour=23, minute=59, second=59)
                query = query.filter(Document.dated.between(t_begin, t_end))

        if paper_id is not None:
            if len(paper_id) >= 5 and yymm_re.match(paper_id):
                least_paper_id = paper_id + "0000.0000"[len(paper_id):]
                most_paper_id = paper_id + "9999.99999"[len(paper_id):]
                query = query.filter(Document.paper_id.between(least_paper_id, most_paper_id))
            else:
                query = query.filter(Document.paper_id.like(paper_id + "%"))
            pass

        if submitter_name:
            first_name = None
            last_name = None
            if "," in submitter_name:
                name_elems = submitter_name.split(",")
                if len(name_elems) == 2:
                    first_name = name_elems[1].strip()
                    last_name = name_elems[0].strip()
                elif len(name_elems) == 1:
                    last_name = name_elems[0].strip()
            elif " " in submitter_name:
                name_elems = [elem for elem in submitter_name.split(" ") if elem]
                if len(name_elems) == 2:
                    first_name = name_elems[0].strip()
                    last_name = name_elems[1].strip()
                elif len(name_elems) == 1:
                    last_name = name_elems[0].strip()
                    pass
                pass
            else:
                last_name = submitter_name.strip()
                pass

            if first_name or last_name:
                # Build a subquery to pre-filter TapirUser table first
                user_subquery = db.query(TapirUser.user_id)
                if last_name:
                    user_subquery = user_subquery.filter(TapirUser.last_name.like(last_name + "%"))
                if first_name:
                    user_subquery = user_subquery.filter(TapirUser.first_name.like(first_name + "%"))
                
                # Use the pre-filtered user IDs to filter documents directly
                query = query.filter(Document.submitter_id.in_(user_subquery))

        if datagrid_filter:
            field_name = datagrid_filter.field_name
            if field_name == "id":
                field_name = "document_id"
            if field_name:
                if hasattr(Document, field_name):
                    field = getattr(Document, field_name)
                    query = datagrid_filter.to_query(query, field)
                else:
                    logger.warning(f"{field_name} field not found on Document, skipping")

        for column in order_columns:
            if _order == "DESC":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())
    else:
        _start = 0
        _end = len(id)
        query = query.filter(Document.document_id.in_(id))

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    if _start is None:
        _start = 0
    if _end is None:
        _end = 100
    result: List[DocumentModel] = [DocumentModel.to_model(db, item) for item in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get("/paper_id/{paper_id:str}")
def get_document(paper_id:str,
                 current_user: ArxivUserClaims = Depends(get_authn),
                 session: Session = Depends(get_db)) -> DocumentModel:
    """Display a paper."""
    query = DocumentModel.base_select(session).filter(Document.paper_id == paper_id)
    doc = query.one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Paper {paper_id} not found")
    return DocumentModel.to_model(session, doc)

@router.get("/paper_id/{category:str}/{paper_id:str}")
def get_old_style_document(
        category: str,
        paper_id:str,
        current_user: ArxivUserClaims = Depends(get_authn),
        session: Session = Depends(get_db)) -> DocumentModel:
    """Display a paper."""
    old_paper_id = f"{category}/{paper_id}"
    query = DocumentModel.base_select(session).filter(Document.paper_id == old_paper_id)
    doc = query.one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Paper {old_paper_id} not found")
    return DocumentModel.to_model(session, doc)

@router.get("/{id:str}")
def get_document(id:int,
                 session: Session = Depends(get_db)) -> DocumentModel:
    """Display a paper."""
    query = DocumentModel.base_select(session).filter(Document.document_id == id)
    doc = query.one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paper not found")
    return DocumentModel.to_model(session, doc)


class DocumentUserAction(str, Enum):
    replace = "replace"
    withdraw = "withdraw"
    cross = "cross"
    jref = "jref"
    pwc_code = "pwc_code"

@router.get("/user-action/{id}/{action}")
def redirect_to_user_document_action(
        id:str,
        action: DocumentUserAction,
        _current_user: ArxivUserClaims = Depends(get_authn),
        session: Session = Depends(get_db)) -> RedirectResponse:
    doc = session.query(Document).filter(Document.document_id == id).one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {id} not found")
    if action not in list(DocumentUserAction):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Action {action} is invalid. Must be one of {list(DocumentUserAction)}")
    url = f"/user/{id}/{action.value}"
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
