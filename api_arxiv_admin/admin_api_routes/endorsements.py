"""arXiv endorsement routes."""
from datetime import timedelta, datetime, date, UTC
from typing import Optional, List
import re

from arxiv.auth.user_claims import ArxivUserClaims
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response

# from sqlalchemy import select, update, func, case, Select, distinct, exists, and_, alias
from sqlalchemy.orm import Session #, joinedload
from sqlalchemy.exc import IntegrityError

from arxiv.base import logging
from arxiv.db.models import Endorsement, EndorsementRequest, TapirUser

from . import get_db, datetime_to_epoch, VERY_OLDE, get_current_user, get_client_host, \
    get_tracking_cookie, get_client_host_name, is_any_user
from .biz.endorsement_biz import EndorsementBusiness
from .biz.endorsement_io import EndorsementDBAccessor
from .endorsement_requsets import EndorsementRequestModel
from .public_users import PublicUserModel
from .user import UserModel
from .dao.endorsement_model import EndorsementModel, EndorsementCodeModel, EndorsementOutcomeModel

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_any_user)], prefix="/endorsements")


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
        type: Optional[List[str] | str] = Query(None, description="user, auto, admin"),
        flag_valid: Optional[bool] = Query(None),
        endorsee_id: Optional[int] = Query(None),
        endorser_id: Optional[int] = Query(None),
        id: Optional[List[int]] = Query(None, description="List of user IDs to filter by"),
        request_id: Optional[int] = Query(None),
        current_user: Optional[ArxivUserClaims] = Depends(get_current_user),
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

    if not current_user.is_admin:
        query = query.filter(Endorsement.endorsee_id == current_user.user_id)

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

        if type is not None:
            if isinstance(type, str):
                query = query.filter(Endorsement.type == type)
            elif isinstance(type, list):
                query = query.filter(Endorsement.type.in_(type))

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
async def get_endorsement(id: int,
                          current_user: Optional[ArxivUserClaims] = Depends(get_current_user),
                          db: Session = Depends(get_db)) -> EndorsementModel:
    item = EndorsementModel.base_select(db).filter(Endorsement.endorsement_id == id).all()
    if item:
        return EndorsementModel.model_validate(item[0])
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement '{id}' not found")


@router.put('/{id:int}')
async def update_endorsement(
        request: Request,
        id: int,
        current_user: Optional[ArxivUserClaims] = Depends(get_current_user),
        session: Session = Depends(get_db)) -> EndorsementModel:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to update endorsements.")
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
        session: Session = Depends(get_db)) -> EndorsementModel:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to create endorsements.")
    item = Endorsement(**request.json())
    session.add(item)
    session.commit()
    session.refresh(item)
    return EndorsementModel.model_validate(item)


async def _endorse(
        session: Session,
        request: Request,
        response: Response,
        endorsement_code: EndorsementCodeModel,
        current_user: ArxivUserClaims,
        tracking_cookie: str | None,
        client_host: str | None,
        client_host_name: str | None,
        audit_timestamp: datetime,
        show_email: bool = False
        ) -> EndorsementOutcomeModel:
    preflight = endorsement_code.preflight
    proto_endorser = UserModel.base_select(session).filter(TapirUser.user_id == endorsement_code.endorser_id).one_or_none()
    if proto_endorser is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Endorser not found")
    endorser = UserModel.model_validate(proto_endorser)

    proto_endorsement_req = EndorsementRequestModel.base_select(session).filter(EndorsementRequest.secret == endorsement_code.endorsement_code).one_or_none()
    if not proto_endorsement_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid endorsement code")
    endorsement_request = EndorsementRequestModel.model_validate(proto_endorsement_req)

    proto_endorsee = PublicUserModel.base_select(session).filter(TapirUser.user_id == endorsement_request.endorsee_id).one_or_none()
    if proto_endorsee is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Endorses not found")
    endorsee = PublicUserModel.model_validate(proto_endorsee)

    accessor = EndorsementDBAccessor(session)
    tapir_session_id = None
    try:
        tapir_session_id = current_user.tapir_session_id
    except AttributeError:
        pass
    business = EndorsementBusiness(
        accessor,
        endorsement_code,
        endorser,
        endorsee,
        endorsement_request,
        tapir_session_id,

        client_host,
        client_host_name,

        audit_timestamp,
        tracking_cookie,
    )

    if not show_email:
        business.endorseE.email = ""

    try:
        acceptable = business.can_submit()
    except Exception as exc:
        logging.error(exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Endorsement criteria is met but failed on database operation") from exc

    if not business.public_reason:
        logging.info("reason %s is emptied as it is not public", business.outcome.reason)
        business.outcome.reason = ""

    if preflight:
        return business.outcome

    if not acceptable:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return business.outcome

    try:
        endorsement = business.submit_endorsement()
        if endorsement:
            business.outcome.endorsement = endorsement
            return business.outcome
        else:
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            response.detail = "Endorsement criteria is met but failed on database operation"
            return business.outcome

    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="During creating endorsement, the database operation failed due to an integrity error.")

    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))

    # NOTREACHED: not reached but please leave this here for back stop
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Endorsement criteria is met but failed on database operation")


@router.post(
    '/endorse',
    description="Create endorsement by a user",
    responses={
        200: {"model": EndorsementOutcomeModel, "description": "Successful endorsement"},
        405: {"model": EndorsementOutcomeModel, "description": "Endorsement not allowed"},
        400: {"description": "Bad request"},
        404: {"description": "Invalid endorsement code"},
    }
)
async def endorse(
        request: Request,
        response: Response,
        endorsement_code: EndorsementCodeModel,
        current_user: ArxivUserClaims = Depends(get_current_user),
        session: Session = Depends(get_db),
        tracking_cookie: str | None = Depends(get_tracking_cookie),
        client_host: str | None = Depends(get_client_host),
        client_host_name: str | None = Depends(get_client_host_name)
        ) -> EndorsementOutcomeModel:
    audit_timestamp = datetime.now(UTC)
    return await _endorse(session, request, response, endorsement_code, current_user, tracking_cookie, client_host, client_host_name, audit_timestamp, show_email=current_user.is_admin)
