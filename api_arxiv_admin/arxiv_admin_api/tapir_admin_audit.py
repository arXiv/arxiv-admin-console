import datetime

from arxiv.auth.user_claims import ArxivUserClaims
from arxiv_bizlogic.fastapi_helpers import get_db, get_authn
from arxiv_bizlogic.audit_event import AdminAuditActionEnum as TapirAdminActionEnum

from fastapi import APIRouter, Depends, HTTPException, Response, status, Query


from pydantic import BaseModel
from typing import List, Optional
import re
from arxiv.db.models import TapirAdminAudit

from sqlalchemy.orm import Session

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
            TapirAdminAudit.data,
            TapirAdminAudit.comment)


@router.get("/")
async def list_tapir_admin_audit(
        response: Response,
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("DESC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        id: Optional[List[int]] = Query(None, description="List of IDs to filter by"),
        admin_user: Optional[int] = Query(None, description="Admin User id"),
        affected_user: Optional[int] = Query(None, description="affected_user"),
        start_date: Optional[datetime.date] = Query(None, description="Start date for filtering"),
        end_date: Optional[datetime.date] = Query(None, description="End date for filtering"),
        session: Session = Depends(get_db),
        current_user: ArxivUserClaims = Depends(get_authn),
) -> List[TapirAdminAuditModel]:
    gate_admin_user(current_user)
    query = TapirAdminAuditModel.base_select(session)

    if id:
        query = query.filter(TapirAdminAudit.id.in_(id))
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
    result = [TapirAdminAuditModel.model_validate(item) for item in query.offset(_start).limit(_end - _start).all()]
    return result

@router.get("/{id:int}")
async def get_tapir_admin_audit(
        id: int,
        session: Session = Depends(get_db),
        current_user: ArxivUserClaims = Depends(get_authn),
) -> TapirAdminAuditModel:
    gate_admin_user(current_user)
    query = TapirAdminAuditModel.base_query(session)
    item = query.filter(TapirAdminAudit.entry_id == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Not found")
    return TapirAdminAuditModel.model_validate(item)

#
# def describe_action(action: str, data: str, admin_nick: str, affected_nick: str):
#     def link(doc_id, paper_id):
#         return f'<a href="/auth/admin/paper-detail.php?document_id={doc_id}">{paper_id}</a>'
#
#     if action == "add_paper_owner":
#         return f"{admin_nick} made {affected_nick} an owner of paper {link(data, data)}"
#
#     elif action == "add_paper_owner_2":
#         return f"{admin_nick} made {affected_nick} an owner of paper {link(data, data)} through the process-ownership screen"
#
#     elif action == "make_moderator":
#         return f"{admin_nick} made {affected_nick} a moderator of {data}"
#
#     elif action == "unmake_moderator":
#         return f"{admin_nick} revoked {affected_nick} being moderator of {data}"
#
#     elif action == "arXiv_change_status":
#         match = re.match(r"^([^ ]*) -> ([^ ]*)$", data)
#         if match:
#             old_status, new_status = match.groups()
#             return f"{admin_nick} moved {affected_nick} from status {old_status} to {new_status}"
#         return f"{admin_nick} changed status of {affected_nick} with data: {data}"
#
#     elif action == "arXiv_make_author":
#         return f"{admin_nick} made {affected_nick} an author of {link(data, data)}"
#
#     elif action == "arXiv_make_nonauthor":
#         return f"{admin_nick} made {affected_nick} a nonauthor of {link(data, data)}"
#
#     elif action == "arXiv_change_paper_pw":
#         return f"{admin_nick} changed the paper password for {link(data, data)} which was submitted by {affected_nick}"
#
#     elif action == "endorsed_by_suspect":
#         try:
#             endorser_id, category, endorsement_id = data.split(" ")
#             return f"Automated action: {affected_nick} was flagged because they <a href=\"/auth/admin/generic-detail.php?tapir_y=endorsements&tapir_id={endorsement_id}\">was endorsed</a> by user {endorser_id} who is also a suspect."
#         except:
#             return "Malformed data in endorsement record."
#
#     elif action == "got_negative_endorsement":
#         try:
#             endorser_id, category, endorsement_id = data.split(" ")
#             return f"Automated action: {affected_nick} was flagged because they got a <a href=\"/auth/admin/generic-detail.php?tapir_y=endorsements&tapir_id={endorsement_id}\">negative endorsement</a> from user {endorser_id}."
#         except:
#             return "Malformed data in negative endorsement record."
#
