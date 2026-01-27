"""arXiv paper display routes."""
from __future__ import annotations

import os
from enum import Enum
from pathlib import Path

from arxiv.auth.user_claims import ArxivUserClaims
from arxiv_bizlogic.fastapi_helpers import get_authn, get_authn_user
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Request, UploadFile, File, Form
from typing import Optional, List, BinaryIO, TextIO
from arxiv.base import logging
from arxiv.db.models import Document, Submission, Metadata, PaperOwner, Demographic, TapirUser
from sqlalchemy import func, and_, desc, cast, LargeBinary, Row, text
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, date, timedelta
# from .models import CrossControlModel
import re
import time
from arxiv.identifier import Identifier as arXivID

from arxiv_bizlogic.latex_helpers import convert_latex_accents
from arxiv_bizlogic.sqlalchemy_helper import sa_model_to_pydandic_model
from starlette.responses import RedirectResponse, FileResponse, StreamingResponse

from . import get_db, datetime_to_epoch, VERY_OLDE, get_current_user
from .accessors import LocalAbsAccessor, LocalTarballAccessor, LocalPDFAccessor, GCPAbsAccessor, GCPTarballAccessor, \
    GCPPDFAccessor, GCPStorage, BaseAccessor, LocalOutcomeAccessor, GCPOutcomeAccessor, GCPBlobAccessor, \
    LocalFileAccessor, VersionedFlavor, LocalPathAccessor
from .helpers.mui_datagrid import MuiDataGridFilter
from .metadata import MetadataModel
from .pubsub.event_schemas import BasePaperMessage
from .pubsub.post_pubsub import post_pubsub_event
from google.cloud.storage.fileio import BlobReader

from io import BufferedIOBase
from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)

def close_stream(it: BufferedIOBase | BinaryIO | TextIO, blob_name: str, extra: dict) -> None:
    """Close the stream."""
    it.close()
    logger.debug(f"closed stream for %s", blob_name, extra=extra)
    pass


def closer(it: BufferedIOBase | BinaryIO | TextIO, blob_name: str, extra: dict) -> BackgroundTasks:
    """Create a background task to close the stream."""
    tasks = BackgroundTasks()
    tasks.add_task(close_stream, it, blob_name, extra)
    return tasks


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
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        id: Optional[List[int]] = Query(None, description="List of document IDs to filter by"),
        submitter_id: Optional[str] = Query(None, description="Submitter ID"),
        submitter_name: Optional[str] = Query(None, description="Submitter Name"),
        filter: Optional[str] = Query(None, description="MUI datagrid filter"),
        preset: Optional[str] = Query(None),
        start_date: Optional[date] = Query(None, description="Start date for filtering"),
        end_date: Optional[date] = Query(None, description="End date for filtering"),
        paper_id: Optional[str] = Query(None, description="arXiv ID"),
        title: Optional[str] = Query(None, description="Document title"),
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

        if title:
            query = query.filter(Document.title.like(text(":title"), escape='\\')).params(title=f"%{title}%")

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
                 current_user: ArxivUserClaims = Depends(get_authn_user),
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
        current_user: ArxivUserClaims = Depends(get_authn_user),
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


