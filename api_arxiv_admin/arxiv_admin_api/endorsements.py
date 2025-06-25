"""arXiv endorsement routes."""
from datetime import timedelta, datetime, date, UTC
from typing import Optional, List, Tuple, Literal
import re

from arxiv.auth.user_claims import ArxivUserClaims
from arxiv_bizlogic.fastapi_helpers import get_authn
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from pydantic import BaseModel
from sqlalchemy import and_

# from sqlalchemy import select, update, func, case, Select, distinct, exists, and_, alias
from sqlalchemy.orm import Session #, joinedload
from sqlalchemy.exc import IntegrityError

from arxiv.base import logging
from arxiv.db.models import Endorsement, EndorsementRequest, TapirUser, Demographic, EndorsementsAudit

from . import get_db, datetime_to_epoch, VERY_OLDE, get_current_user, get_client_host, \
    get_tracking_cookie, get_client_host_name, is_any_user, get_tapir_session
from .biz.endorsement_biz import EndorsementBusiness
from .biz.endorsement_io import EndorsementDBAccessor
from .endorsement_requests import EndorsementRequestModel
from .helpers.user_session import TapirSessionData
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
        flag_valid: Optional[bool] = Query(True, description="Valid endorsements only"),
        endorsee_id: Optional[int] = Query(None),
        endorser_id: Optional[int] = Query(None),
        by_suspect: Optional[bool] = Query(None),
        positive_endorsement: Optional[bool] = Query(None),
        id: Optional[List[int]] = Query(None, description="List of user IDs to filter by"),
        request_id: Optional[int] = Query(None),
        current_user: Optional[ArxivUserClaims] = Depends(get_authn),
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
            matched = re.search(r"last_(\d+)_day", preset)
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

        if positive_endorsement is not None:
            if positive_endorsement:
                query = query.filter(Endorsement.point_value > 0)
            else:
                query = query.filter(Endorsement.point_value <= 0)

        if by_suspect is not None:
            query = query.join(Demographic, Endorsement.endorser_id == Demographic.user_id)
            query = query.filter(Demographic.flag_suspect == by_suspect)
            pass

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
                          current_user: Optional[ArxivUserClaims] = Depends(get_authn),
                          db: Session = Depends(get_db)) -> EndorsementModel:
    item = EndorsementModel.base_select(db).filter(Endorsement.endorsement_id == id).all()
    if item:
        return EndorsementModel.model_validate(item[0])
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement '{id}' not found")


@router.put('/{id:int}')
async def update_endorsement(
        request: Request,
        id: int,
        current_user: Optional[ArxivUserClaims] = Depends(get_authn),
        session: Session = Depends(get_db)) -> EndorsementModel:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to update endorsements.")
    body = await request.json()

    changed = False
    endorsement: Endorsement | None = session.query(Endorsement).filter(Endorsement.endorsement_id == id).one_or_none()
    if endorsement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement '{id}' not found")

    if "positive_endorsement" in body:
        before = endorsement.point_value > 0
        after = body["positive_endorsement"]
        if before != after:
            if body["positive_endorsement"]:
                endorsement.point_value = 10
            else:
                endorsement.point_value = 0
            changed = True

    if "flag_valid" in body:
        flag_valid = 1 if body["flag_valid"] else 0
        if endorsement.flag_valid != flag_valid:
            endorsement.flag_valid = flag_valid
            changed = True

    if changed:
        session.commit()

    data = EndorsementModel.base_select(session).filter(Endorsement.endorsement_id == id).one_or_none()
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement '{id}' not found")
    if not changed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No changes to update")
    return EndorsementModel.model_validate(data)


