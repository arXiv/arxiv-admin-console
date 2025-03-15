"""arXiv ownership routes."""
from datetime import timedelta, datetime, date
from typing import Optional, List, Tuple
import re

from arxiv.auth.user_claims import ArxivUserClaims
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status as http_status
from sqlalchemy.exc import IntegrityError

from sqlalchemy import literal_column, func, and_  # case, Select, distinct, exists, alias,  select, update

from sqlalchemy.orm import Session # , joinedload

from pydantic import BaseModel #, validator
from arxiv.base import logging
from arxiv.db.models import PaperOwner, PaperPw, Document

from . import get_db, datetime_to_epoch, VERY_OLDE, get_current_user, is_any_user, gate_admin_user
from .biz.paper_owner_biz import generate_paper_pw
from .localfile.submission_state import arxiv_is_pending

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

ownership_id_re = re.compile(r"user_(\d+)-doc_(\d+)")


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
        user_id: Optional[int] = Query(None),
        document_id: Optional[int] = Query(None),
        id: Optional[List[str]] = Query(None,
                                        description="List of paper owner"),
        current_user: ArxivUserClaims = Depends(get_current_user),
        session: Session = Depends(get_db)
    ) -> List[OwnershipModel]:

    gate_admin_user(current_user)

    query = OwnershipModel.base_select(session)

    if id:
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
                    keys.append("user_id")
                    keys.append("document_id")
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

        for column in order_columns:
            if _order == "DESC":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [OwnershipModel.model_validate(item) for item in query.offset(_start).limit(_end - _start).all()]
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
    gate_admin_user(current_user)
    query = OwnershipModel.base_select(session)


    if _start < 0 or _end < _start:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    if not current_user.is_admin or user_id != current_user.user_id:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN,
                            detail="Not authorized")

    query = query.filter(PaperOwner.user_id == user_id)
    if document_id is not None:
        query = query.filter(PaperOwner.document_id == document_id)

    t0 = datetime.now()

    order_columns = []
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

    for column in order_columns:
        if _order == "DESC":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
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


@router.put("/")
def register_paper_owner(
        response: Response,
        body: PaperAuthRequest,
        session: Session = Depends(get_db),
        current_user: ArxivUserClaims = Depends(get_current_user),
):
    if current_user is None:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    if body.user_id != current_user.user_id and not current_user.is_admin:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="You can only own the paper.")

    if not body.verify_id:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail="You must verify your contact information.")

    squashed_id = arxiv_squash_id(body.paper_id)
    if not squashed_id:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Paper ID '{body.paper_id}' is ill-formed.")

    paper: Document | None = session.query(Document).filter(Document.paper_id == squashed_id).one_or_none()
    if paper is None:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Paper ID '{body.paper_id}' is ill-formed.")

    # This needs to review hard
    is_author = body.user_id == paper.submitter_id
    if (not is_author) and arxiv_is_pending(body.paper_id):
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Non-authors cannot access pending papers.")

    document_id = paper.document_id
    paper_pw = session.query(PaperPw).filter(PaperPw.document_id == document_id).one_or_none()
    if not paper_pw:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Paper '{body.paper_id}' does not have a password.")

    if paper_pw.password_storage != 0:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=f"Paper '{body.paper_id}' has a password storage which is unexpected.")

    if body.password != paper_pw.password_enc:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Incorrect password.")

    existing = session.query(PaperOwner).filter(PaperOwner.user_id == body.user_id, PaperOwner.document_id == document_id).one_or_none()
    if existing:
        raise HTTPException(status_code=http_status.HTTP_409_CONFLICT, detail=f"Paper owner '{body.paper_id}' already exists.")

    paper_owner = PaperOwner(
        user_id=body.user_id,
        document_id=document_id,
        added_by=current_user.user_id,
        remote_addr=body.client.host,
        flag_author=1 if is_author else 0,
    )
    session.add(paper_owner)
    session.commit()
    response.status_code = http_status.HTTP_201_CREATED
    return
