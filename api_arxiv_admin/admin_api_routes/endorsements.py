"""arXiv endorsement routes."""
from datetime import timedelta, datetime, date, UTC
from enum import Enum
from typing import Optional, List
import re

from arxiv.auth.user_claims import ArxivUserClaims
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response

# from sqlalchemy import select, update, func, case, Select, distinct, exists, and_, alias
from sqlalchemy.orm import Session #, joinedload

from pydantic import BaseModel # , validator
from arxiv.base import logging
from arxiv.db import transaction
from arxiv.db.models import Endorsement, EndorsementRequest #, TapirUser

from . import is_admin_user, get_db, datetime_to_epoch, VERY_OLDE, get_current_user, get_client_host, \
    get_tracking_cookie, get_client_host_name
from .biz.endorsement_biz import EndorsementBusiness
from .biz.endorsement_io import EndorsementDBAccessor
from .categories import CategoryModel
from .endorsement_requsets import EndorsementRequestModel
from .user import UserModel

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_admin_user)], prefix="/endorsements")


class EndorsementType(str, Enum):
    user = "user"
    admin = "admin"
    auto = "auto"


class EndorsementModel(BaseModel):
    class Config:
        from_attributes = True

    id: int # Mapped[intpk]
    endorser_id: Optional[int] # Mapped[Optional[int]] = mapped_column(ForeignKey('tapir_users.user_id'), index=True)
    endorsee_id: int # Mapped[int] = mapped_column(ForeignKey('tapir_users.user_id'), nullable=False, index=True, server_default=FetchedValue())
    archive: str #  mapped_column(String(16), nullable=False, server_default=FetchedValue())
    subject_class: str # Mapped[str] = mapped_column(String(16), nullable=False, server_default=FetchedValue())
    flag_valid: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    type: EndorsementType | None # Mapped[Optional[Literal['user', 'admin', 'auto']]] = mapped_column(Enum('user', 'admin', 'auto'))
    point_value: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    issued_when: datetime # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    request_id: int | None # Mapped[Optional[int]] = mapped_column(ForeignKey('arXiv_endorsement_requests.request_id'), index=True)

    arXiv_categories: Optional[CategoryModel] #  = relationship('Category', primaryjoin='and_(Endorsement.archive == Category.archive, Endorsement.subject_class == Category.subject_class)', back_populates='arXiv_endorsements')
    # endorsee_of: List[UserModel] # = relationship('TapirUser', primaryjoin='Endorsement.endorsee_id == TapirUser.user_id', back_populates='endorsee_of')
    # endorser: UserModel # = relationship('TapirUser', primaryjoin='Endorsement.endorser_id == TapirUser.user_id', back_populates='endorses')
    #request: List['EndorsementRequestModel'] # = relationship('EndorsementRequest', primaryjoin='Endorsement.request_id == EndorsementRequest.request_id', back_populates='endorsement')

    @staticmethod
    def base_select(db: Session):
        return db.query(
            Endorsement.endorsement_id.label("id"),
            Endorsement.endorser_id,
            Endorsement.endorsee_id,
            Endorsement.archive,
            Endorsement.subject_class,
            Endorsement.flag_valid,
            Endorsement.type,
            Endorsement.point_value,
            Endorsement.issued_when,
            Endorsement.request_id,
        )