# class EndorsementUpdateModel(BaseModel):
#     positive: bool
#     category: str
#     flag_seen_paper: bool
#     flag_knows_personally: bool
#     comment: Optional[str]
#
# class EndorsementsUpdateModel(BaseModel):
#     endorser_id: str
#     endorsee_id: str
#     endorsements: List[EndorsementUpdateModel]
#
#
# @router.put('/upsert')
# async def upsert_endorsement(
#         request: Request,
#         body: EndorsementsUpdateModel,
#         current_user: Optional[ArxivUserClaims] = Depends(get_authn),
#         session: Session = Depends(get_db),
#         remote_addr: str = Depends(get_client_host),
#         remote_host: str = Depends(get_client_host_name),
#         tracking_cookie: str = Depends(get_tracking_cookie),
#
#         ) -> List[EndorsementModel]:
#     if current_user is None:
#         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
#     if not current_user.is_admin:
#         raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
#                             detail="You are not authorized to update endorsements.")
#
#     endorsements: List[Tuple[Endorsement, EndorsementUpdateModel]] = []
#     issued_when = datetime_to_epoch(None, datetime.now(UTC))
#
#     for item in body.endorsements:
#         [archive, subject_class] = item.category.split(".")
#         point_value = 10 if item.positive else 0
#         flag_valid = item.positive
#
#         endorsement: Endorsement | None = session.query(Endorsement).filter(and_(
#             Endorsement.endorsee_id == body.endorsee_id,
#             Endorsement.archive == archive,
#             Endorsement.subject_class == subject_class
#         )).one_or_none()
#
#         if endorsement is not None:
#             if endorsement.point_value == 0:
#                 endorsement.flag_valid = flag_valid
#                 endorsement.point_value = point_value
#                 endorsements.append((endorsement, item))
#                 pass
#             else:
#                 if item.positive:
#                     if point_value > endorsement.point_value:
#                         endorsement.point_value = point_value
#                         endorsement.flag_valid = flag_valid
#                         endorsements.append((endorsement, item))
#                         pass
#                     pass
#                 else:
#                     if point_value != endorsement.point_value:
#                         endorsement.point_value = point_value
#                         endorsement.flag_valid = flag_valid
#                         endorsements.append((endorsement, item))
#                         pass
#                     pass
#                 pass
#             pass
#         else:
#             endorsement = Endorsement(
#                 endorser_id = body.endorser_id,
#                 endorsee_id = body.endorsee_id,
#                 archive = archive,
#                 subject_class = subject_class,
#                 flag_valid = flag_valid,
#                 type_ = "admin",
#                 point_value = point_value,
#                 issued_when = issued_when
#             )
#             session.add(endorsement)
#             session.flush()
#             endorsements.append((endorsement, item))
#             pass
#         pass
#
#     if len(endorsements) == 0:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No changes to update")
#
#     positives = []
#     for endorsement, item in endorsements:
#         if endorsement.flag_valid:
#             positives.append(endorsement)
#         audit = EndorsementsAudit(
#             endorsement_id = endorsement.endorsement_id,
#             session_id = current_user.session_id,
#             remote_addr = remote_addr,
#             remote_host = remote_host,
#             tracking_cookie = tracking_cookie,
#             flag_knows_personally = item.flag_knows_personally,
#             flag_seen_paper = item.flag_seen_paper,
#             comment = item.comment
#         )
#         session.add(audit)
#     session.commit()
#
#     #  notify ensorsee - how can I do that?
#
#     return [EndorsementModel.model_validate(EndorsementModel.base_select(session).filter(Endorsement.endorsement_id == endorsement.endorsement_id).first()) for endorsement, _ in endorsements]


