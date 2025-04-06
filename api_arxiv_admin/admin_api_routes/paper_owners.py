"""arXiv ownership routes."""
from datetime import timedelta, datetime, date, UTC
from typing import Optional, List, Tuple
import re

from arxiv.auth.user_claims import ArxivUserClaims
from arxiv_bizlogic.bizmodels.user_model import UserModel
from arxiv_bizlogic.fastapi_helpers import get_hostname, get_client_host_name, get_client_host
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status as http_status
from sqlalchemy.exc import IntegrityError

from sqlalchemy import literal_column, func, and_, update  # case, Select, distinct, exists, alias,  select, update

from sqlalchemy.orm import Session # , joinedload

from pydantic import BaseModel #, validator
from arxiv.base import logging
from arxiv.db.models import PaperOwner, PaperPw, Document

from . import get_db, datetime_to_epoch, VERY_OLDE, get_current_user, is_any_user, gate_admin_user, get_tracking_cookie
from .biz.paper_owner_biz import generate_paper_pw
from .helpers.mui_datagrid import MuiDataGridFilter
from .localfile.submission_state import arxiv_is_pending

from .documents import DocumentModel

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_any_user)], prefix="/paper_owners")

class OwnershipModel(BaseModel):
    class Config:
        from_attributes = True

    id: str
    document_id: int
    user_id: int
    date: datetime
    added_by: int
    remote_addr: str
    remote_host: str
    tracking_cookie: str
    valid: bool
    flag_author: bool
    flag_auto: bool

    document: Optional[DocumentModel] = None

    @staticmethod
    def base_select(session: Session):
        return session.query(
            func.concat(
                literal_column("'user_'"),
                PaperOwner.user_id,
                literal_column("'-doc_'"),
                PaperOwner.document_id
            ).label('id'),
            PaperOwner.document_id,
            PaperOwner.user_id,
            PaperOwner.date,
            PaperOwner.added_by,
            PaperOwner.remote_addr,
            PaperOwner.remote_host,
            PaperOwner.tracking_cookie,
            PaperOwner.valid,
            PaperOwner.flag_author,
            PaperOwner.flag_auto,
        )

# to deal with combo primary key - what a pain
ownership_id_re = re.compile(r"user_(\d+)-doc_(\d+)")

def ownership_combo_key(user_id: int, document_id: int):
    """Make the combo primary key -matches with the select above"""
    return f"user_{user_id}-doc_{document_id}"

def to_ids(one_id: str) -> Tuple[Optional[int], Optional[int]]:
    matched = ownership_id_re.match(one_id)
    if not matched:
        return (None, None)
    return int(matched.group(1)), int(matched.group(2))


