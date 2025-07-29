"""arXiv paper display routes."""
from arxiv.db import Base
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import Optional, List
from arxiv.base import logging
from arxiv.db.models import Metadata, Document
from arxiv.document.version import SOURCE_FORMAT

from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, date, timedelta, timezone
# from .models import CrossControlModel
import re

from . import get_db, datetime_to_epoch, VERY_OLDE
from .biz.metadata_biz import propagate_metadata_to_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metadata")

yymm_re = re.compile(r"^\d{4}\.\d{0,5}")

class MetadataModel(BaseModel):
    id: int # metadata_id

    document_id: int
    paper_id: str # Mapped[str] = mapped_column(String(64), nullable=False)
    created: Optional[datetime] = None # Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated: Optional[datetime] = None # Mapped[Optional[datetime]] = mapped_column(DateTime)
    submitter_id: Optional[int] = None # Mapped[Optional[int]] = mapped_column(ForeignKey("tapir_users.user_id"), index=True)
    submitter_name: str # Mapped[str] = mapped_column(String(64), nullable=False)
    submitter_email: str # Mapped[str] = mapped_column(String(64), nullable=False)
    source_size: Optional[int] = None # Mapped[Optional[int]] = mapped_column(Integer)
    source_format: Optional[SOURCE_FORMAT] = None # Mapped[Optional[SOURCE_FORMAT]] = mapped_column(String(12))
    source_flags: Optional[str] = None # Mapped[Optional[str]] = mapped_column(String(12))
    title: Optional[str] = None # Mapped[Optional[str]] = mapped_column(Text)
    authors: Optional[str] = None # Mapped[Optional[str]] = mapped_column(Text)
    abs_categories: Optional[str] = None # Mapped[Optional[str]] = mapped_column(String(255))
    comments: Optional[str] = None # Mapped[Optional[str]] = mapped_column(Text)
    proxy: Optional[str] = None #Mapped[Optional[str]] = mapped_column(String(255))
    report_num: Optional[str] = None #Mapped[Optional[str]] = mapped_column(Text)
    msc_class: Optional[str] = None #Mapped[Optional[str]] = mapped_column(String(255))
    acm_class: Optional[str] = None #Mapped[Optional[str]] = mapped_column(String(255))
    journal_ref: Optional[str] = None #Mapped[Optional[str]] = mapped_column(Text)
    doi: Optional[str]  = None #Mapped[Optional[str]] = mapped_column(String(255))
    abstract: Optional[str] = None #Mapped[Optional[str]] = mapped_column(Text)
    license: Optional[str] = None #Mapped[Optional[str]] = mapped_column(ForeignKey("arXiv_licenses.name"), index=True)
    version: int #Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    modtime: Optional[int] = None # Mapped[Optional[int]] = mapped_column(Integer)
    is_current: Optional[int] = None # Mapped[Optional[int]] = mapped_column(Integer, server_default=FetchedValue())
    is_withdrawn: bool # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())

    class Config:
        from_attributes = True

    @staticmethod
    def base_select(db: Session):

        return db.query(
            Metadata.metadata_id.label("id"),
            Metadata.document_id,
            Metadata.paper_id,
            Metadata.created,
            Metadata.updated,
            Metadata.submitter_id,
            Metadata.submitter_name,
            Metadata.submitter_email,
            Metadata.source_size,
            Metadata.source_format,
            Metadata.source_flags,
            Metadata.title,
            Metadata.authors,
            Metadata.abs_categories,
            Metadata.comments,
            Metadata.proxy,
            Metadata.report_num,
            Metadata.msc_class,
            Metadata.acm_class,
            Metadata.journal_ref,
            Metadata.doi,
            Metadata.abstract,
            Metadata.license,
            Metadata.version,
            Metadata.modtime,
            Metadata.is_current,
            Metadata.is_withdrawn
        )