async def _endorse(
        session: Session,
        request: Request,
        response: Response,
        endorsement_code: EndorsementCodeModel,
        current_user: ArxivUserClaims,
        current_tapir_session: TapirSessionData,
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
    endorser = UserModel.to_model(proto_endorser)

    proto_endorsement_req = EndorsementRequestModel.base_select(session).filter(EndorsementRequest.secret == endorsement_code.endorsement_code).one_or_none()
    if not proto_endorsement_req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid endorsement code")
    endorsement_request = EndorsementRequestModel.model_validate(proto_endorsement_req)

    proto_endorsee = PublicUserModel.base_select(session).filter(TapirUser.user_id == endorsement_request.endorsee_id).one_or_none()
    if proto_endorsee is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Endorses not found")
    endorsee = PublicUserModel.model_validate(proto_endorsee)

    accessor = EndorsementDBAccessor(session)

    tapir_session_id = current_tapir_session.session_id if current_tapir_session else None

    business = EndorsementBusiness(
        accessor,
        endorser,
        endorsee,
        audit_timestamp,

        archive=endorsement_code.archive,
        subject_class=endorsement_code.subject_class,
        endorsement_code=endorsement_code,
        endorsement_request=endorsement_request,
        session_id=tapir_session_id,
        remote_host_ip=client_host,
        remote_host_name=client_host_name,
        tracking_cookie=tracking_cookie,
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
        current_user: ArxivUserClaims = Depends(get_authn),
        session: Session = Depends(get_db),
        current_tapir_session: TapirSessionData = Depends(get_tapir_session),
        tracking_cookie: str | None = Depends(get_tracking_cookie),
        client_host: str | None = Depends(get_client_host),
        client_host_name: str | None = Depends(get_client_host_name)
        ) -> EndorsementOutcomeModel:
    audit_timestamp = datetime.now(UTC)
    return await _endorse(session, request, response, endorsement_code, current_user, current_tapir_session, tracking_cookie, client_host, client_host_name, audit_timestamp, show_email=current_user.is_admin)


class EndorsementCreationModel(BaseModel):
    endorser_id: str
    endorsee_id: str
    archive: str
    subject_class: str
    type_: Literal["user", "admin", "auto"]
    point_value: int
    flag_valid: bool
    flag_seen_paper: bool
    flag_knows_personally: bool
    comment: Optional[str] = None

@router.post('/', description="Create a new endorsement (admin user only)")
async def create_endorsement(
        body: EndorsementCreationModel,
        current_user: ArxivUserClaims = Depends(get_authn),
        current_tapir_session: TapirSessionData = Depends(get_tapir_session),
        tracking_cookie: str | None = Depends(get_tracking_cookie),
        client_host: str | None = Depends(get_client_host),
        client_host_name: str | None = Depends(get_client_host_name),
        session: Session = Depends(get_db)) -> Optional[EndorsementModel]:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to create endorsements.")

    if not body.endorser_id:
        body.endorser_id = str(current_user.user_id)

    if current_user.user_id != body.endorser_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Endorser is not the admin.")

    user = UserModel.one_user(session, current_user.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Endorser is not the admin.")
    endorsee = PublicUserModel.one_user(session, body.endorsee_id)
    if endorsee is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Endorses does not exist.")

    audit_timestamp = datetime.now(UTC)
    endorsement_request = None
    accessor = EndorsementDBAccessor(session)
    endorse = EndorsementCodeModel(
        preflight=True,
        positive=True,
        endorser_id=body.endorser_id,
        endorsement_code="",
        comment="" if not body.comment else body.comment,
        knows_personally=True,
        seen_paper=False
    )
    biz = EndorsementBusiness(accessor,
                              user,
                              endorsee,
                              audit_timestamp,
                              archive=body.archive,
                              subject_class=body.subject_class,
                              endorsement_code=endorse,
                              endorsement_request=endorsement_request,
                              session_id=current_tapir_session.session_id if current_tapir_session else None,
                              remote_host_ip=client_host,
                              remote_host_name=client_host_name,
                              tracking_cookie=tracking_cookie)
    outcome = biz.admin_approve()
    if outcome:
        return biz.submit_endorsement()
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=biz.reason)


@router.delete('/{id}/', description="Delete an endorsement (admin user only)")
async def delete_endorsement(
        id: str,
        current_user: TapirSessionData = Depends(get_authn),
        session: Session = Depends(get_db)) -> Response:
    if not current_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    u_a_s = id.split('+')
    if len(u_a_s) != 3:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid endorsement id")

    endorsee_id = u_a_s[0]
    archive = u_a_s[1]
    subject_class = u_a_s[2]

    if endorsee_id != current_user.user_id and (not current_user.is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="You are not authorized to delete endorsements.")

    # Instead of deleting, update flag_valid and point_value to 0
    result = session.query(Endorsement).filter(
        Endorsement.endorsee_id == endorsee_id,
        Endorsement.archive == archive,
        Endorsement.subject_class == subject_class
    ).update(
        {"flag_valid": 0},
        synchronize_session=False
    )

    if result == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endorsement not found")

    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
