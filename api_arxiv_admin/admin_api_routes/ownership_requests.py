"""arXiv paper ownership routes."""
from __future__ import annotations
import re
import datetime
from enum import Enum
from typing import Optional, Literal, List

from arxiv.auth.user_claims import ArxivUserClaims
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Request

from sqlalchemy.orm import Session
from sqlalchemy import insert, Row
from pydantic import BaseModel

from arxiv.base import logging
from arxiv.db.models import OwnershipRequest, t_arXiv_ownership_requests_papers, PaperOwner, OwnershipRequestsAudit, \
    TapirUser, Document

from . import get_db, is_any_user, get_current_user, datetime_to_epoch, VERY_OLDE, get_client_host, get_tapir_session, \
    TapirSessionData
from .documents import DocumentModel


logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_any_user)], prefix='/ownership_requests')


class WorkflowStatus(str, Enum):
    pending = 'pending'
    accepted = 'accepted'
    rejected = 'rejected'


class OwnershipRequestModel(BaseModel):
    class Config:
        from_attributes = True

    id: int  # request_id
    user_id: int
    endorsement_request_id: Optional[int] = None
    workflow_status: WorkflowStatus # Literal['pending', 'accepted', 'rejected']
    date: Optional[datetime.datetime] = None
    document_ids: Optional[List[int]] = None
    paper_ids: Optional[List[str]] = None

    @classmethod
    def base_query_0(cls, session: Session) -> Query:
        return session.query(
            OwnershipRequest.request_id.label("id"),
            OwnershipRequest.user_id,
            OwnershipRequest.endorsement_request_id,
            OwnershipRequest.workflow_status)

    @classmethod
    def base_query(cls, session: Session) -> Query:
        return session.query(
            OwnershipRequest.request_id.label("id"),
            OwnershipRequest.user_id,
            OwnershipRequest.endorsement_request_id,
            OwnershipRequest.workflow_status,
            OwnershipRequestsAudit.date
            ).join(
                OwnershipRequestsAudit, OwnershipRequest.request_id == OwnershipRequestsAudit.request_id
            )


    @classmethod
    def from_record(cls, record: Row, session: Session) -> OwnershipRequestModel:
        data: OwnershipRequestModel = cls.model_validate(record)
        populate_document_ids(data, record, session)
        return data


class CreateOwnershipRequestModel(BaseModel):
    user_id: Optional[str] = None
    endorsement_request_id: Optional[str] = None
    # Use arXiv IDs or document IDs but not both
    arxiv_ids: Optional[List[str]] = None  # paper ids, not document ids
    document_ids: Optional[List[str]] = None  # not paper ids
    remote_addr: Optional[str] = None


class UpdateOwnershipRequestModel(BaseModel):
    """
        make_owner: This field is checked to determine if the action is to approve ownership. If present, the function proceeds to process the approval of ownership for selected documents.

        approve_<doc_id>: These fields are dynamically generated based on the document IDs. The function looks for keys in the form that start with approve_ followed by a document ID (e.g., approve_123). These represent the documents that the user has selected to approve for ownership.

        is_author: This field is used to determine if the user is an author of the document. It is a boolean field that influences the flag_author attribute when creating a new PaperOwner record.

        reject: This field is checked to determine if the action is to reject the ownership request. If present, the function updates the ownership request status to "rejected".

        revisit: This field is checked to determine if the action is to revisit the ownership request. If present, the function updates the ownership request status to "pending".
    """
    make_owner: bool = False
    is_author: bool = False
    endorsement_request_id: Optional[int] = None
    # Use arXiv IDs or document IDs but not both
    arxiv_ids: Optional[List[str]] = None  # paper ids, not document ids
    document_ids: Optional[List[int]] = None
    remote_addr: Optional[str] = None


class PaperOwnershipDecisionModel(BaseModel):
    workflow_status: WorkflowStatus # Literal['pending', 'accepted', 'rejected']
    rejected_document_ids: List[int]
    accepted_document_ids: List[int]


def populate_document_ids(data: OwnershipRequestModel, record: Row, session: Session):
    data.document_ids = [
        requested.document_id for requested in session.query(
            t_arXiv_ownership_requests_papers.c.document_id
        ).filter(
            t_arXiv_ownership_requests_papers.c.request_id == int(data.id)
        ).all()]

    doc: Document
    data.paper_ids = [doc.paper_id for doc in session.query(Document).filter(Document.document_id.in_(data.document_ids)).all() ]


