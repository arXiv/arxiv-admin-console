"""arXiv endorsement routes."""
from datetime import timedelta, datetime, date, UTC
from typing import Optional, List, Tuple, Literal
import re

from arxiv.auth.user_claims import ArxivUserClaims
from arxiv_bizlogic.audit_event import AdminAudit_GotNegativeEndorsement, admin_audit, AdminAudit_SetEndorsementValid, \
    AdminAudit_SetPointValue
from arxiv_bizlogic.fastapi_helpers import get_authn, get_authn_user, get_tapir_tracking_cookie
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
        endorsee_name: Optional[str] = Query(None, description="Endorsee name. Last name, or first name + last name"),
        endorsee_email: Optional[str] = Query(None, description="Endorsee email"),
        category: Optional[str] = Query(None, description="Category"),
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

        if endorsee_name is not None or endorsee_email is not None:
            query = query.join(TapirUser, TapirUser.user_id == Endorsement.endorsee_id)

            if endorsee_name is not None:
                first_name = None
                last_name = None
                if "," in endorsee_name:
                    elems = endorsee_name.split(",")
                    if len(elems) == 2:
                        last_name = elems[0].strip()
                        first_name = elems[1].strip()
                else:
                    elems = endorsee_name.split(" ")
                    if len(elems) == 2:
                        first_name = elems[0].strip()
                        last_name = elems[1].strip()

                if first_name and last_name:
                    query = query.filter(TapirUser.first_name.like(first_name + "%"))
                    query = query.filter(TapirUser.last_name.like(last_name + "%"))
                else:
                    query = query.filter(TapirUser.last_name.like(endorsee_name + "%"))
                    pass
                pass

            if endorsee_email is not None:
                query = query.filter(TapirUser.email.like(endorsee_email + "%"))
                pass
            pass

        if category is not None:
            elems = category.split(".")
            if len(elems) > 1 and elems[1]:
                query = query.filter(Endorsement.archive.like(elems[0].strip() + "%"))
                query = query.filter(Endorsement.subject_class.like(elems[1].strip() + "%"))
            else:
                query = query.filter(Endorsement.archive.like(elems[0].strip() + "%"))
                pass
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


class EndorsementUpdateModel(BaseModel):
    positive_endorsement: Optional[bool] = None
    flag_valid: Optional[bool] = None
    admin_comment: Optional[str] = None


@router.put('/{id:int}')
async def update_endorsement(
        request: Request,
        id: int,
        body: EndorsementUpdateModel,
        current_user: Optional[ArxivUserClaims] = Depends(get_authn_user),
        remote_ip: Optional[str] = Depends(get_client_host),
        remote_hostname: Optional[str] = Depends(get_client_host_name),
        tracking_cookie: Optional[str] = Depends(get_tapir_tracking_cookie),
        session: Session = Depends(get_db)) -> EndorsementModel:
    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not authorized to update endorsements.")

    changed = False
    endorsement: Endorsement | None = session.query(Endorsement).filter(Endorsement.endorsement_id == id).one_or_none()
    if endorsement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement '{id}' not found")

    if body.positive_endorsement is not None:
        before = bool(endorsement.point_value > 0)
        after = bool(body.positive_endorsement)
        if before != after:
            if after:
                endorsement.point_value = 10
            else:
                endorsement.point_value = 0
            changed = True
            admin_audit(session,
                        AdminAudit_SetPointValue(
                            str(current_user.user_id),
                            str(endorsement.endorsee_id),
                            current_user.tapir_session_id,
                            endorsement.point_value,
                            remote_ip=remote_ip,
                            remote_hostname=remote_hostname,
                            tracking_cookie=tracking_cookie,
                            comment=body.admin_comment
                        ))

    if body.flag_valid is not None:
        if bool(endorsement.flag_valid) != body.flag_valid:
            endorsement.flag_valid = 1 if body.flag_valid else 0
            changed = True
            admin_audit(session,
                        AdminAudit_SetEndorsementValid(
                            str(current_user.user_id),
                            str(endorsement.endorsee_id),
                            current_user.tapir_session_id,
                            body.flag_valid,
                            remote_ip=remote_ip,
                            remote_hostname=remote_hostname,
                            tracking_cookie=tracking_cookie,
                            comment=body.admin_comment
                        ))

    if changed:
        if body.comment is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comment is required")

        session.commit()

    data = EndorsementModel.base_select(session).filter(Endorsement.endorsement_id == id).one_or_none()
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement '{id}' not found")
    if not changed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No changes to update")
    return EndorsementModel.model_validate(data)


