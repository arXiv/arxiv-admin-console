"""arXiv endorsement routes."""

from typing import Optional, List, Any
from fastapi import APIRouter, Query, HTTPException, status, Depends, Request, Response
from pydantic import BaseModel, ConfigDict

from sqlalchemy.orm import Session
from arxiv.db.models import EndorsementRequestsAudit

from . import is_admin_user, get_db
# from .models import EndorsementRequestsAuditModel

router = APIRouter(dependencies=[Depends(is_admin_user)], prefix="/endorsement_requests_audit")

class EndorsementRequestsAuditModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: Optional[int]
    remote_addr: Optional[str]
    remote_host: Optional[str]
    tracking_cookie: Optional[str]

    @classmethod
    def base_select(cls, db: Session):
        return (db.query(
            EndorsementRequestsAudit.request_id.label("id"),
            EndorsementRequestsAudit.session_id,
            EndorsementRequestsAudit.remote_addr,
            EndorsementRequestsAudit.remote_host,
            EndorsementRequestsAudit.tracking_cookie,
        ))

@router.get("/")
async def list_endorsement_requests_audit(
        response: Response,
        _sort: Optional[str] = Query(None, description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        id: Optional[List[int]] = Query(None, description="List of user IDs to filter by"),
        db: Session = Depends(get_db)
) -> List[EndorsementRequestsAuditModel]:
    """

    """
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
                order_column = getattr(EndorsementRequestsAudit, key)
                order_columns.append(order_column)
            except AttributeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid start or end index")

    query = EndorsementRequestsAuditModel.base_select(db)

    if id is not None:
        query = query.filter(EndorsementRequestsAudit.request_id.in_(id))
    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [EndorsementRequestsAuditModel.model_validate(user) for user in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get('/{id:int}')
async def get_endorsement_requests_audit(id: int, db: Session = Depends(get_db)) -> EndorsementRequestsAuditModel:
    item = db.query(EndorsementRequestsAudit).where(EndorsementRequestsAudit.request_id == id)
    if item:
        return EndorsementRequestsAuditModel.model_validate(item[0])
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