@router.get('/')
async def list_ownerships(
        response: Response,
        _sort: Optional[str] = Query("date", description="sort by"),
        _order: Optional[str] = Query("DESC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        preset: Optional[str] = Query(None),
        start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
        end_date: Optional[datetime] = Query(None, description="End date for filtering"),
        flag_valid: Optional[bool] = Query(None),
        user_id: Optional[str] = Query(None),
        document_id: Optional[int] = Query(None),
        filter: Optional[str] = Query(None, description="MUI datagrid filter"),
        id: Optional[List[str]] = Query(None,
                                        description="List of paper owner"),
        with_document: Optional[bool] = Query(False, description="with document"),
        current_user: ArxivUserClaims = Depends(get_current_user),
        session: Session = Depends(get_db)
    ) -> List[OwnershipModel]:
    query = OwnershipModel.base_select(session)

    if str(user_id) != current_user.user_id and not current_user.is_admin:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Unauthorized")

    datagrid_filter = MuiDataGridFilter(filter) if filter is not None else None

    if id:
        _start = 0
        _end = len(id)
        users = []
        docs = []
        for one_id in id:
            uid, did = to_ids(one_id)
            if not uid:
                raise HTTPException(status_code=400)
            users.append(uid)
            docs.append(did)
        if len(users) == 1:
            query = query.filter(and_(PaperOwner.user_id == users[0],
                                      PaperOwner.document_id.in_(docs)))
        elif len(docs) == 1:
            query = query.filter(and_(PaperOwner.document_id == docs[0],
                                      PaperOwner.user_id.in_(users)))
        else:
            # not that difficult to support this but not sure I need it
            raise HTTPException(status_code=400)
    else:
        if _start < 0 or _end < _start:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST,
                                detail="Invalid start or end index")
        if user_id is not None:
            query = query.filter(PaperOwner.user_id == user_id)

        if document_id is not None:
            query = query.filter(PaperOwner.document_id == document_id)

        t0 = datetime.now()

        order_columns = []
        if _sort:
            keys = _sort.split(",")
            for key in keys:
                if key == "id":
                    order_columns.append(getattr(PaperOwner, "user_id"))
                    order_columns.append(getattr(PaperOwner, "document_id"))
                else:
                    try:
                        order_column = getattr(PaperOwner, key)
                        order_columns.append(order_column)
                    except AttributeError:
                        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST,
                                            detail="Invalid start or end index")

        if preset is not None:
            matched = re.search(r"last_(\d+)_days", preset)
            if matched:
                t_begin = datetime_to_epoch(None, t0 - timedelta(days=int(matched.group(1))))
                t_end = datetime_to_epoch(None, t0)
                query = query.filter(PaperOwner.date.between(t_begin, t_end))
            else:
                raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid preset format")
        else:
            if start_date or end_date:
                t_begin = datetime_to_epoch(start_date, VERY_OLDE)
                t_end = datetime_to_epoch(end_date, date.today(), hour=23, minute=59, second=59)
                query = query.filter(PaperOwner.date.between(t_begin, t_end))

        if flag_valid is not None:
            query = query.filter(PaperOwner.valid == flag_valid)
        else:
            if current_user and not current_user.is_admin:
                query = query.filter(PaperOwner.valid == 1)

        if datagrid_filter:
            query = query.join(Document).filter(PaperOwner.document_id == Document.document_id)
            field_name = datagrid_filter.field_name
            if field_name == "id":
                field_name = "document_id"
            if field_name:
                if field_name.startswith("document."):
                    doc_field_name = field_name.split(".")[1]
                    if hasattr(Document, doc_field_name):
                        field = getattr(Document, doc_field_name)
                        query = datagrid_filter.to_query(query, field)
                    else:
                        logger.warning(f"{field_name} field not found on Document, skipping")

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
    result = [OwnershipModel.model_validate(item) for item in query.offset(_start).limit(_end - _start).all()]

    if with_document:
        doc_ids = [doc.document_id for doc in result]
        docs = {d.id: d for d in [DocumentModel.model_validate(doc).populate_remaining_fields(session) for doc in DocumentModel.base_select(session).filter(Document.document_id.in_(doc_ids)).all()]}
        for onwnership in result:
            onwnership.document = docs.get(onwnership.document_id)
    return result



@router.get('/user/{user_id:int}')
async def list_ownerships_for_user(
        response: Response,
        user_id: int,
        _sort: Optional[str] = Query("date", description="sort by"),
        _order: Optional[str] = Query("DESC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        preset: Optional[str] = Query(None),
        start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
        end_date: Optional[datetime] = Query(None, description="End date for filtering"),
        flag_valid: Optional[bool] = Query(None),
        document_id: Optional[int] = Query(None),
        current_user: ArxivUserClaims = Depends(get_current_user),
        session: Session = Depends(get_db)
    ) -> List[OwnershipModel]:
    # gate_admin_user(current_user)
    query = OwnershipModel.base_select(session)

    if (not current_user.is_admin) and (user_id != current_user.user_id):
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN,
                            detail="Not authorized")

    query = query.filter(PaperOwner.user_id == user_id)
    if document_id is not None:
        query = query.filter(PaperOwner.document_id == document_id)

    t0 = datetime.now()

    order_columns = []

    if preset is not None:
        matched = re.search(r"last_(\d+)_days", preset)
        if matched:
            t_begin = datetime_to_epoch(None, t0 - timedelta(days=int(matched.group(1))))
            t_end = datetime_to_epoch(None, t0)
            query = query.filter(PaperOwner.date.between(t_begin, t_end))
        else:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST,
                                detail="Invalid preset format")
    else:
        if start_date or end_date:
            t_begin = datetime_to_epoch(start_date, VERY_OLDE)
            t_end = datetime_to_epoch(end_date, date.today(), hour=23, minute=59, second=59)
            query = query.filter(PaperOwner.date.between(t_begin, t_end))

    if flag_valid is not None:
        query = query.filter(PaperOwner.valid == flag_valid)

    if _sort:
        keys = _sort.split(",")
        for key in keys:
            if key == "id":
                # keys.append("user_id") -> This is for single user so makes no sense to sort
                keys.append("document_id")
            try:
                order_column = getattr(PaperOwner, key)
                order_columns.append(order_column)
            except AttributeError:
                raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid start or end index")

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
    result = [OwnershipModel.model_validate(item) for item in query.offset(_start).limit(_end - _start).all()]
    return result



