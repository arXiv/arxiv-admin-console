"""arXiv paper ownership routes."""
from __future__ import annotations
import re
import datetime
from enum import Enum, StrEnum
from typing import Optional, Literal, List, Generic, TypeVar, Set, cast
import hashlib

from arxiv.auth.user_claims import ArxivUserClaims
from arxiv_bizlogic.audit_event import admin_audit, AdminAudit_AddPaperOwner2
from arxiv_bizlogic.bizmodels.user_model import UserModel
from arxiv_bizlogic.fastapi_helpers import get_client_host_name, get_authn, get_authn_user
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Request
from sqlalchemy.exc import IntegrityError

from sqlalchemy.orm import Session, Query as OrmQuery
from sqlalchemy import insert, Row, and_
from pydantic import BaseModel, Field

from arxiv.base import logging
from arxiv.db.models import OwnershipRequest, t_arXiv_ownership_requests_papers, PaperOwner, OwnershipRequestsAudit, \
    TapirUser, Document

from . import get_db, is_any_user, get_current_user, datetime_to_epoch, VERY_OLDE, get_client_host, get_tapir_session, \
    TapirSessionData, get_tracking_cookie
from .documents import DocumentModel
from .paper_owners import ownership_combo_key

T = TypeVar('T')
class Partial(Generic[T]):
    pass

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_any_user)], prefix='/ownership_requests')


class WorkflowStatus(StrEnum):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'


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
    def base_query_0(cls, session: Session) -> OrmQuery:
        return session.query(
            OwnershipRequest.request_id.label("id"),
            OwnershipRequest.user_id,
            OwnershipRequest.endorsement_request_id,
            OwnershipRequest.workflow_status)

    @classmethod
    def base_query_with_audit(cls, session: Session) -> OrmQuery:
        return session.query(
            OwnershipRequest.request_id.label("id"),
            OwnershipRequest.user_id,
            OwnershipRequest.endorsement_request_id,
            OwnershipRequest.workflow_status,
            OwnershipRequestsAudit.date
            ).join(
                OwnershipRequestsAudit,
                OwnershipRequest.request_id == OwnershipRequestsAudit.request_id,
                isouter=True
            )


    @classmethod
    def to_model(cls, record: Row | OwnershipRequest, session: Session) -> OwnershipRequestModel:
        if isinstance(record, Row):
            data = record._asdict()
        elif isinstance(record, OwnershipRequest):
            data = record.__dict__.copy()
            data["id"] = data["request_id"]
            del data["request_id"]
            audit = session.query(OwnershipRequestsAudit.date).filter(OwnershipRequestsAudit.request_id == data["id"]).one_or_none()
            if audit:
                data["date"] = audit.date
        else:
            raise TypeError(f"Unsupported record type: {type(record)}")

        validated_data: OwnershipRequestModel = cls.model_validate(data)
        populate_document_ids(validated_data, session)
        return validated_data


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
    date: Optional[datetime.datetime] = None
    document_ids: Optional[List[int]] = None
    endorsement_request_id: Optional[int] = None
    make_owner: bool = False
    is_author: bool = False
    # Use arXiv IDs or document IDs but not both
    arxiv_ids: Optional[List[str]] = None  # paper ids, not document ids
    workflow_status: WorkflowStatus = WorkflowStatus.PENDING


# class PaperOwnershipDecisionModel(BaseModel):
#     workflow_status: WorkflowStatus # Literal['pending', 'accepted', 'rejected']
#     accepted_document_ids: List[int]   # is author
#     nonauthor_document_ids: List[int]  # is not author


class OwnershipRequestSubmit(BaseModel):
    user_id: int = Field(..., description="The ID of the user associated with the ownership request.")
    workflow_status: WorkflowStatus = Field(..., description="The status of the workflow ('pending', 'accepted', 'rejected').")
    document_ids: List[int] = Field(..., description="List of IDs of the documents in the ownership request.")
    authored_documents: Optional[List[int]] = Field(
        None, description="List of document IDs that the requester is the author."
    )
    paper_ids: Optional[List[str]] = Field(
        None, description="Optional list of paper IDs associated with the ownership request."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1129053,
                "workflow_status": "accepted",
                "document_ids": [2123367, 2123675, 2125897, 2130529, 2134610, 2612674, 2618378],
                "authored_documents": [2125897, 2123675, 2130529],
                "paper_ids": ["2208.04373", "2208.04681", "2208.06903", "2208.11535", "2209.00613"]
            }
        }