@router.get('/')
async def list_metadatas(
        response: Response,
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        id: Optional[List[int]] = Query(None, description="List of metadata IDs to filter by"),
        preset: Optional[str] = Query(None),
        start_date: Optional[date] = Query(None, description="Start date for filtering"),
        end_date: Optional[date] = Query(None, description="End date for filtering"),
        document_id: Optional[str] = Query(None, description="Document ID"),
        paper_id: Optional[str] = Query(None, description="arXiv ID"),
        db: Session = Depends(get_db)
    ) -> List[MetadataModel]:
    query = MetadataModel.base_select(db)

    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")
    if id is None:

        t0 = datetime.now()
        order_columns = []
        if _sort:
            keys = _sort.split(",")
            for key in keys:
                if key == "id":
                    key = "metadata_id"
                try:
                    order_column = getattr(Metadata, key)
                    order_columns.append(order_column)
                except AttributeError:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Invalid start or end index")

        if preset is not None:
            matched = re.search(r"last_(\d+)_days", preset)
            if matched:
                t_begin = datetime_to_epoch(None, t0 - timedelta(days=int(matched.group(1))))
                t_end = datetime_to_epoch(None, t0)
                query = query.filter(Metadata.created.between(t_begin, t_end))
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid preset format")
        else:
            if start_date or end_date:
                t_begin = datetime_to_epoch(start_date, VERY_OLDE)
                t_end = datetime_to_epoch(end_date, date.today(), hour=23, minute=59, second=59)
                query = query.filter(Metadata.created.between(t_begin, t_end))

        if document_id is not None:
            query = query.filter(Metadata.document_id == document_id)
            pass
        elif paper_id is not None:
            if len(paper_id) >= 5 and yymm_re.match(paper_id):
                least_paper_id = paper_id + "0000.00000"[len(paper_id):]
                most_paper_id = paper_id + "9999.99999"[len(paper_id):]
                query = query.filter(Metadata.paper_id.between(least_paper_id, most_paper_id))
            else:
                query = query.filter(Metadata.paper_id.like(paper_id + "%"))
                pass
            pass

        for column in order_columns:
            if _order == "DESC":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())
    else:
        query = query.filter(Metadata.metadata_id.in_(id))

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result: List[MetadataModel] = [MetadataModel.model_validate(item) for item in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get("/paper_id/{paper_id:str}")
def get_metadata_by_paper_id(paper_id:str,
                 session: Session = Depends(get_db)) -> MetadataModel:
    """Get the metadata from paper id."""
    query = MetadataModel.base_select(session).filter(Metadata.paper_id == paper_id)
    doc = query.one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Paper not found")
    return MetadataModel.model_validate(doc)

@router.get("/paper_id/{category}/{numeric_id:str}")
def get_metadata_ancient(category:str, numeric_id:str,
                 session: Session = Depends(get_db)) -> MetadataModel:
    """Get the metadata from paper id."""
    paper_id = f"{category}/{numeric_id}"
    query = MetadataModel.base_select(session).filter(Metadata.paper_id == paper_id)
    doc = query.one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Paper not found")
    return MetadataModel.model_validate(doc)


@router.get("/document_id/{document_id:str}")
def get_metadata_from_document_id(
    document_id:str,
    session: Session = Depends(get_db)) -> MetadataModel:
    """Display a paper."""
    metadata = MetadataModel.base_select(session).filter(Metadata.document_id == document_id).order_by(Metadata.metadata_id.desc()).limit(1).all()
    if not metadata:
        raise HTTPException(status_code=404, detail="Paper not found")
    return MetadataModel.model_validate(metadata[0])


@router.get("/{id:str}")
def get_metadata_by_id(id:int,
                 session: Session = Depends(get_db)) -> MetadataModel:
    """Display a paper."""
    query = MetadataModel.base_select(session).filter(Metadata.metadata_id == id)
    doc = query.one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Paper not found")
    return MetadataModel.model_validate(doc)



@router.put("/{id:str}")
def update_metadata_by_id(
        id:int,
        body: MetadataModel,
        session: Session = Depends(get_db)) -> MetadataModel:
    """Display a paper."""
    md: Metadata | None = session.query(Metadata).filter(Metadata.metadata_id == id).one_or_none()
    if not md:
        raise HTTPException(status_code=404, detail="Paper not found")

    doc: Document | None = None
    if md.is_current:
        doc = session.query(Document).filter(Document.document_id == md.document_id).one_or_none()

    updating = body.model_dump(exclude_unset=True, exclude_none=True, exclude={"id"})
    count = 0

    for key, value in updating.items():
        old_value = getattr(md, key)
        if old_value != value:
            count += 1
            setattr(md, key, value)
            if not md.is_current:
                continue

            if propagate_metadata_to_document(session, md, key, doc):
                count += 1
        pass

    if count > 0:
        md.updated = datetime.now(timezone.utc)
        session.commit()

    metadata = MetadataModel.base_select(session).filter(Metadata.metadata_id == id).one_or_none()
    if not metadata:
        raise HTTPException(status_code=404, detail="Paper not found")
    return MetadataModel.model_validate(metadata)