@router.get('/{id:str}')
async def get_ownership(id: str,
                        current_user: ArxivUserClaims = Depends(get_current_user),
                        session: Session = Depends(get_db)
                        ) -> OwnershipModel:
    uid, did = to_ids(id)
    gate_admin_user(current_user)
    if not uid or not did:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST)
    item = OwnershipModel.base_select(session).filter(and_(
        PaperOwner.user_id == uid,
        PaperOwner.document_id == did,
    )).one_or_none()
    if item:
        return OwnershipModel.model_validate(item)
    raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND)


@router.put('/{id:str}')
async def update_ownership(
        request: Request,
        id: str,
        current_user: ArxivUserClaims = Depends(get_current_user),
        session: Session = Depends(get_db)) -> OwnershipModel:
    gate_admin_user(current_user)

    if not current_user.is_admin:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN,)

    uid, did = to_ids(id)
    if uid is None:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST)
    body = await request.json()

    item = session.query(PaperOwner).filter(PaperOwner.user_id == id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify?
    for key, value in body.items():
        if key in item.__dict__:
            setattr(item, key, value)

    session.commit()
    session.refresh(item)  # Refresh the instance with the updated data
    return OwnershipModel.model_validate(item)



paper_pw_router = APIRouter(prefix="/paper-pw")

class PaperPwModel(BaseModel):
    id: int
    password_enc: str

    class Config:
        from_attributes = True

    @staticmethod
    def base_select(session: Session):
        return session.query(
            PaperPw.document_id.label("id"),
            PaperPw.password_enc,
        )

async def _get_paper_pw(id: str,
                        current_user: ArxivUserClaims = Depends(get_current_user),
                        session: Session = Depends(get_db)) -> PaperPwModel:
    if current_user is None:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED)

    doc = session.query(Document).filter(Document.document_id == id).one_or_none()
    if doc is None:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Document not found")

    if not current_user.is_admin:
        owner = session.query(Document).filter(and_(
            Document.document_id == id,
            Document.submitter_id == current_user.user_id
        )).one_or_none()
        if not owner:
            owner = session.query(PaperOwner).filter(and_(
                PaperOwner.document_id == id,
                PaperOwner.user_id == current_user.user_id)).all()
        if not owner:
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not paper owner")

    item = PaperPwModel.base_select(session).filter(PaperPw.document_id == id).one_or_none()
    if not item:
        new_password = generate_paper_pw()
        item = PaperPw(document_id=id, password_storage=0, password_enc=new_password)
        session.add(item)
        try:
            session.commit()
        except IntegrityError:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="Paper password already exists")

    return PaperPwModel.model_validate(item)


@paper_pw_router.get('/{id:str}')
async def get_paper_pw(id: str,
                       current_user: ArxivUserClaims = Depends(get_current_user),
                       session: Session = Depends(get_db)) -> PaperPwModel:
    return await _get_paper_pw(id, current_user, session)


@paper_pw_router.get('/paper/{arxiv_id:str}')
async def get_paper_pw_from_arxiv_id(arxiv_id: str,
                       current_user: ArxivUserClaims = Depends(get_current_user),
                       session: Session = Depends(get_db)) -> PaperPwModel:
    doc: Document | None = session.query(Document).filter(Document.paper_id == arxiv_id).one_or_none()
    if not doc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Paper not found")
    return await _get_paper_pw(doc.document_id, current_user, session)

@paper_pw_router.get('/paper/{category:str}/{subject_class:str}')
async def get_paper_pw_from_arxiv_id(category: str, subject_class: str,
                       current_user: ArxivUserClaims = Depends(get_current_user),
                       session: Session = Depends(get_db)) -> PaperPwModel:
    arxiv_id = f"{category}/{subject_class}"
    doc: Document | None = session.query(Document).filter(Document.paper_id == arxiv_id).one_or_none()
    if not doc:
        raise HTTPException(status_code=http_status.HTTP_404_NOT_FOUND, detail="Paper not found")
    return await _get_paper_pw(doc.document_id, current_user, session)


@router.post('/')
async def create_ownership(
        request: Request,
        current_user: ArxivUserClaims = Depends(get_current_user),
        session: Session = Depends(get_db)) -> OwnershipModel:
    gate_admin_user(current_user)
    body = await request.json()

    item = PaperOwner(**body)
    session.add(item)
    session.commit()
    session.refresh(item)
    return OwnershipModel.model_validate(item)


class PaperAuthRequest(BaseModel):
    paper_id: str
    password: str
    user_id: str
    verify_id: bool


def arxiv_squash_id(paper_id: str) -> str | None:
    """Normalize an arXiv paper ID to its standard format."""
    paper_id = paper_id.strip()
    if re.match(r"^([a-z-]*/\d{7}|\d{4}\.\d{4,5})$", paper_id):
        return paper_id
    match = re.match(r"^([a-z-]*)\.[A-Za-z]{2}/(\d{7})$", paper_id)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return None