class OwnershipRequestNavi(BaseModel):
    first_request_id: Optional[int]
    prev_request_ids: List[int]
    next_request_ids: List[int]
    last_request_id: Optional[int]


def populate_document_ids(data: OwnershipRequestModel, session: Session):
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
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        preset: Optional[str] = Query(None),
        start_date: Optional[datetime.date] = Query(None, description="Start date for filtering"),
        end_date: Optional[datetime.date] = Query(None, description="End date for filtering"),
        id: Optional[List[int]] = Query(None, description="List of ownership request IDs to filter by"),
        current_id: Optional[int] = Query(None, description="Current ID - index position - for navigation"),
        user_id: Optional[int] = Query(None),
        endorsement_request_id: Optional[int] = Query(None),
        workflow_status: Optional[Literal['pending', 'accepted', 'rejected']] = Query(None),
        session: Session = Depends(get_db),
        current_user: ArxivUserClaims = Depends(get_authn_user),
    ) -> List[OwnershipRequestModel]:
    query = OwnershipRequestModel.base_query_with_audit(session)
    order_columns = []

    if id is not None:
        query = query.filter(OwnershipRequest.request_id.in_(id))
        _start = 0
        _end = len(id)
        if not current_user.is_admin:
            query = query.filter(OwnershipRequest.user_id == current_user.user_id)
    else:
        if preset is not None or start_date is not None or end_date is not None:
            t0 = datetime.datetime.now(datetime.UTC)
            if preset is not None:
                matched = re.search(r"last_(\d+)_day(s){0,1}", preset)
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
            prev_req_id = current_id
            next_req_id = current_id
            if prev_req:
                prev_req_id = prev_req.request_id
            if next_req:
                next_req_id = next_req.request_id
            query = query.filter(OwnershipRequest.request_id.between(prev_req_id, next_req_id))

        if _sort:
            keys = _sort.split(",")
            for key in keys:
                if key == "id":
                    key = "request_id"

                if key == "date":
                    try:
                        order_column = getattr(OwnershipRequestsAudit, key)
                        order_columns.append(order_column)
                    except AttributeError:
                        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                            detail="Invalid start or end index")
                else:
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
    if _start is None:
        _start = 0

    if _end is None:
        _end = 100
    result = [OwnershipRequestModel.to_model(item, session) for item in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get("/{id:int}")
async def get_ownership_request(
        id: int,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        session: Session = Depends(get_db),
    ) ->OwnershipRequestModel:
    query = OwnershipRequestModel.base_query_with_audit(session).filter(OwnershipRequest.request_id == id)
    if not current_user.is_admin:
        query = query.filter(OwnershipRequest.user_id == current_user.user_id)
    oreq = query.one_or_none()
    if oreq is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return OwnershipRequestModel.to_model(oreq, session)


@router.get("/navigate")
async def navigate(
        id: int,
        workflow: WorkflowStatus = Query(WorkflowStatus.PENDING, description="Workflow status" ),
        count: Optional[int] = Query(default=2, description="Number of prev/next IDs" ),
        session: Session = Depends(get_db),
    ) -> OwnershipRequestNavi:

    first_pending = session.query(OwnershipRequest) \
        .filter(OwnershipRequest.workflow_status == workflow.value) \
        .order_by(OwnershipRequest.request_id.asc()) \
        .first()

    last_pending = session.query(OwnershipRequest) \
        .filter(OwnershipRequest.workflow_status == workflow.value) \
        .order_by(OwnershipRequest.request_id.desc()) \
        .first()

    next_pending = session.query(OwnershipRequest) \
        .filter(and_(OwnershipRequest.request_id > id, OwnershipRequest.workflow_status == workflow.value)) \
        .order_by(OwnershipRequest.request_id.asc()) \
        .limit(count).all()

    prev_pending = session.query(OwnershipRequest) \
        .filter(and_(OwnershipRequest.request_id < id, OwnershipRequest.workflow_status == workflow.value)) \
        .order_by(OwnershipRequest.request_id.desc()) \
        .limit(count).all()

    return OwnershipRequestNavi(
        first_request_id=first_pending.request_id if first_pending else None,
        last_request_id=last_pending.request_id if last_pending else None,
        next_request_ids=[req0.request_id for req0 in next_pending],
        prev_request_ids=[req1.request_id for req1 in reversed(prev_pending)],
    )



@router.post('/')
async def create_ownership_request(
        request: Request,
        ownership_request: CreateOwnershipRequestModel,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        current_tapir_session: TapirSessionData | None = Depends(get_tapir_session),
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

    tsid = current_tapir_session.session_id if current_tapir_session else current_user.tapir_session_id

    audit = OwnershipRequestsAudit(
        request_id = req.request_id,
        session_id = int(tsid or 0),
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
    refreshed_req = OwnershipRequestModel.base_query_with_audit(session).filter(OwnershipRequest.request_id == req.request_id).one_or_none()
    if refreshed_req is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error")
    session.commit()
    return OwnershipRequestModel.to_model(refreshed_req, session)


@router.put("/{id:int}")
async def update_ownership_request(
        id: int,
        request: Request,
        payload: OwnershipRequestSubmit,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        remote_ip: str = Depends(get_client_host),
        remote_host: str = Depends(get_client_host_name),
        session: Session = Depends(get_db)) -> OwnershipRequestModel:
    """Update ownership request.

    This is about accepting/rejecting ownership requests.

$nickname=$auth->get_nickname_of($user_id);
$policy_class=$auth->conn->select_scalar("SELECT name FROM tapir_policy_classes WHERE class_id=$user->policy_class");


if ($_SERVER["REQUEST_METHOD"]=="POST") {
   if ($_POST["reject"]) {
      $auth->conn->query("UPDATE arXiv_ownership_requests SET workflow_status='rejected' WHERE request_id=$request->request_id");
      include "ownership-rejected-screen.php";
      exit();
   }

   if ($_POST["revisit"]) {
      $auth->conn->query("UPDATE arXiv_ownership_requests SET workflow_status='pending' WHERE request_id=$request->request_id");
      $request->workflow_status="pending";
   } else {

      $flag_author=$_POST["is_author"] ? 1:0;
      $n_papers=$_POST["n_papers"];
      $document_ids=array();
      $approved_count=0;
      for ($i=0;$i<$n_papers;$i++) {
         if ($_POST["approve_$i"]) {
            $approved_count++;
            array_push($document_ids,addslashes($_POST["document_id_$i"]));
         }
      }

      if($approved_count==0) {
         if($bulk_mode) {
            include "ownership-bulk-none-approved-screen.php";
            exit();
         }

         $auth->conn->query("UPDATE arXiv_ownership_requests SET workflow_status='accepted' WHERE request_id=$request->request_id");
         include "ownership-none-approved-screen.php";
         exit();
      }

      $auth->conn->begin();

      $id_list="(".join(",",$document_ids).")";
      $already_owns=$auth->conn->select_keys_and_values("SELECT document_id,1 FROM arXiv_paper_owners
                                                   WHERE user_id=$user->user_id
                                                   AND document_id IN $id_list FOR UPDATE");

      if(count($already_owns) == count($document_ids)) {
         include "ownership-all-owned-screen.php";
         exit();
      }

      $paper_ids=$auth->conn->select_keys_and_values("SELECT document_id,paper_id FROM arXiv_documents
                                                      WHERE document_id IN $id_list");

      $paper_list=array();
      $owned_list=array();

      for($i=0;$i<$n_papers;$i++) {
        if ($_POST["approve_$i"]) {
           $_document_id=addslashes($_POST["document_id_$i"]);
           $paper_id=$paper_ids[$_document_id];
           if($already_owns[$_document_id]) {
              array_push($owned_list,$paper_id);
           } else {
              $_remote_addr=addslashes($_SERVER["REMOTE_ADDR"]);
              $_remote_host=addslashes($_SERVER["REMOTE_HOST"]);
              $_tracking_cookie=addslashes($_COOKIE["M4_TRACKING_COOKIE_NAME"]);
              array_push($paper_list,$paper_id);
              $auth->conn->query("INSERT INTO arXiv_paper_owners (document_id,user_id,date,added_by,remote_addr,remote_host,tracking_cookie,valid,flag_author,flag_auto) VALUES ($_document_id,$user_id,$auth->timestamp,$auth->user_id,'$_remote_addr','$_remote_host','$_tracking_cookie',1,$flag_author,0)");
              tapir_audit_admin($user_id,"add-paper-owner-2",$_document_id);
           }
         }
      }

      if(!$bulk_mode) {
         $auth->conn->query("UPDATE arXiv_ownership_requests SET workflow_status='accepted' WHERE request_id=$request->request_id");
      }

      $auth->conn->commit();
      include "ownership-granted-screen.php";
      exit();
   }
}

{"id":62648,
  "user_id":1129053,
  "endorsement_request_id":null,
  "workflow_status":"accepted",
  "date":"2025-03-29T04:00:00Z",
  "document_ids":[2123367,2123675,2125897,2130529,2134610,2612674,2618378],
  "paper_ids":["2208.04373","2208.04681","2208.06903","2208.11535","2209.00613"]
  "selected_documents":[2125897,2123675,2130529]}
    """
    current_tapir_session_id = current_user.tapir_session_id

    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can update ownership requests.")

    req_id = id
    # body = await request.json()
    workflow_status = payload.workflow_status
    if workflow_status is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workflow status is required.")

    if workflow_status == WorkflowStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workflow status is pending. It needs to be rejected or accepted.")

    user_id = payload.user_id
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User id is required.")

    document_ids = payload.document_ids
    if document_ids is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document ids is required.")

    # Get the ownership request
    ownership_request: OwnershipRequest | None = session.query(OwnershipRequest).filter(OwnershipRequest.request_id == req_id).one_or_none()
    if ownership_request is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Ownership request id %s does not exist." % req_id)

    # The ownership request must be in pending statue
    if ownership_request.workflow_status != WorkflowStatus.PENDING.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Ownership request id %s has been decided as {ownership_request.workflow_status }." % req_id)

    # Make sure all of the docs in the request exist
    existing_document_ids: Set[int] = set([
        doc.document_id for doc in session.query(Document.document_id).filter(Document.document_id.in_(document_ids)).all()
    ])
    if len(existing_document_ids) != len(document_ids):
        nonexisting_ids = set(document_ids) - existing_document_ids
        bads = list(nonexisting_ids)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=f"Ownership request id %s - the some documents {bads!r} IDs doss not exist" % req_id)

    # Existing ownerships - Ignore them. This is a submit and only interested in making new ownerships.
    # If you want to change existing ownerships, use the ownership's update endpoint.

    existing_ownership_document_ids: Set[int] = set([
        po.document_id for po in session.query(PaperOwner.document_id).filter(and_(PaperOwner.document_id.in_(document_ids), PaperOwner.user_id == user_id)).all()
    ])

    requester = UserModel.one_user(session, str(user_id))
    if requester is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"User {user_id} not found.")
    date = datetime_to_epoch(None, datetime.datetime.now(datetime.UTC))
    ownership_request.workflow_status = cast(Literal['pending', 'accepted', 'rejected'], workflow_status.value)

    tracking_cookie = requester.tracking_cookie
    tracking_cookie_col = PaperOwner.__table__.columns["tracking_cookie"]
    tracking_cookie_max_len = getattr(tracking_cookie_col.type, "length", 32) or 32
    if tracking_cookie and len(tracking_cookie) > tracking_cookie_max_len:
        # ntai: 2025-03-30
        # When the tracking cookie is longer than the column size (32), adding tracking cookie
        # to the record fails as it is too long.
        # There are two options - one is to chop it, or hash it. I chose to hash it since the original
        # value cannot match anyway, and by hashing it, it has a chance to match it to the original
        # value.
        # The root cause is that the tapir_users' tracking_cookie has 255, and somehow, PaperOwner
        # does not follow the original design, which is a mistake.
        # I checked the database and 110+k tapir_users has the tracking cookie longer than 32 and thus,
        # I don't understand how this has been working.
        tracking_cookie = hashlib.md5(tracking_cookie.encode()).hexdigest()

    authored_documents = set(payload.authored_documents) if payload.authored_documents else set()

    try:
        for document_id in document_ids:
            if document_id in existing_ownership_document_ids:
                continue
            is_author = document_id in authored_documents
            paper_owner_r = PaperOwner(
                document_id = document_id,
                user_id = user_id,
                date = date,
                added_by = current_user.user_id,
                remote_addr = remote_ip,
                remote_host = remote_host,
                tracking_cookie = tracking_cookie,
                valid = True,
                flag_author = is_author,
                flag_auto = False
            )
            session.add(paper_owner_r)

            admin_audit(
                session,
                AdminAudit_AddPaperOwner2(
                    str(current_user.user_id),
                    str(user_id),
                    str(current_tapir_session_id),
                    str(document_id),
                    remote_ip=remote_ip,
                    remote_hostname=remote_host,
                    tracking_cookie=tracking_cookie,
                ))

        audit: OwnershipRequestsAudit | None = session.query(OwnershipRequestsAudit).filter(OwnershipRequestsAudit.request_id == req_id).one_or_none()
        if audit is None:
            audit = OwnershipRequestsAudit(
                request_id = req_id,
                session_id = int(current_tapir_session_id or 0),
                remote_addr = remote_ip,
                remote_host = remote_host,
                tracking_cookie = requester.tracking_cookie or "",
                date = date
            )
            session.add(audit)
        else:
            # ??? The judgement has been made but the status is still penning. Rather than burf, update the
            # audit to match with this judgement
            audit.session_id = int(current_tapir_session_id or 0)
            audit.remote_addr = remote_ip
            audit.remote_host = remote_host
            audit.tracking_cookie = requester.tracking_cookie or ""
            audit.date = date

        session.commit()
        return OwnershipRequestModel.to_model(OwnershipRequestModel.base_query_with_audit(session).filter(OwnershipRequest.request_id == req_id).one(), session)

    except IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The database operation failed due to integrity error. " + str(exc)) from exc

#
# @router.post('/{request_id:int}/documents/')
# async def post_ownership_request_decision(
#         request: Request,
#         request_id: int,
#         decision: PaperOwnershipDecisionModel,
#         current_user: ArxivUserClaims = Depends(get_authn_user),
#         remote_addr: str = Depends(get_client_host),
#         session: Session = Depends(get_db)) -> OwnershipRequestModel:
#     """Ownership creation
#
#     """
#     if not current_user.is_admin:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
#
#     ownership_request = OwnershipRequestModel.base_query_with_audit(session).filter(OwnershipRequest.request_id == request_id).one_or_none()
#
#     if ownership_request is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ownership request not found")
#
#     if decision.workflow_status not in [ws.value for ws in WorkflowStatus]:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"The decision's workflow_status {ownership_request.workflow_status} is invalid")
#
#     if ownership_request.workflow_status != WorkflowStatus.pending:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Existing ownership request workflow_status {ownership_request.workflow_status} is not pending")
#
#     if decision.workflow_status == WorkflowStatus.pending:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"The decision's workflow_status {decision.workflow_status} shound not be pending")
#
#     user_id = ownership_request.user_id
#     admin_id = current_user.user_id
#
#     current_request: OwnershipRequestModel = OwnershipRequestModel.to_model(None, ownership_request)
#     docs = set(current_request.document_ids)
#     decided_docs = set(decision.accepted_document_ids) | set(decision.nonauthor_document_ids)
#     if docs != decided_docs:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Not all papers decided")
#
#     ownership_request.workflow_status = decision.workflow_status
#
#     already_owns: [int] = [po.document_id for po in session.query(PaperOwner).filter(PaperOwner.user_id == user_id).all()]
#
#     decided_docs.remove(set(already_owns))
#
#     user: TapirUser = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
#
#     t_now = datetime.datetime.now(datetime.UTC)
#     for doc_id in decided_docs:
#         is_author = doc_id in decision.accepted_document_ids
#         po = PaperOwner(
#             document_id=doc_id,
#             user_id=user_id,
#             date=t_now,
#             added_by=admin_id,
#             remote_addr=remote_addr,
#             tracking_cookie=user.tracking_cookie,
#             valid=True,
#             flag_auto=False,
#             flag_author=is_author
#         )
#         session.add(po)
#
#     session.commit()
#     session.refresh(ownership_request)
#     return OwnershipRequestModel.to_model(ownership_request, session)