@router.get("/{id:str}/metadata")
def get_document_metadata(
        id:int,
        response: Response,
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("DESC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        session: Session = Depends(get_db)) -> List[MetadataModel]:
    """List of metadata for a document."""
    doc = session.query(Document).filter(Document.document_id == id).one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {id} not found")

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

    query = MetadataModel.base_select(session).filter(Metadata.document_id == id)

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
    return [MetadataModel.model_validate(md) for md in query.offset(_start).limit(_end - _start).all()]


@router.get("/{id:str}/metadata/latest")
def get_document_metadata_latest(
        id:int,
        response: Response,
        session: Session = Depends(get_db)) -> Optional[MetadataModel]:
    """List of metadata for a document."""
    doc = session.query(Document).filter(Document.document_id == id).one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {id} not found")
    query = MetadataModel.base_select(session).filter(Metadata.document_id == id).order_by(Metadata.metadata_id.desc()).limit(1)
    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    return [MetadataModel.model_validate(sa_model_to_pydandic_model(item, MetadataModel)) for item in query.all()][0] if count > 0 else None


@router.get('/metadata/latest')
async def list_document_metadata_latest(
        response: Response,
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("DESC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        id: Optional[List[int]] = Query(None, description="List of document IDs to filter by"),
        db: Session = Depends(get_db)
) -> List[MetadataModel]:
    if id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="id is required")

    # Subquery to get the latest metadata_id for each document
    latest_metadata_subquery = (
        db.query(
            Metadata.document_id,
            func.max(Metadata.metadata_id).label('latest_metadata_id')
        )
        .filter(Metadata.document_id.in_(id))
        .group_by(Metadata.document_id)
        .subquery()
    )
    
    # Join with the subquery to get the latest metadata records
    query = (
        db.query(Metadata)
        .join(
            latest_metadata_subquery,
            and_(
                Metadata.document_id == latest_metadata_subquery.c.document_id,
                Metadata.metadata_id == latest_metadata_subquery.c.latest_metadata_id
            )
        )
    )
    
    # Apply sorting
    if _sort:
        keys = _sort.split(",")
        for key in keys:
            if key == "id":
                key = "metadata_id"
            try:
                order_column = getattr(Metadata, key)
                if _order == "DESC":
                    query = query.order_by(order_column.desc())
                else:
                    query = query.order_by(order_column.asc())
            except AttributeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Invalid sort field: {key}")

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    
    if _start is None:
        _start = 0
    if _end is None:
        _end = 100
        
    results = query.offset(_start).limit(_end - _start).all()
    # When returning this metadata, ID is keyed by document ID, not metadata ID.
    # This may cause other problem so use it carefully
    return [MetadataModel.model_validate(sa_model_to_pydandic_model(item, MetadataModel, name_map={"id": "document_id"})) for item in results]


class DocumentUserAction(str, Enum):
    replace = "replace"
    withdraw = "withdraw"
    cross = "cross"
    jref = "jref"
    pwc_code = "pwc_code"

@router.get("/user-action/{id}/{action}")
def redirect_to_user_document_action(
        request: Request,
        id:str,
        action: DocumentUserAction,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        session: Session = Depends(get_db)) -> RedirectResponse:
    doc = session.query(Document).filter(Document.document_id == id).one_or_none()
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {id} not found")
    if action not in list(DocumentUserAction):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Action {action} is invalid. Must be one of {list(DocumentUserAction)}")
    user_id = current_user.user_id
    site = request.app.extra['USER_ACTION_SITE']
    urls = request.app.extra['USER_ACTION_URLS']
    url_template = urls.get(action.value, "https://dev.arxiv.org/user/{doc_id}/{action}")
    url = url_template.format(site=site, doc_id=id, action=action.value, user_id=user_id)
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.post("/{id:str}/actions/regenerate/{target:str}")
def regenerate_document_artifacts(
        id:int,
        target: str,
        request: Request,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        session: Session = Depends(get_db)):
    """Regenerate document artifacts."""
    doc: Optional[Document] = session.query(Document).filter(Document.document_id == id).one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {id} not found")

    if doc.submitter_id != current_user.user_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to regenerate document artifacts")

    if target not in ["pdf", "html", "all"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid target: {target}")

    metadata: Optional[Metadata] = session.query(Metadata).filter(Metadata.document_id == id).order_by(desc(Metadata.version)).first()
    if not metadata:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Metadata does not exist")


    if target in ["html", "all"]:
        message = BasePaperMessage(paper_id=doc.paper_id, version=metadata.version)
        post_pubsub_event(message,
                          project_id=request.app.extra['GCP_PROJECT_ID'],
                          topic_name=request.app.extra.get('GCP_HTML_DIRECT_CONVERT', 'html-direct-convert'),
                          logger=logger,
                          creds_name=request.app.extra['GCP_PROJECT_CREDS']
                          )

    if target in ["pdf", "all"]:
        message = BasePaperMessage(paper_id=doc.paper_id, version=metadata.version)


class DocumentFile(BaseModel):
    id: str # canonical name
    blob_id: str
    storage_id: str
    document_id: int
    exists: bool
    file_name: str
    file_size: Optional[int] = None
    content_type: Optional[str] = None

    @property
    def is_file(self) -> bool:
        return self.id.startswith("file://")

    @property
    def is_bucket_object(self) -> bool:
        return self.id.startswith("gs://")


async def blob_to_doc_file(entry: BaseAccessor, document_id: int) -> DocumentFile:
    storage_id = "gcp" if isinstance(entry, GCPBlobAccessor) else "local"
    return DocumentFile(id=entry.canonical_name, blob_id=entry.flavor, storage_id=storage_id,
                        file_name=entry.basename, file_size=await entry.bytesize,
                            content_type=entry.content_type, exists=await entry.exists(), document_id=document_id)


def get_local_source_accessor(xid: arXivID, metadata: Metadata, latest: bool = True) -> BaseAccessor:
    match metadata.source_format:
        case "tex":
            return LocalTarballAccessor(xid, latest=latest)

        case "ps":
            return LocalTarballAccessor(xid, latest=latest)

        case "html":
            return LocalTarballAccessor(xid, latest=latest)

        case "pdf":
            return LocalTarballAccessor(xid, latest=latest)

        case "withdrawn":
            return LocalTarballAccessor(xid, latest=latest)

        case "pdftex":
            return LocalTarballAccessor(xid, latest=latest)

        case "docx":
            return LocalTarballAccessor(xid, latest=latest)

        case _:
            return LocalTarballAccessor(xid, latest=latest)


    # SOURCE_FORMAT = Literal["tex", "ps", "html", "pdf", "withdrawn", "pdftex", "docx"]

    raise ValueError(f"Unknown source format: {metadata.source_format}")


def list_related_files(xid: arXivID, all_metadata: List[Metadata], doc_storage: GCPStorage) -> List[BaseAccessor]:
    candidate_files: List[BaseAccessor] = []
    max_version = max([metadata.version for metadata in all_metadata])

    buddy_files = []
    for idx, metadata in enumerate(all_metadata):
        v_xid = arXivID("%sv%d" % (xid.ids, metadata.version))
        if max_version == metadata.version:
            abs_accessor = LocalAbsAccessor(xid, latest=True)
            candidate_files.append(abs_accessor)
            candidate_files.append(get_local_source_accessor(v_xid, metadata, latest=True))
        else:
            abs_accessor = LocalAbsAccessor(v_xid, latest=False)
            candidate_files.append(abs_accessor)
            candidate_files.append(get_local_source_accessor(v_xid, metadata, latest=False))

        candidate_files.append(LocalPDFAccessor(v_xid, latest=False))
        pass


    if doc_storage:
        for idx, metadata in enumerate(all_metadata):
            v_xid = arXivID("%sv%d" % (xid.ids, metadata.version))
            if max_version == metadata.version:
                candidate_files.append(GCPAbsAccessor(xid, storage=doc_storage, latest=True))
                candidate_files.append(GCPTarballAccessor(xid, storage=doc_storage, latest=True))
            else:
                candidate_files.append(GCPAbsAccessor(v_xid, storage=doc_storage, latest=False))
                candidate_files.append(GCPTarballAccessor(v_xid, storage=doc_storage, latest=False))

            candidate_files.append(GCPPDFAccessor(v_xid, storage=doc_storage, latest=False))
            candidate_files.append(GCPOutcomeAccessor(v_xid, storage=doc_storage, latest=False))
            pass
        pass

    return candidate_files


@router.get("/{id:str}/files")
async def list_document_files(
        id:int,
        request: Request,
        response: Response,
        _sort: Optional[str] = Query("version", description="sort by"),
        _order: Optional[str] = Query("DESC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        current_user: ArxivUserClaims = Depends(get_authn_user),
        session: Session = Depends(get_db)) -> List[DocumentFile]:
    """Regenerate document artifacts."""
    doc: Optional[Document] = session.query(Document).filter(Document.document_id == id).one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {id} not found")

    if doc.submitter_id != current_user.user_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to regenerate document artifacts")

    all_metadata: Optional[List[Metadata]] = session.query(Metadata).filter(Metadata.document_id == id).order_by(desc(Metadata.version)).all()
    if not all_metadata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document metadata {id} not found")

    xid = arXivID(doc.paper_id)
    doc_storage: GCPStorage = request.app.extra.get("DOCUMENT_STORAGE")

    files = list_related_files(xid, all_metadata, doc_storage)
    response.headers['X-Total-Count'] = str(len(files))
    return [ await blob_to_doc_file(blob, id) for blob in files[_start:_end]]


def to_content_type(flavor: str ) -> str:
    return {
       "pdf": "application/pdf",
       "abs": "text/plain",
       "tarball": "application/gzip",
       "html": "text/html",
       "outcome": "application/gzip",
    }.get(flavor, "application/octet-stream")

@router.get("/{id:str}/files/{blob_id:str}")
async def download_document_file(
        id:int,
        blob_id: str,
        request: Request,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        session: Session = Depends(get_db)) -> StreamingResponse:
    """Regenerate document artifacts."""
    doc: Optional[Document] = session.query(Document).filter(Document.document_id == id).one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {id} not found")

    if doc.submitter_id != current_user.user_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to regenerate document artifacts")

    metadata: Optional[Metadata] = session.query(Metadata).filter(Metadata.document_id == id).order_by(desc(Metadata.version)).first()
    if not metadata:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document metadata {id} not found")

    doc_storage: GCPStorage = request.app.extra.get("DOCUMENT_STORAGE")
    blobs = list_related_files(arXivID(doc.paper_id), metadata.version, doc_storage)

    blob: BaseAccessor
    for blob in blobs:
        if not (await blob.exists()):
            continue

        if blob.flavor == blob_id:

            filename = os.path.basename(blob.local_path)
            media_type = to_content_type(blob.flavor)
            headers = {
                "Content-Type": media_type,
                "Content-Disposition": f"attachment; filename={filename}",
            }
            content = blob.open()
            log_extra = {"blob_id": blob_id, "file_base_name": filename}
            return StreamingResponse(
                content,
                headers=headers,
                media_type=media_type,
                background=closer(content, filename, log_extra),
                status_code=status.HTTP_200_OK,
            )
        pass
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"File {doc.paper_id} {blob_id} not found")


@router.post("/{id:str}/files")
async def upload_document_file(
        id: int,
        uploading: UploadFile,
        file_type: str = Form(...),
        storage_id: str = Form(...),
        request: Request = None,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        session: Session = Depends(get_db)):
    """Upload a document file."""
    doc: Optional[Document] = session.query(Document).filter(Document.document_id == id).one_or_none()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Document {id} not found")

    if doc.submitter_id != current_user.user_id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to upload document files")

    # Validate file_type
    valid_types = ["pdf", "abs", "tarball", "html", "outcome"]
    if file_type not in valid_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                          detail=f"Invalid file_type: {file_type}. Must be one of {valid_types}")

    xid = arXivID(doc.paper_id)
    # Determine which accessor to use based on file_type and available storage
    accessor: Optional[BaseAccessor]

    doc_storage: GCPStorage = request.app.extra.get("DOCUMENT_STORAGE")

    if storage_id == "gcp":
        if not doc_storage:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No document storage configured")

        if file_type == "abs":
            accessor = GCPAbsAccessor(xid, storage=doc_storage, latest=True) if doc_storage else LocalAbsAccessor(xid, latest=True)
        elif file_type == "tarball":
            accessor = GCPTarballAccessor(xid, storage=doc_storage, latest=True) if doc_storage else LocalTarballAccessor(xid, latest=True)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported file_type: {file_type}")

    if storage_id == "local":
        if not doc_storage:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No document storage configured")

        if file_type == "abs":
            accessor = LocalAbsAccessor(xid, storage=doc_storage, latest=True) if doc_storage else LocalAbsAccessor(xid, latest=True)
        elif file_type == "tarball":
            accessor = LocalTarballAccessor(xid, storage=doc_storage, latest=True) if doc_storage else LocalTarballAccessor(xid, latest=True)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported file_type: {file_type}")

    if not accessor:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create file accessor")

    # Ensure parent directory exists for local files
    if isinstance(accessor, LocalFileAccessor):
        try:
            os.makedirs(os.path.dirname(accessor.local_path), exist_ok=True)
        except Exception as e:
            logger.warning(f"Failed to create parent directory for local file {accessor.local_path}: {e}")
            pass

    # Stream the file directly to storage
    try:
        with accessor.open(mode='wb') as fd:
            while chunk := await uploading.read(65536):  # 8KB chunks
                fd.write(chunk)

        logger.info(f"Uploaded {file_type} file for document {id} ({doc.paper_id})",
                   extra={"document_id": id, "paper_id": doc.paper_id, "file_type": file_type})

    except Exception as e:
        logger.error(f"Failed to upload {file_type} file for document {id}: {e}",
                    extra={"document_id": id, "paper_id": doc.paper_id, "file_type": file_type, "error": str(e)})
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                          detail=f"Failed to upload file: {str(e)}")

    return
