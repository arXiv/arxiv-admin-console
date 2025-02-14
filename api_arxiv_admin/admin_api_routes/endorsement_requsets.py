"""arXiv endorsement routes."""
import re
from datetime import timedelta, datetime, date
from typing import Optional, List

from arxiv.auth.user_claims import ArxivUserClaims
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response

from sqlalchemy import case # select, update, func, Select, distinct, exists, and_, or_
from sqlalchemy.orm import Session, joinedload

from pydantic import BaseModel
from arxiv.base import logging
from arxiv.db import transaction
from arxiv.db.models import Endorsement, EndorsementRequest, Demographic, TapirUser, Category, \
    EndorsementRequestsAudit, EndorsementRequestsAudit

from . import is_admin_user, get_db, datetime_to_epoch, VERY_OLDE, is_any_user, get_current_user
from .categories import CategoryModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/endorsement_requests", dependencies=[Depends(is_any_user)])


class EndorsementRequestModel(BaseModel):
    class Config:
        from_attributes = True

    id: int
    endorsee_id: int
    archive: str
    subject_class: str
    secret: str
    flag_valid: bool
    flag_open: bool
    issued_when: datetime
    point_value: int
    flag_suspect: bool

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

            # Endorsee ID (single value)
            #TapirUser.user_id.label("endorsee"),
            # Endorsement ID (single value)
            #Endorsement.endorsement_id.label("endorsement"),
            # Audit ID (single value)
            #EndorsementRequestsAudit.session_id.label("audit")
        ).outerjoin(
            Demographic,
            Demographic.user_id == EndorsementRequest.endorsee_id,
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if current_user.user_id != item.endorsee_id and (not (current_user.is_admin or current_user.is_mod)):
        return Response(status_code=status.HTTP_403_FORBIDDEN)
    return EndorsementRequestModel.model_validate(item)


@router.put('/{id:int}', dependencies=[Depends(is_any_user)])
async def update_endorsement_request(
        request: Request,
        id: int,
        current_user: ArxivUserClaims = Depends(get_current_user),
        session: Session = Depends(transaction)) -> EndorsementRequestModel:
    body = await request.json()

    item = session.query(EndorsementRequest).filter(EndorsementRequest.request_id == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Endorsement request not found")

    if current_user.user_id != item.endorsee_id and (not (current_user.is_admin or current_user.is_mod)):
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    #
    flag_open = body.gep("flag_open")
    if flag_open == False and item.point_value == 0:
        item.point_value = 10

    item.flag_valid = body.gep("flag_valid", item.flag_valid)
    session.commit()
    session.refresh(item)  # Refresh the instance with the updated data
    updated = EndorsementRequestModel.base_select(session).filter(EndorsementRequest.request_id == id).one_or_none()
    return EndorsementRequestModel.model_validate(updated)


@router.post('/')
async def create_endorsement_request(
        request: Request,
        session: Session = Depends(transaction)) -> EndorsementRequestModel:
    body = await request.json()
    # ID is decided after added
    if "id" in body:
        del body["id"]

    item = EndorsementRequest(**body)
    session.add(item)
    session.commit()
    session.refresh(item)
    return EndorsementRequestModel.model_validate(item)


@router.delete('/{id:int}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_endorsement_request(
        id: int,
        current_user: ArxivUserClaims = Depends(get_current_user),
        session: Session = Depends(transaction)) -> Response:

    item: EndorsementRequest = session.query(EndorsementRequest).filter(EndorsementRequest.request_id == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="User not found")

    if current_user.user_id != item.endorsee_id and (not (current_user.is_admin or current_user.is_mod)):
        return Response(status_code=status.HTTP_403_FORBIDDEN)

    item.delete_instance()
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
