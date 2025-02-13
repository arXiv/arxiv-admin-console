"""arXiv ownership routes."""
from datetime import timedelta, datetime, date
from typing import Optional, List, Tuple
import re

from arxiv.auth.user_claims import ArxivUserClaims
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status as http_status

from sqlalchemy import literal_column, func, and_  # case, Select, distinct, exists, alias,  select, update

from sqlalchemy.orm import Session # , joinedload

from pydantic import BaseModel #, validator
from arxiv.base import logging
from arxiv.db import transaction
from arxiv.db.models import PaperOwner

from . import is_admin_user, get_db, datetime_to_epoch, VERY_OLDE, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_admin_user)], prefix="/paper_owners")


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
    def base_select(db: Session):
        return db.query(
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
        db: Session = Depends(get_db)
    ) -> List[OwnershipModel]:
    query = OwnershipModel.base_select(db)

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
        db: Session = Depends(get_db)
    ) -> List[OwnershipModel]:
    query = OwnershipModel.base_select(db)


    if _start < 0 or _end < _start:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    if not current_user.is_admin or user_id != current_user.user_id:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN,
                            details="Not authorized")

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
async def get_ownership(id: str, db: Session = Depends(get_db)) -> OwnershipModel:
    uid, did = to_ids(id)
    if not uid or not did:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST)
    item = OwnershipModel.base_select(db).filter(and_(
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
        session: Session = Depends(transaction)) -> OwnershipModel:

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
        session: Session = Depends(transaction)) -> OwnershipModel:
    body = await request.json()

    item = PaperOwner(**body)
    session.add(item)
    session.commit()
    session.refresh(item)
    return OwnershipModel.model_validate(item)