@router.post(
    '/endorse',
    description="Create endorsement by a user",
    responses={
        200: {"model": EndorsementOutcomeModel, "description": "Successful endorsement"},
        405: {"model": EndorsementOutcomeModel, "description": "Endorsement not allowed"},
        400: {"description": "Bad request"},
        404: {"description": "Invalid endorsement code"},
        500: {"model": EndorsementOutcomeModel, "description": "Endorsement failed due to database operation error"},
    }
)
async def endorse(
        request: Request,
        response: Response,
        endorsement_code: EndorsementCodeModel,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        session: Session = Depends(get_db),
        tracking_cookie: str | None = Depends(get_tracking_cookie),
        client_host: str | None = Depends(get_client_host),
        client_host_name: str | None = Depends(get_client_host_name)
        ) -> EndorsementOutcomeModel:
    current_tapir_session = current_user.tapir_session_id
    audit_timestamp = datetime.now(UTC)
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

    # Admin can see the email (mod too?)
    show_email = current_user.is_admin

    accessor = EndorsementDBAccessor(session)

    business = EndorsementBusiness(
        accessor,
        endorser,
        endorsee,
        audit_timestamp,

        archive=endorsement_request.archive,
        subject_class=endorsement_request.subject_class,
        endorsement_code=endorsement_code,
        endorsement_request=endorsement_request,
        session_id=str(current_tapir_session),
        remote_host_ip=client_host,
        remote_host_name=client_host_name,
        tracking_cookie=tracking_cookie,
    )

    if not show_email and business.endorseE.email is not None:
        business.endorseE.email = ""

    try:
        acceptable = business.can_submit()
    except Exception as exc:
        logging.error(exc)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Endorsement criteria is met but failed on database operation") from exc

    if not business.public_reason:
        logging.info("reason %s is emptied as it is not public", business.outcome.reason)
        # Make sure the reason is empty if it is not public
        business.outcome.reason = ""

    if preflight:
        outcome = business.outcome
        return outcome

    if not acceptable:
        response.status_code = status.HTTP_405_METHOD_NOT_ALLOWED
        return business.outcome

    try:
        endorsement = business.submit_endorsement()
        if endorsement:
            business.outcome.endorsement = endorsement
            session.commit()
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



class EndorsementCreationModel(BaseModel):
    endorser_id: str
    endorsee_id: str
    archive: str
    subject_class: str
    type_: Literal["user", "admin", "auto"]
    point_value: int # This is rather be boolean?
    flag_valid: bool
    flag_seen_paper: bool
    flag_knows_personally: bool
    comment: Optional[str] = None


@router.post('/', description="Create a new endorsement (admin user only)")
async def create_endorsement(
        body: EndorsementCreationModel,
        current_user: ArxivUserClaims = Depends(get_authn_user),
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
                              session_id=current_user.tapir_session_id,
                              remote_host_ip=client_host,
                              remote_host_name=client_host_name,
                              tracking_cookie=tracking_cookie)
    outcome = biz.admin_approve(current_user)
    if outcome:
        return biz.submit_endorsement()
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=biz.reason)


@router.delete('/{id}', description="Delete an endorsement (admin user only)")
async def delete_endorsement(
        id: str,
        current_user: TapirSessionData = Depends(get_authn),
        session: Session = Depends(get_db)) -> Response:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not implemented yet")
    # if not current_user:
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    #
    # u_a_s = id.split('+')
    # if len(u_a_s) != 3:
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid endorsement id")
    #
    # endorsee_id = u_a_s[0]
    # archive = u_a_s[1]
    # subject_class = u_a_s[2]
    #
    # if endorsee_id != current_user.user_id and (not current_user.is_admin):
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
    #                         detail="You are not authorized to delete endorsements.")
    #
    # # Instead of deleting, update flag_valid and point_value to 0
    # result = session.query(Endorsement).filter(
    #     Endorsement.endorsee_id == endorsee_id,
    #     Endorsement.archive == archive,
    #     Endorsement.subject_class == subject_class
    # ).update(
    #     {"flag_valid": 0},
    #     synchronize_session=False
    # )
    #
    # if result == 0:
    #     raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Endorsement not found")
    #
    # session.commit()
    # return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get('/ids/')
async def list_endorsement_ids(
        response: Response,
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(1000, alias="_end"),
        _order: Optional[str] = Query("DESC", description="sort order"),
        preset: Optional[str] = Query(None),
        current_id: Optional[int] = Query(None),
        start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
        end_date: Optional[datetime] = Query(None, description="End date for filtering"),
        type: Optional[List[str] | str] = Query(None, description="user, auto, admin"),
        flag_valid: Optional[bool] = Query(True, description="Valid endorsements only"),
        endorsee_id: Optional[int] = Query(None),
        endorser_id: Optional[int] = Query(None),
        by_suspect: Optional[bool] = Query(None),
        positive_endorsement: Optional[bool] = Query(None),
        request_id: Optional[int] = Query(None),
        category: Optional[str] = Query(None, description="Category"),
        current_user: Optional[ArxivUserClaims] = Depends(get_authn),
        db: Session = Depends(get_db)
    ) -> List[int]:

    query = db.query(Endorsement)

    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")
    t0 = datetime.now()


    if not current_user.is_admin:
        query = query.filter(Endorsement.endorsee_id == current_user.user_id)

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
            pass
        pass
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

    if category is not None:
        elems = category.split(".")
        if len(elems) > 1 and elems[1]:
            query = query.filter(Endorsement.archive.like(elems[0].strip() + "%"))
            query = query.filter(Endorsement.subject_class.like(elems[1].strip() + "%"))
        else:
            query = query.filter(Endorsement.archive.like(elems[0].strip() + "%"))
            pass
        pass

    if _order is not None:
        order_columns = [Endorsement.endorsement_id]
        for column in order_columns:
            if _order == "DESC":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    endorsement: Endorsement
    result = [endorsement.endorsement_id for endorsement in query.offset(_start).limit(_end - _start).all()]
    return result
