"""arXiv endorsement routes."""
import re
from datetime import timedelta, datetime, date, UTC
from sqlite3 import IntegrityError
from typing import Optional, List

from arxiv.auth.user_claims import ArxivUserClaims
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response

from sqlalchemy import case # select, update, func, Select, distinct, exists, and_, or_
from sqlalchemy.orm import Session #, joinedload

from pydantic import BaseModel
from arxiv.base import logging
from arxiv.db.models import EndorsementRequest, Demographic, TapirNickname

from . import get_db, datetime_to_epoch, VERY_OLDE, is_any_user, get_current_user #  is_admin_user,
from .biz.endorsement_coed import endorsement_code
# from .categories import CategoryModel
from .dao.endorsement_request_model import EndorsementRequestRequestModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/endorsement_requests", dependencies=[Depends(is_any_user)])


class EndorsementRequestModel(BaseModel):
    class Config:
        from_attributes = True

    id: Optional[int] = None
    endorsee_id: Optional[int] = None
    archive: Optional[str] = None
    subject_class: Optional[str] = None
    secret: Optional[str] = None
    flag_valid: Optional[bool] = None
    flag_open: Optional[bool] = None
    issued_when: Optional[datetime] = None
    flag_suspect: Optional[bool] = None

    endorsee_username: Optional[str] = None

    @staticmethod
    def base_select(db: Session):

        return db.query(
            EndorsementRequest.request_id.label("id"),
            EndorsementRequest.endorsee_id,
            EndorsementRequest.archive,
            EndorsementRequest.subject_class,
            EndorsementRequest.secret,
            EndorsementRequest.flag_valid,
            case(
                (EndorsementRequest.point_value == 0, True),
                else_=False
            ).label("flag_open"),
            EndorsementRequest.issued_when,
            EndorsementRequest.point_value,
            Demographic.flag_suspect.label("flag_suspect"),
            TapirNickname.nickname.label("endorsee_username")
            # Endorsee ID (single value)
            #TapirUser.user_id.label("endorsee"),
            # Endorsement ID (single value)
            #Endorsement.endorsement_id.label("endorsement"),
            # Audit ID (single value)
            #EndorsementRequestsAudit.session_id.label("audit")
        ).outerjoin(
            Demographic, Demographic.user_id == EndorsementRequest.endorsee_id
        ).outerjoin(
            TapirNickname, TapirNickname.user_id == EndorsementRequest.endorsee_id,
        )
    pass