@router.post("/authorize/")
def register_paper_owner(
        response: Response,
        body: PaperAuthRequest,
        session: Session = Depends(get_db),
        remote_addr: str = Depends(get_client_host),
        remote_host: str = Depends(get_client_host_name),
        current_user: ArxivUserClaims = Depends(get_current_user),
):
    if current_user is None:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    if body.user_id != current_user.user_id and not current_user.is_admin:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="You can only own the paper as your own.")

    if not body.verify_id:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="You must verify your contact information.")

    squashed_id = arxiv_squash_id(body.paper_id)
    if not squashed_id:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Paper ID '{body.paper_id}' is ill-formed.")

    paper: Document | None = session.query(Document).filter(Document.paper_id == squashed_id).one_or_none()
    if paper is None:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Paper ID '{body.paper_id}' is ill-formed.")

    # This needs to review hard
    is_auto = body.user_id == paper.submitter_id

    document_id = paper.document_id

    if not current_user.is_admin:
        paper_pw = session.query(PaperPw).filter(PaperPw.document_id == document_id).one_or_none()
        if not paper_pw:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Paper '{body.paper_id}' does not have a password.")

        if paper_pw.password_storage != 0:
            raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Paper '{body.paper_id}' has a password storage which is unexpected.")

        if body.password != paper_pw.password_enc and not current_user.is_admin:  # the 2nd part is redundant, I know.
            raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Incorrect password.")

    user = UserModel.one_user(session, body.user_id)

    existing = session.query(PaperOwner).filter(PaperOwner.user_id == body.user_id, PaperOwner.document_id == document_id).one_or_none()
    if existing:
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail=f"You, {user.username} have the ownership of '{body.paper_id}'.")

    paper_owner = PaperOwner(
        user_id=body.user_id,
        document_id=document_id,
        added_by=current_user.user_id,
        remote_addr=remote_addr,
        remote_host=remote_host,
        valid = True,
        flag_author=True,
        flag_auto=1 if is_auto else 0,
        tracking_cookie = None if user is None else user.tracking_cookie,
    )
    session.add(paper_owner)
    session.commit()
    response.status_code = http_status.HTTP_201_CREATED
    return


class PaperOwnershipUpdateRequest(BaseModel):
    user_id: str
    authored: List[str] = []
    not_authored: List[str] = []
    valid: Optional[bool] = None    # Default is True when created
    auto: Optional[bool] = None     # Default is False when created
    timestamp: Optional[str] = None # ISO timestamp


def parse_doc_id(doc_id: str) -> str | int:
    if doc_id.startswith("user_"):
        matched = ownership_id_re.match(doc_id)
        if matched:
            return int(matched.group(2))
    return doc_id


@router.post("/update-authorship")
async def update_authorship(
        body: PaperOwnershipUpdateRequest,
        session: Session = Depends(get_db),
        remote_addr: Optional[str] = Depends(get_client_host),
        remote_host: Optional[str] = Depends(get_client_host_name),
        tracking_cookie: Optional[str] = Depends(get_tracking_cookie),
        current_user: ArxivUserClaims = Depends(get_current_user)  # Assumes user has an 'id' field
):
    if current_user is None:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    if body.user_id != current_user.user_id and not current_user.is_admin:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="You can only update own paper owner.")

    timestamp = datetime.fromisoformat(body.timestamp) if body.timestamp else datetime_to_epoch(None, datetime.now(UTC))
    auto = False if body.auto is None else body.auto
    valid = True if body.valid is None else body.valid

    if valid == False and not current_user.is_admin:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not authorized.")

    for flag, doc__list in enumerate([body.not_authored, body.authored]):
        if not doc__list:
            continue
        doc_ids = [parse_doc_id(doc) for doc in doc__list]

        existing_docs = {
            str(po.document_id): po for po in session.query(PaperOwner)
            .filter(PaperOwner.user_id == body.user_id, PaperOwner.document_id.in_(doc_ids))
            .all()
        }

        for doc_id in doc_ids:
            d_id = str(doc_id)
            if d_id in existing_docs:
                existing_docs[d_id].flag_author = flag
                if body.auto is not None:
                    existing_docs[d_id].flag_auto = body.auto
                if body.valid is not None:
                    existing_docs[d_id].flag_valid = body.valid
            else:
                new_ownership = PaperOwner(
                    document_id=doc_id,
                    user_id=body.user_id,
                    date=timestamp,
                    added_by=current_user.user_id,
                    remote_addr=remote_addr,
                    remote_host=remote_host,
                    tracking_cookie=tracking_cookie,
                    valid=valid,
                    flag_author=flag,
                    flag_auto=auto,
                )
                session.add(new_ownership)
    session.commit()
    return
