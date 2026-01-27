import datetime

from arxiv.auth.user_claims import ArxivUserClaims
from arxiv_bizlogic.fastapi_helpers import get_db, get_authn, get_authn_user
from arxiv_bizlogic.audit_event import AdminAuditActionEnum as TapirAdminActionEnum

from fastapi import APIRouter, Depends, HTTPException, Response, status, Query


from pydantic import BaseModel
from typing import List, Optional
import re
from arxiv.db.models import TapirAdminAudit
from sqlalchemy import LargeBinary, cast

from sqlalchemy.orm import Session
from arxiv_bizlogic.sqlalchemy_helper import sa_model_to_pydandic_model

from arxiv_admin_api import gate_admin_user

router = APIRouter(prefix="/tapir_admin_audit")



class TapirAdminAuditModel(BaseModel):
    id: int  # entry id - thank god it has a p-key
    log_date: datetime.datetime
    session_id: Optional[int]
    ip_addr: str
    remote_host: str
    admin_user: Optional[int]
    affected_user: int
    tracking_cookie: str
    action: TapirAdminActionEnum
    data: str
    comment: str

    class Config:
        from_attributes = True

    @staticmethod
    def base_select(session: Session):
        return session.query(
            TapirAdminAudit.entry_id.label("id"),
            TapirAdminAudit.log_date,
            TapirAdminAudit.session_id,
            TapirAdminAudit.ip_addr,
            TapirAdminAudit.remote_host,
            TapirAdminAudit.admin_user,
            TapirAdminAudit.affected_user,
            TapirAdminAudit.tracking_cookie,
            TapirAdminAudit.action,
            cast(TapirAdminAudit.data, LargeBinary).label("data"),
            cast(TapirAdminAudit.comment, LargeBinary).label("comment"))


@router.get("/")
async def list_tapir_admin_audit(
        response: Response,
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("DESC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        id: Optional[List[int]] = Query(None, description="List of IDs to filter by"),
        admin_user: Optional[int] = Query(None, description="Admin User id"),
        affected_user: Optional[int] = Query(None, description="affected_user"),
        start_date: Optional[datetime.date] = Query(None, description="Start date for filtering"),
        end_date: Optional[datetime.date] = Query(None, description="End date for filtering"),
        session: Session = Depends(get_db),
        current_user: ArxivUserClaims = Depends(get_authn_user),
) -> List[TapirAdminAuditModel]:
    gate_admin_user(current_user)
    query = TapirAdminAuditModel.base_select(session)

    if id:
        query = query.filter(TapirAdminAudit.entry_id.in_(id))
    else:
        if _start < 0 or _end < _start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid start or end index")

        order_columns = []
        if _sort:
            keys = _sort.split(",")
            for key in keys:
                if key == "id":
                    key = "entry_id"

                try:
                    order_column = getattr(TapirAdminAudit, key)
                    order_columns.append(order_column)
                except AttributeError:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Invalid start or end index")

        if admin_user:
            query = query.filter(TapirAdminAudit.admin_user == admin_user)

        if affected_user:
            query = query.filter(TapirAdminAudit.affected_user == affected_user)

        for column in order_columns:
            if _order == "DESC":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [TapirAdminAuditModel.model_validate(sa_model_to_pydandic_model(item, TapirAdminAuditModel)) for item in query.offset(_start).limit(_end - _start).all()]
    return result

@router.get("/{id:int}")
async def get_tapir_admin_audit(
        id: int,
        session: Session = Depends(get_db),
        current_user: ArxivUserClaims = Depends(get_authn_user),
) -> TapirAdminAuditModel:
    gate_admin_user(current_user)
    query = TapirAdminAuditModel.base_select(session)
    item = query.filter(TapirAdminAudit.entry_id == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Not found")
    return TapirAdminAuditModel.model_validate(sa_model_to_pydandic_model(item, TapirAdminAuditModel))

