import datetime

from arxiv_bizlogic.fastapi_helpers import get_authn
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from typing import Optional, List
from sqlalchemy.orm import Session, aliased
from pydantic import BaseModel, field_validator, ConfigDict
from enum import IntEnum

from arxiv.base import logging
from arxiv.db.models import ShowEmailRequest
from arxiv.auth.user_claims import ArxivUserClaims

from . import is_admin_user, get_db, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_admin_user)], prefix="/show_email_requests")


class ShowEmailRequestsModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    document_id: int
    user_id: int
    session_id: int
    dated: int
    flag_allowed: int
    remote_addr: str
    remote_host: str
    tracking_cookie: str

    @staticmethod
    def base_select(session: Session):
        return session.query(
            ShowEmailRequest.request_id.label("id"),
            ShowEmailRequest.document_id,
            ShowEmailRequest.user_id,
            ShowEmailRequest.session_id,
            ShowEmailRequest.dated,
            ShowEmailRequest.flag_allowed,
            ShowEmailRequest.remote_addr,
            ShowEmailRequest.remote_host,
            ShowEmailRequest.tracking_cookie,
        )


@router.get('/')
async def list_show_email_requests(
        response: Response,
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("DESC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        document_id: Optional[int] = Query(None, description="Document ID"),
        user_id: Optional[int] = Query(None, description="User ID"),
        session: Session = Depends(get_db)
    ) -> List[ShowEmailRequestsModel]:
    query = ShowEmailRequestsModel.base_select(session)

    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    if document_id is not None:
        query = query.filter(ShowEmailRequest.document_id == document_id)

    if user_id is not None:
        query = query.filter(ShowEmailRequest.user_id == user_id)

    order_columns = []
    if _sort:
        keys = _sort.split(",")
        for key in keys:
            if key == "id":
                key = "request_id"
            try:
                order_column = getattr(ShowEmailRequest, key)
                order_columns.append(order_column)
            except AttributeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid sort field")

    # Apply sorting
    for column in order_columns:
        if _order == "DESC":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [ShowEmailRequestsModel.model_validate(item) for item in query.offset(_start).limit(_end - _start).all()]
    return result
