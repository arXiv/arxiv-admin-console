"""arXiv paper ownership routes."""
import re
from datetime import datetime, date, timedelta
from enum import Enum
from typing import Optional, Literal, List, Any

import sqlalchemy.orm
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response

from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel

from arxiv.base import logging
# from arxiv.db import transaction
from arxiv.db.models import OwnershipRequest, OwnershipRequestsAudit

from . import is_admin_user, get_db, is_any_user, datetime_to_epoch, VERY_OLDE
# from .models import OwnershipRequestsAuditModel

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_any_user)], prefix='/ownership_requests_audit')

class OwnershipRequestsAuditModel(BaseModel):
    class Config:
        from_attributes = True

    id: int  # request_id
    session_id: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    remote_addr: str # Mapped[str] = mapped_column(String(16), nullable=False, server_default=FetchedValue())
    remote_host: str # Mapped[str] = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    tracking_cookie: str# Mapped[str] = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    date: datetime # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())

    @classmethod
    def base_query(cls, session: Session) -> sqlalchemy.orm.Query[Any]:
        return session.query(
            OwnershipRequestsAudit.request_id.label("id"),
            OwnershipRequestsAudit.session_id,
            OwnershipRequestsAudit.remote_addr,
            OwnershipRequestsAudit.remote_host,
            OwnershipRequestsAudit.tracking_cookie,
            OwnershipRequestsAudit.date,
        )

@router.get("/")
def list_ownership_requests_audit(
        response: Response,
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        preset: Optional[str] = Query(None),
        start_date: Optional[date] = Query(None, description="Start date for filtering"),
        end_date: Optional[date] = Query(None, description="End date for filtering"),
        id: Optional[List[int]] = Query(None, description="List of user IDs to filter by"),
        session: Session = Depends(get_db),
    ) -> List[OwnershipRequestsAuditModel]:

    if id is None:
        order_columns = []
        if _sort:
            keys = _sort.split(",")
            for key in keys:
                if key == "id":
                    key = "request_id"
                try:
                    order_column = getattr(OwnershipRequestsAudit, key)
                    order_columns.append(order_column)
                except AttributeError:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Invalid start or end index")

        if preset is not None or start_date is not None or end_date is not None:
            t0 = datetime.now()
            query = session.query(
                OwnershipRequest,
                OwnershipRequestsAudit
            ).join(
                OwnershipRequestsAudit, OwnershipRequest.request_id == OwnershipRequestsAudit.request_id
            )

            if preset is not None:
                matched = re.search(r"last_(\d+)_days", preset)
                if matched:
                    t_begin = datetime_to_epoch(None, t0 - timedelta(days=int(matched.group(1))))
                    t_end = datetime_to_epoch(None, t0)
                    query = query.filter(OwnershipRequestsAudit.date.between(t_begin, t_end))
                else:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Invalid preset format")
            else:
                if start_date or end_date:
                    t_begin = datetime_to_epoch(start_date, VERY_OLDE)
                    t_end = datetime_to_epoch(end_date, date.today(), hour=23, minute=59, second=59)
                    query = query.filter(OwnershipRequestsAudit.date.between(t_begin, t_end))
        else:
            query = OwnershipRequestsAuditModel.base_query(session)

        if _start < 0 or _end < _start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid start or end index")

    else:
        query = OwnershipRequestsAuditModel.base_query(session)
        query = query.filter(OwnershipRequestsAudit.request_id.in_(id))

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [OwnershipRequestsAuditModel.model_validate(item) for item in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get("/{id:int}")
def get_ownership_requests_audit(
        id: int,
        session: Session = Depends(get_db),
    ) -> List[OwnershipRequestsAuditModel]:
    req = OwnershipRequestsAuditModel.base_query(session).filter(OwnershipRequestsAudit.request_id == id).all()
    if req is None:
        return Response(status_code=404)
    result = [OwnershipRequestsAuditModel.model_validate(item) for item in req]
    return result