@router.get('/')
async def list_endorsement_requests(
        response: Response,
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        preset: Optional[str] = Query(None),
        start_date: Optional[date] = Query(None, description="Start date for filtering"),
        end_date: Optional[date] = Query(None, description="End date for filtering"),
        flag_valid: Optional[bool] = Query(None),
        not_positive: Optional[bool] = Query(None, description="Not positive point value"),
        suspected: Optional[bool] = Query(None, description="Suspected user"),
        current_user: ArxivUserClaims = Depends(get_current_user),
        db: Session = Depends(get_db),

    ) -> List[EndorsementRequestModel]:

    query = EndorsementRequestModel.base_select(db)

    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    order_columns = []
    if _sort:
        keys = _sort.split(",")
        for key in keys:
            if key == "id":
                key = "request_id"
            try:
                order_column = getattr(EndorsementRequest, key)
                order_columns.append(order_column)
            except AttributeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid start or end index")

    t0 = datetime.now()

    if preset is not None:
        matched = re.search(r"last_(\d+)_days", preset)
        if matched:
            t_begin = datetime_to_epoch(None, t0 - timedelta(days=int(matched.group(1))))
            t_end = datetime_to_epoch(None, t0)
            query = query.filter(EndorsementRequest.issued_when.between(t_begin, t_end))
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid preset format")
    else:
        if start_date or end_date:
            t_begin = datetime_to_epoch(start_date, VERY_OLDE)
            t_end = datetime_to_epoch(end_date, date.today(), hour=23, minute=59, second=59)
            query = query.filter(EndorsementRequest.issued_when.between(t_begin, t_end))

    if not (current_user.is_admin or current_user.is_mod):
        query = query.filter(EndorsementRequest.endorsee_id == current_user.user_id)

    if flag_valid is not None:
        query = query.filter(EndorsementRequest.flag_valid == flag_valid)

    for column in order_columns:
        if _order == "DESC":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    if not_positive is not None:
        if not_positive:
            query = query.filter(EndorsementRequest.point_value <= 0)
        else:
            query = query.filter(EndorsementRequest.point_value > 0)

    if suspected is not None:
        query = query.join(Demographic, Demographic.user_id == EndorsementRequest.endorsee_id)
        query = query.filter(Demographic.flag_suspect == suspected)

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [EndorsementRequestModel.model_validate(item) for item in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get('/{id:int}')
async def get_endorsement_request(id: int,
                                  current_user: ArxivUserClaims = Depends(get_current_user),
                                  db: Session = Depends(get_db)) -> EndorsementRequestModel:
    item: EndorsementRequest = EndorsementRequestModel.base_select(db).filter(EndorsementRequest.request_id == id).one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement request with id {id} not found")

    if current_user.user_id != item.endorsee_id and (not (current_user.is_admin or current_user.is_mod)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")
    return EndorsementRequestModel.model_validate(item)


@router.put('/{id:int}', dependencies=[Depends(is_any_user)])
async def update_endorsement_request(
        id: int,
        body: EndorsementRequestModel,
        current_user: ArxivUserClaims = Depends(get_current_user),
        session: Session = Depends(get_db)) -> EndorsementRequestModel:

    item: EndorsementRequest | None = session.query(EndorsementRequest).filter(EndorsementRequest.request_id == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement request with id {id} not found")

    if current_user.user_id != item.endorsee_id and (not (current_user.is_admin or current_user.is_mod)):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to perform this action")

    #
    if body.flag_open is not None:
        if body.flag_open == False and item.point_value == 0:
            item.point_value = 10
        if body.flag_open == True and item.point_value == 10:
            item.point_value = 0

    if body.flag_valid is not None:
        item.flag_valid = body.flag_valid

    if current_user.is_admin:
        if body.archive is not None:
            item.archive = body.archive
            item.subject_class = body.subject_class
    session.add(item)
    session.commit()
    session.refresh(item)  # Refresh the instance with the updated data
    updated = EndorsementRequestModel.base_select(session).filter(EndorsementRequest.request_id == id).one_or_none()
    return EndorsementRequestModel.model_validate(updated)


@router.post('/')
async def create_endorsement_request(
        respones: Response,
        body: EndorsementRequestRequestModel,
        current_user: ArxivUserClaims = Depends(get_current_user),
        session: Session = Depends(get_db)) -> EndorsementRequestModel:
    endorsee_id = body.endorsee_id
    if endorsee_id is None:
        endorsee_id = current_user.user_id

    if endorsee_id != current_user.user_id and (not current_user.is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to create endorsement for other users.")

    timestamp = datetime_to_epoch(None, datetime.now(UTC))
    er: EndorsementRequest
    for _ in range(10):
        code = endorsement_code()
        er = EndorsementRequest(
            endorsee_id=endorsee_id,
            archive=body.archive,
            subject_class=body.subject_class,
            secret=code,
            flag_valid=1,
            issued_when=timestamp,
            point_value=0)
        try:
            session.add(er)
            session.commit()
            session.refresh(er)
        except IntegrityError:
            pass
        except Exception as exc:
            logger.error(f"Creating Endorsement request failed", exc_info=exc)
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unknown database opesation error " + str(exc)) from exc
        if er is not None:
            break
    else:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Code creation failed")

    respones.status_code = status.HTTP_201_CREATED
    erm = EndorsementRequestModel.base_select(session).filter(EndorsementRequest.request_id == er.request_id).one_or_none()
    if erm is None:
        msg = f"Endorsement request {er.request_id} is created but not accessible"
        logger.warning(msg)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=msg)
    logger.info(f"Endorsement request {er.request_id} is created successfully.")
    return EndorsementRequestModel.model_validate(erm)


@router.delete('/{id:int}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_endorsement_request(
        id: int,
        current_user: ArxivUserClaims = Depends(get_current_user),
        session: Session = Depends(get_db)) -> Response:
    if not current_user.is_admin:
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    item: EndorsementRequest | None = session.query(EndorsementRequest).filter(EndorsementRequest.request_id == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="User not found")

    session.delete(item)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/code')
async def get_endorsement_request_by_secret(
        secret: str = Query(None, description="Find an endorsement request by code"),
        current_user: ArxivUserClaims = Depends(get_current_user),
        db: Session = Depends(get_db)
) -> EndorsementRequestModel:
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Please log in first")
    item: EndorsementRequest = EndorsementRequestModel.base_select(db).filter(EndorsementRequest.secret == secret).one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement request with code {secret} not found")
    return EndorsementRequestModel.model_validate(item)