@router.get('/')
async def list_endorsements(
        response: Response,
        _sort: Optional[str] = Query("issued_when", description="sort by"),
        _order: Optional[str] = Query("DESC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        preset: Optional[str] = Query(None),
        start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
        end_date: Optional[datetime] = Query(None, description="End date for filtering"),
        flag_valid: Optional[bool] = Query(None),
        endorsee_id: Optional[int] = Query(None),
        endorser_id: Optional[int] = Query(None),
        id: Optional[List[int]] = Query(None, description="List of user IDs to filter by"),
        request_id: Optional[int] = Query(None),
        db: Session = Depends(get_db)
    ) -> List[EndorsementModel]:
    query = EndorsementModel.base_select(db)

    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    t0 = datetime.now()

    order_columns = []

    if _sort:
        keys = _sort.split(",")
        for key in keys:
            if key == "id":
                key = "endorsement_id"
            try:
                order_column = getattr(Endorsement, key)
                order_columns.append(order_column)
            except AttributeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid start or end index")

    if id is not None:
        query = query.filter(Endorsement.endorsement_id.in_(id))
    else:
        if endorsee_id is not None:
            query = query.filter(Endorsement.endorsee_id == endorsee_id)
        if endorser_id is not None:
            query = query.filter(Endorsement.endorser_id == endorser_id)
        if request_id is not None:
            query = query.filter(Endorsement.request_id == request_id)

        if preset is not None:
            matched = re.search(r"last_(\d+)_days", preset)
            if matched:
                t_begin = datetime_to_epoch(None, t0 - timedelta(days=int(matched.group(1))))
                t_end = datetime_to_epoch(None, t0)
                query = query.filter(Endorsement.issued_when.between(t_begin, t_end))
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid preset format")
        else:
            if start_date or end_date:
                t_begin = datetime_to_epoch(start_date, VERY_OLDE)
                t_end = datetime_to_epoch(end_date, date.today(), hour=23, minute=59, second=59)
                query = query.filter(Endorsement.issued_when.between(t_begin, t_end))

        if flag_valid is not None:
            query = query.filter(Endorsement.flag_valid == flag_valid)

        for column in order_columns:
            if _order == "DESC":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())


    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [EndorsementModel.model_validate(item) for item in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get('/{id:int}')
async def get_endorsement(id: int, db: Session = Depends(get_db)) -> EndorsementModel:
    item = EndorsementModel.base_select(db).filter(Endorsement.endorsement_id == id).all()
    if item:
        return EndorsementModel.model_validate(item[0])
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement '{id}' not found")


@router.put('/{id:int}')
async def update_endorsement(
        request: Request,
        id: int,
        session: Session = Depends(transaction)) -> EndorsementModel:
    body = await request.json()

    item = session.query(Endorsement).filter(Endorsement.endorsement_id == id).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement '{id}' not found")

    # Verify?
    for key, value in body.items():
        if key in item.__dict__:
            setattr(item, key, value)

    session.commit()
    session.refresh(item)  # Refresh the instance with the updated data
    return EndorsementModel.model_validate(item)



@router.post('/', description="Create a new endorsement by admin")
async def create_endorsement(
        request: Request,
        current_user: ArxivUserClaims = Depends(get_current_user),
        session: Session = Depends(transaction)) -> EndorsementModel:
    item = Endorsement(**request.json())
    session.add(item)
    session.commit()
    session.refresh(item)
    return EndorsementModel.model_validate(item)


class EndorsementCodeModel(BaseModel):
    endorser_id: str
    endorsement_code: str
    comment: str
    knows_personally: bool
    seen_paper: bool


@router.post('/endorse', description="Create endorsement by a user")
async def endorse(
        request: Request,
        endorsement_code: EndorsementCodeModel,
        current_user: ArxivUserClaims = Depends(get_current_user),
        session: Session = Depends(transaction),
        tracking_cookie: str | None = Depends(get_tracking_cookie),
        client_host: str | None = Depends(get_client_host),
        client_host_name: str | None = Depends(get_client_host_name)
        ) -> EndorsementModel:

    proto_endorser = UserModel.base_select(session).filter(UserModel.id == endorsement_code.endorser_id).one_or_none()
    if proto_endorser is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Endorser not found")
    endorser = UserModel.model_validate(proto_endorser)

    proto_endorsement_req = EndorsementRequestModel.base_select(session).filter(EndorsementRequest.secret == endorsement_code.endorsement_code).one_or_none()
    if not proto_endorsement_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid endorsement code")
    endorsement_request = EndorsementRequestModel.model_validate(proto_endorsement_req)

    proto_endorsee = UserModel.base_select(session).filter(UserModel.id == endorsement_request.endorsee_id).one_or_none()
    if proto_endorsee is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Endorses not found")
    endorsee = UserModel.model_validate(proto_endorsee)

    audit_timestamp = datetime.now(UTC)
    accessor = EndorsementDBAccessor(session)
    business = EndorsementBusiness(
        accessor,
        endorsement_code,
        endorser,
        endorsee,
        endorsement_request,
        current_user.tapir_session_id,

        client_host,
        client_host_name,

        audit_timestamp,
        tracking_cookie,
    )

    try:
        if business.can_endorse():
            endorsement = business.endorse()
            if endorsement:
                return EndorsementModel.model_validate(endorsement)
        else:
            raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE, detail=business.outcome)

    except Exception as e:
        logging.error(e)
        pass
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Endorsement not found")