@router.get("/")
def list_ownership_requests(
        response: Response,
        _sort: Optional[str] = Query("last_name,first_name", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        preset: Optional[str] = Query(None),
        start_date: Optional[datetime.date] = Query(None, description="Start date for filtering"),
        end_date: Optional[datetime.date] = Query(None, description="End date for filtering"),
        id: Optional[List[int]] = Query(None, description="List of ownership request IDs to filter by"),
        current_id: Optional[int] = Query(None, description="Current ID - index position - for navigation"),
        user_id: Optional[int] = Query(None),
        endorsement_request_id: Optional[int] = Query(None),
        workflow_status: Optional[Literal['pending', 'accepted', 'rejected']] = Query(None),
        session: Session = Depends(get_db),
        current_user: ArxivUserClaims = Depends(get_current_user),
    ) -> List[OwnershipRequestModel]:
    query = OwnershipRequestModel.base_query(session)
    order_columns = []

    if id is not None:
        query = query.filter(OwnershipRequest.request_id.in_(id))
        _start = None
        _end = None
        if not current_user.is_admin:
            query = query.filter(OwnershipRequest.user_id == current_user.user_id)
    else:
        if preset is not None or start_date is not None or end_date is not None:
            t0 = datetime.datetime.now(datetime.UTC)
            if preset is not None:
                matched = re.search(r"last_(\d+)_days", preset)
                if matched:
                    t_begin = datetime_to_epoch(None, t0 - datetime.timedelta(days=int(matched.group(1))))
                    t_end = datetime_to_epoch(None, t0)
                    query = query.filter(OwnershipRequestsAudit.date.between(t_begin, t_end))
                else:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Invalid preset format")
            else:
                if start_date or end_date:
                    t_begin = datetime_to_epoch(start_date, VERY_OLDE)
                    t_end = datetime_to_epoch(end_date, datetime.date.today(), hour=23, minute=59, second=59)
                    query = query.filter(OwnershipRequestsAudit.date.between(t_begin, t_end))

        if user_id:
            if not current_user.is_admin and str(current_user.user_id) != str(user_id):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")
            query = query.filter(OwnershipRequest.user_id == user_id)
        else:
            if not current_user.is_admin:
                query = query.filter(OwnershipRequest.user_id == current_user.user_id)

        if workflow_status is not None:
            query = query.filter(OwnershipRequest.workflow_status == workflow_status)

        if endorsement_request_id is not None:
            query = query.filter(OwnershipRequest.endorsement_request_id == endorsement_request_id)

        if current_id is not None:
            # This is used to navigate
            _order = "ASC"
            _sort = "request_id"
            prev_req = (
                session.query(OwnershipRequest)
                .filter(OwnershipRequest.request_id < current_id)
                .order_by(OwnershipRequest.request_id.desc())
                .first()
            )

            next_req = (
                session.query(OwnershipRequest)
                .filter(OwnershipRequest.request_id > current_id)
                .order_by(OwnershipRequest.request_id.asc())
                .first()
            )
            query = query.filter(OwnershipRequest.request_id.between(prev_req.request_id, next_req.request_id))

        if _sort:
            keys = _sort.split(",")
            for key in keys:
                if key == "id":
                    key = "request_id"
                try:
                    order_column = getattr(OwnershipRequest, key)
                    order_columns.append(order_column)
                except AttributeError:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Invalid start or end index")

    for column in order_columns:
        if _order == "DESC":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [OwnershipRequestModel.from_record(item, session) for item in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get("/{id:int}")
async def get_ownership_request(
        id: int,
        current_user: ArxivUserClaims = Depends(get_current_user),
        session: Session = Depends(get_db),
    ) ->OwnershipRequestModel:
    query = OwnershipRequestModel.base_query(session).filter(OwnershipRequest.request_id == id)
    if not current_user.is_admin:
        query = query.filter(OwnershipRequest.user_id == current_user.user_id)
    oreq = query.one_or_none()
    if oreq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return OwnershipRequestModel.from_record(oreq, session)



@router.post('/')
async def create_ownership_request(
        request: Request,
        ownership_request: CreateOwnershipRequestModel,
        current_user: ArxivUserClaims = Depends(get_current_user),
        current_tapir_session: TapirSessionData = Depends(get_tapir_session),
        session: Session = Depends(get_db)) -> OwnershipRequestModel:
    """Create ownership request.
   $auth->conn->begin();

   $sql="INSERT INTO arXiv_ownership_requests (user_id,workflow_status,endorsement_request_id) VALUES ($auth->user_id,'pending',$_endorsement_request_id)";
   $auth->conn->query($sql);

   $sql="INSERT INTO arXiv_ownership_requests_audit (request_id,remote_addr,remote_host,session_id,tracking_cookie,date) VALUES (LAST_INSERT_ID(),'$_remote_addr','$_remote_host','$_session_id','$_tracking_cookie',{$auth->timestamp})";
   $auth->conn->query($sql);

   foreach($documents as $document_id) {
      $sql="INSERT INTO arXiv_ownership_requests_papers (request_id,document_id) VALUES (LAST_INSERT_ID(),$document_id)";
      $auth->conn->query($sql);
   }

   $request_id=$auth->conn->select_scalar("SELECT LAST_INSERT_ID()");
   $auth->conn->commit();
    """
    expected_len = -1
    if ownership_request.document_ids and ownership_request.arxiv_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use arxiv ids or document ids but not both at the same time")
    elif ownership_request.document_ids:
        expected_len = len(ownership_request.document_ids)
        documents = DocumentModel.base_select(session).filter(Document.document_id.in_(ownership_request.document_ids)).all()
    elif ownership_request.arxiv_ids:
        expected_len = len(ownership_request.arxiv_ids)
        documents = DocumentModel.base_select(session).filter(Document.paper_id.in_(ownership_request.arxiv_ids)).all()
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No arxiv ids or document ids")

    if len(documents) != expected_len:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Some of documents do not exist.")

    user_id = ownership_request.user_id if ownership_request.user_id else current_user.user_id

    # ownerships = [OwnershipModel.model_validate(paper) for paper in OwnershipModel.base_select(session).filter(PaperOwner.document_id.in_(ownership_request.document_ids)).filter(PaperOwner.user_id == user_id).all()]
    # ids = [ownerhip.id for ownerhip in ownerships]

    request_date = datetime.date.today()
    #     request_id: Mapped[intpk]
    #     user_id: Mapped[int] = mapped_column(ForeignKey('tapir_users.user_id'), nullable=False, index=True, server_default=FetchedValue())
    #     endorsement_request_id: Mapped[Optional[int]] = mapped_column(ForeignKey('arXiv_endorsement_requests.request_id'), index=True)
    #     workflow_status: Mapped[Literal['pending', 'accepted', 'rejected']] = mapped_column(Enum('pending', 'accepted', 'rejected'), nullable=False, server_default=FetchedValue())

    req = OwnershipRequest(
        user_id = user_id,
        endorsement_request_id = ownership_request.endorsement_request_id,
        workflow_status = 'pending'
    )
    session.add(req)
    session.flush()
    session.refresh(req)

    #    $sql="INSERT INTO arXiv_ownership_requests_audit (request_id,remote_addr,remote_host,session_id,tracking_cookie,date) VALUES (LAST_INSERT_ID(),'$_remote_addr','$_remote_host','$_session_id','$_tracking_cookie',{$auth->timestamp})";

    audit = OwnershipRequestsAudit(
        request_id = req.request_id,
        session_id = int(current_tapir_session.session_id),
        remote_addr = ownership_request.remote_addr,
        remote_host = "",
        tracking_cookie = "",
        date = datetime_to_epoch(None, request_date)
    )
    session.add(audit)
    session.flush()
    session.refresh(audit)

    for document in documents:
        # $sql = "INSERT INTO arXiv_ownership_requests_papers (request_id,document_id) VALUES (LAST_INSERT_ID(),$document_id)";
        stmt = insert(t_arXiv_ownership_requests_papers).values(
            request_id=req.request_id,
            document_id=document.id
        )
        session.execute(stmt)

    session.flush()
    refreshed_req = OwnershipRequestModel.base_query(session).filter(OwnershipRequest.request_id == req.request_id).one_or_none()
    if refreshed_req is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error")
    session.commit()
    return OwnershipRequestModel.from_record(refreshed_req, session)


@router.put("/{id:int}")
async def update_ownership_request(
        id: int,
        request: Request,
        ownership_request: UpdateOwnershipRequestModel,
        current_user: ArxivUserClaims = Depends(get_current_user),
        current_tapir_session: TapirSessionData = Depends(get_tapir_session),
        session: Session = Depends(get_db)) -> OwnershipRequestModel:
    """Update ownership request.


   $auth->conn->begin();

   $sql="INSERT INTO arXiv_ownership_requests (user_id,workflow_status,endorsement_request_id) VALUES ($auth->user_id,'pending',$_endorsement_request_id)";
   $auth->conn->query($sql);

   $sql="INSERT INTO arXiv_ownership_requests_audit (request_id,remote_addr,remote_host,session_id,tracking_cookie,date) VALUES (LAST_INSERT_ID(),'$_remote_addr','$_remote_host','$_session_id','$_tracking_cookie',{$auth->timestamp})";
   $auth->conn->query($sql);

   foreach($documents as $document_id) {
      $sql="INSERT INTO arXiv_ownership_requests_papers (request_id,document_id) VALUES (LAST_INSERT_ID(),$document_id)";
      $auth->conn->query($sql);
   }

   $request_id=$auth->conn->select_scalar("SELECT LAST_INSERT_ID()");
   $auth->conn->commit();

    """

    document = DocumentModel.base_select(session).filter(Document.document_id == id).one_or_none()
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    user_id = ownership_request.user_id if ownership_request.user_id else current_user.user_id

    # ownerships = [OwnershipModel.model_validate(paper) for paper in OwnershipModel.base_select(session).filter(PaperOwner.document_id.in_(ownership_request.document_ids)).filter(PaperOwner.user_id == user_id).all()]
    # ids = [ownerhip.id for ownerhip in ownerships]

    request_date = datetime.date.today()
    #     request_id: Mapped[intpk]
    #     user_id: Mapped[int] = mapped_column(ForeignKey('tapir_users.user_id'), nullable=False, index=True, server_default=FetchedValue())
    #     endorsement_request_id: Mapped[Optional[int]] = mapped_column(ForeignKey('arXiv_endorsement_requests.request_id'), index=True)
    #     workflow_status: Mapped[Literal['pending', 'accepted', 'rejected']] = mapped_column(Enum('pending', 'accepted', 'rejected'), nullable=False, server_default=FetchedValue())
    req = OwnershipRequest(
        user_id = user_id,
        endorsement_request_id = ownership_request.endorsement_request_id,
        workflow_status = 'pending'
    )
    session.add(req)
    session.flush()
    session.refresh(req)

    #    $sql="INSERT INTO arXiv_ownership_requests_audit (request_id,remote_addr,remote_host,session_id,tracking_cookie,date) VALUES (LAST_INSERT_ID(),'$_remote_addr','$_remote_host','$_session_id','$_tracking_cookie',{$auth->timestamp})";

    audit = OwnershipRequestsAudit(
        request_id = req.request_id,
        session_id = int(current_tapir_session.session_id),
        remote_addr = ownership_request.remote_addr,
        remote_host = "",
        tracking_cookie = "",
        date = datetime_to_epoch(None, request_date)
    )
    session.add(audit)
    session.flush()
    session.refresh(audit)

    for doc_id in ownership_request.document_ids:
        # $sql = "INSERT INTO arXiv_ownership_requests_papers (request_id,document_id) VALUES (LAST_INSERT_ID(),$document_id)";
        a_o_r_p = t_arXiv_ownership_requests_papers(
            request_id = req.request_id,
            document_id = doc_id,
        )
        session.add(a_o_r_p)

    session.commit()

    return OwnershipRequestModel.from_record(req, session)


@router.post('/{request_id:int}/documents/')
async def create_paper_ownership_decision(
        request: Request,
        request_id: int,
        decision: PaperOwnershipDecisionModel,
        current_user: ArxivUserClaims = Depends(get_current_user),
        remote_addr: str = Depends(get_client_host),
        session: Session = Depends(get_db)) -> OwnershipRequestModel:
    """Ownership creation

    """
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    ownership_request = OwnershipRequestModel.base_query(session).filter(OwnershipRequest.request_id == request_id).one_or_none()

    if ownership_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ownership request not found")

    if ownership_request.workflow_status not in [ws.value for ws in WorkflowStatus]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"workflow_status {ownership_request.workflow_status} is invalid")

    if ownership_request.workflow_status != WorkflowStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"workflow_status {ownership_request.workflow_status} is not pending")

    user_id = ownership_request.user_id
    admin_id = current_user.user_id

    current_request: OwnershipRequestModel = OwnershipRequestModel.from_record(None, ownership_request)
    docs = set(current_request.document_ids)
    decided_docs = set(decision.accepted_document_ids) | set(decision.rejected_document_ids)
    if docs != decided_docs:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Not all papers decided")

    if decision.workflow_status == WorkflowStatus.accepted and not decision.accepted_document_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"No accepted documents")

    ownership_request.workflow_status = decision.workflow_status

    already_owns: [int] = [po.document_id for po in session.query(PaperOwner).filter(PaperOwner.user_id == user_id).all()]

    accepting = set(decision.accepted_document_ids)
    accepting.remove(set(already_owns))

    user: TapirUser = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()

    t_now = datetime.datetime.now(datetime.UTC)
    for doc_id in accepting:
        po = PaperOwner(
            document_id=doc_id,
            user_id=user_id,
            date=t_now,
            added_by=admin_id,
            remote_addr=remote_addr,
            tracking_cookie=user.tracking_cookie,
            valid=True,
            flag_auto=False,
            flag_author=True
        )
        session.add(po)

    session.commit()
    session.refresh(ownership_request)
    return OwnershipRequestModel.from_record(ownership_request, session)
