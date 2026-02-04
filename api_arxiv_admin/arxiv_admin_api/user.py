"""arXiv user routes."""
from __future__ import annotations
import re
from typing import Optional, List, Type
from datetime import date, timedelta, datetime, timezone

from arxiv.auth.user_claims import ArxivUserClaims
from arxiv_bizlogic.audit_event import AdminAudit_ChangeStatus, AdminAudit_AddComment, admin_audit
from arxiv_bizlogic.user_status import UserVetoStatus

from arxiv_bizlogic.fastapi_helpers import get_current_user, get_authn, get_client_host, get_client_host_name, \
    get_tapir_tracking_cookie, get_authn_user
from fastapi import APIRouter, Query, status, Depends, Request
from fastapi.responses import Response
from fastapi.exceptions import HTTPException
from pydantic import BaseModel, ConfigDict, field_validator

from sqlalchemy import select, distinct, and_, inspect, cast, LargeBinary, Row, or_, func, literal
from sqlalchemy.orm import Session, aliased

from arxiv.db.models import (TapirUser, TapirNickname, t_arXiv_moderators, Demographic,
                             t_arXiv_black_email, Category, OrcidIds, TapirSession, AdminLog, TapirAdminAudit)
from arxiv_bizlogic.bizmodels.user_model import UserModel, VetoStatusEnum, _tapir_user_utf8_fields_, \
    _demographic_user_utf8_fields_, list_mod_cats_n_arcs, ACCOUNT_MANAGEMENT_FIELDS
from arxiv_bizlogic.sqlalchemy_helper import update_model_fields

from . import is_admin_user, get_db, VERY_OLDE, datetime_to_epoch, check_authnz
from .audit import record_user_prop_admin_action
from .biz import canonicalize_category
from .biz.document_biz import document_summary
from .biz.endorsement_biz import can_user_submit_to, can_user_endorse_for, EndorsementAccessor
from .dao.react_admin import ReactAdminUpdateResult, ReactAdminCreateResult
from logging import getLogger

from .endorsing import endorsing_db
from .endorsing.endorsing_models import EndorsementCandidate

logger = getLogger(__name__)

router = APIRouter(prefix="/users")
users_by_username_router = APIRouter(prefix="/users-by-username")


# Things normal user can update
DEMOGRAPHIC_FIELDS = {
    "country", "archive", "subject_class",
    "type", # Career status
    "flag_group_physics",
    "flag_group_math",
    "flag_group_cs",
    "flag_group_nlin",
    "flag_group_q_bio",
    "flag_group_q_fin",
    "flag_group_stat",
    "flag_group_eess",
    "flag_group_econ"
}

ADMIN_DEMOGRAPHIC_FIELDS = {
    "original_subject_classes",
    "flag_journal",
    "dirty",
}

ADMIN_AUDIT_DEMOGRAPHIC_FIELDS = {
    "flag_suspect",
    "veto_status",
    "flag_proxy",
    "flag_xml",
    "flag_group_test",
}

TAPIR_USER_FIELDS = {
    "first_name",
    "last_name",
    "suffix_name",
    "share_first_name",
    "share_last_name",
    # "email",
    # "flag_email_verified",
    "share_email",
    "flag_wants_email",
    "flag_html_email",
}

ADMIN_TAPIR_USER_FIELDS = {
    "policy_class",
    "joined_date",
    "joined_ip_num",
    "joined_remote_host",
    "flag_approved",
    "tracking_cookie",
    "flag_allow_tex_produced",
    "flag_internal",
}

ADMIN_AUDIT_TAPIR_USER_FIELDS = {
    "email_bouncing",
    "flag_edit_users",
    "flag_edit_system",
    "flag_deleted",
    "flag_banned",
    "flag_can_lock"
}


def is_ascii_only(value: str) -> bool:
    """
    Check if a string contains only ASCII characters.

    :param value: The string to check
    :return: True if the string contains only ASCII characters
    """
    try:
        value.encode('ascii')
        return True
    except UnicodeEncodeError:
        return False


def encode_for_latin1_column(value: str) -> bytes:
    """
    Encode a UTF-8 string as bytes for querying Latin1 database columns.

    This converts the UTF-8 string to bytes that can be compared with Latin1 columns
    containing UTF-8 data. The database stores UTF-8 data as raw bytes in Latin1 columns.

    :param value: The UTF-8 string to convert
    :return: UTF-8 encoded bytes
    """
    return value.encode('utf-8')




class UserUpdateModel(UserModel):
    pass

class UserPropertyUpdateRequest(BaseModel):
    property_name: str
    property_value: str | int | bool
    comment: Optional[str] = None


class UserVetoStatusRequest(BaseModel):
    status_before: UserVetoStatus
    status_after: UserVetoStatus
    comment: Optional[str] = None


class UserCommentRequest(BaseModel):
    comment: str


@router.get("/{user_id:int}")
def get_one_user(user_id:int,
                 current_user: ArxivUserClaims = Depends(get_authn_user),
                 db: Session = Depends(get_db)) -> UserModel:
    check_authnz(None, current_user, str(user_id))
    # @ignore-types
    user = UserModel.one_user(db, str(user_id))
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.get("/username/")
def list_user_by_username(response: Response,
                          _sort: Optional[str] = Query("last_name,first_name", description="sort by"),
                          _order: Optional[str] = Query("ASC", description="sort order"),
                          _start: int = Query(0, alias="_start"),
                          _end: int = Query(100, alias="_end"),
                          id: Optional[List[str]] = Query(None, description="List of user IDs to filter by"),
                          db: Session = Depends(get_db),
                          _is_admin: bool = Depends(is_admin_user),
                          ) -> List[UserModel]:
    """
    List users by username
    """
    if _start is None:
        _start = 0
    if _end is None:
        _end = _start + 100
    query = UserModel.base_select(db)
    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    order_columns = []
    if _sort:
        keys = _sort.split(",")
        for key in keys:
            if key == "id":
                key = "user_id"
            try:
                order_column = getattr(TapirUser, key)
                order_columns.append(order_column)
            except AttributeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid start or end index")


    if id is not None:
        user_ids = select(TapirNickname.user_id).where(TapirNickname.nickname.in_(id))
        query = query.filter(TapirUser.user_id.in_(user_ids))
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [UserModel.to_model(user) for user in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get("/username/{username:str}")
def get_user_by_username(username: str,
                         db: Session = Depends(get_db),
                         _is_admin: bool = Depends(is_admin_user),
                         ) -> UserModel:
    """
    List users by username
    """
    query = UserModel.base_select(db)
    query = query.join(TapirNickname, TapirUser.user_id == TapirNickname.user_id)
    query = query.filter(TapirNickname.nickname == username)
    user = query.one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,)
    return UserModel.to_model(user)


@router.get("/")
async def list_users(
        request: Request,
        response: Response,
        _sort: Optional[str] = Query("last_name,first_name", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        user_class: Optional[str] = Query(None, description="None for all, 'admin|owner'"),
        flag_is_mod: Optional[bool] = Query(None, description="moderator"),
        is_non_academic: Optional[bool] = Query(None, description="non-academic"),
        username: Optional[str] = Query(None),
        email: Optional[str] = Query(None),
        name: Optional[str] = Query(None),
        last_name: Optional[str] = Query(None),
        first_name: Optional[str] = Query(None),
        flag_edit_users: Optional[bool] = Query(None),
        flag_email_verified: Optional[bool] = Query(None),
        flag_proxy: Optional[bool] = Query(None),
        flag_veto: Optional[bool] = Query(None),
        email_bouncing: Optional[bool] = Query(None),
        clue: Optional[str] = Query(None),
        suspect: Optional[bool] = Query(None),
        endorsing_categories: Optional[List[str]] = Query(None),
        start_joined_date: Optional[date] = Query(None, description="Start date for filtering"),
        end_joined_date: Optional[date] = Query(None, description="End date for filtering"),
        id: Optional[List[int]] = Query(None, description="List of user IDs to filter by"),
        q: Optional[str] = Query(None, description="Query string"),
        db: Session = Depends(get_db),
        current_user: ArxivUserClaims = Depends(get_authn_user),
) -> List[UserModel]:
    """
    List users
    """
    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    order_columns = []
    sort_nickname_alias = None
    if _sort:
        keys = _sort.split(",")
        for key in keys:
            if key == "id":
                key = "user_id"
            if key == "username":
                if sort_nickname_alias is None:
                    sort_nickname_alias = aliased(TapirNickname)
                order_columns.append(sort_nickname_alias.nickname)
            else:
                try:
                    order_column = getattr(TapirUser, key)
                    order_columns.append(order_column)
                except AttributeError:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Invalid sort field")

    # Horay, base query no longer uses subqueries.
    query = UserModel.base_select(db)
    
    if not current_user.is_admin:
        query = query.filter(TapirUser.user_id == current_user.user_id)

    # Join with TapirNickname if needed for sorting by username
    if sort_nickname_alias is not None:
        query = query.join(sort_nickname_alias, TapirUser.user_id == sort_nickname_alias.user_id)

    all_users = True
    if id is not None:
        all_users = False
        if current_user.is_admin:
            query = query.filter(TapirUser.user_id.in_(id))
    else:
        if q:
            all_users = False
            if "@" in q:
                query = query.filter(TapirUser.email == q)
            elif q[0] in "0123456789":
                query = query.filter(TapirUser.user_id == q)
            else:
                query = query.filter(TapirUser.last_name == q)

        if suspect:
            all_users = False
            dgfx = aliased(Demographic)
            query = query.join(dgfx, dgfx.user_id == TapirUser.user_id)
            query = query.filter(dgfx.flag_suspect == suspect)

        if user_class in ["owner", "admin"]:
            all_users = False
            query = query.filter(TapirUser.policy_class == False)

        if user_class in ["owner"]:
            all_users = False
            query = query.filter(TapirUser.flag_edit_system == True)

        if flag_edit_users is not None:
            all_users = False
            query = query.filter(TapirUser.flag_edit_users == flag_edit_users)

        if flag_is_mod is not None:
            all_users = False
            # We're not using the moderator-driven query, so need to filter
            subquery = select(distinct(t_arXiv_moderators.c.user_id))

            if flag_is_mod is True:
                # Anti-join: users NOT in moderators table
                query = query.filter(TapirUser.user_id.in_(subquery))
            else:
                query = query.filter(TapirUser.user_id.not_in(subquery))

        if username:
            all_users = False
            nick1 = aliased(TapirNickname)
            query = query.join(nick1, nick1.user_id == TapirUser.user_id)
            query = query.filter(nick1.nickname.like(username + "%"))

        if name and first_name is None and last_name is None:
            all_users = False
            if "," in name:
                names = name.split(",")
                if len(names) > 1:
                    last_name = names[0].strip()
                    first_name = names[1].strip()
                else:
                    last_name = names[0].strip()
            elif " " in name:
                names = [elem.strip() for elem in name.split(' ') if elem.strip()]
                if len(names) > 1:
                    last_name = names[0]
                    first_name = names[1]
                else:
                    last_name = names[0]
                pass
            elif re.match(r"^[0-9]+$", name):
                query = query.filter(TapirUser.user_id == name)
            else:
                last_name = name.strip()
                pass
            pass


        if first_name:
            all_users = False
            if is_ascii_only(first_name):
                # Fast indexed search for ASCII/Latin-only names
                query = query.filter(TapirUser.first_name.startswith(first_name))
            else:
                # Binary comparison for non-Latin characters (no case folding needed)
                query = query.filter(cast(TapirUser.first_name, LargeBinary).like(
                    encode_for_latin1_column(first_name + '%')))

        if last_name:
            all_users = False
            if is_ascii_only(last_name):
                # Fast indexed search for ASCII/Latin-only names
                query = query.filter(TapirUser.last_name.startswith(last_name))
            else:
                # Binary comparison for non-Latin characters (no case folding needed)
                query = query.filter(cast(TapirUser.last_name, LargeBinary).like(
                    encode_for_latin1_column(last_name + '%')))

        if email:
            all_users = False
            query = query.filter(TapirUser.email.startswith(email))

        if flag_email_verified is not None:
            all_users = False
            query = query.filter(TapirUser.flag_email_verified == flag_email_verified)

        if flag_veto is not None:
            all_users = False
            dgfx2 = aliased(Demographic)
            query = query.join(dgfx2, dgfx2.user_id == TapirUser.user_id)
            query = query.filter(dgfx2.flag_suspect == suspect)
            if flag_veto:
                query = query.filter(dgfx2.veto_status != "ok")
            else:
                query = query.filter(dgfx2.veto_status == "ok")

        if flag_proxy is not None:
            all_users = False
            dgfx3 = aliased(Demographic)
            query = query.join(dgfx3, dgfx3.user_id == TapirUser.user_id)
            query = query.filter(dgfx3.flag_proxy == flag_proxy)

        if email_bouncing is not None:
            all_users = False
            query = query.filter(TapirUser.email_bouncing == email_bouncing)

        # This is how Tapir limits the search
        if is_non_academic and start_joined_date is None:
            all_users = False
            start_joined_date = date.today() - timedelta(days=90)

        if start_joined_date or end_joined_date:
            t_begin = datetime_to_epoch(start_joined_date, VERY_OLDE)
            t_end = datetime_to_epoch(end_joined_date, date.today(), hour=23, minute=59, second=59)
            query = query.filter(TapirUser.joined_date.between(t_begin, t_end))

        if is_non_academic:
            # Inner join with arxiv_black_email on pattern match with email
            all_users = False
            query = query.join(t_arXiv_black_email, TapirUser.email.like(t_arXiv_black_email.c.pattern))

        if clue is not None:
            all_users = False
            if len(clue) > 0 and clue[0] in "0123456789":
                query = query.filter(TapirUser.user_id.like(clue + "%"))
            elif "@" in clue:
                query = query.filter(TapirUser.email.like(clue + "%"))
            elif len(clue) >= 2:
                names = clue.split(",")
                if len(names) > 0:
                    query = query.filter(TapirUser.last_name.like(names[0] + "%"))
                if len(names) > 1:
                    query = query.filter(TapirUser.first_name.like(names[1] + "%"))
                if len(names) > 2:
                    query = query.filter(TapirUser.suffix_name.like(names[2] + "%"))

        if endorsing_categories is not None:
            all_users = False
            engine = endorsing_db.endorsing_db_get_cached_db(request)
            candidates = endorsing_db.endorsing_db_query_users_in_categories(engine, endorsing_categories)
            user_ids = [candidate.id for candidate in candidates] if candidates else []
            query = query.filter(TapirUser.user_id.in_(user_ids))

    for column in order_columns:
        if _order == "DESC":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    if all_users:
        count = db.query(TapirUser.user_id).count()
    else:
        count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [UserModel.to_model(user, session=db) for user in query.offset(_start).limit(_end - _start).all()]
    return result


def sanitize_user_update_data(update_data: dict) -> dict:
    for key in ["id", "user_id", "username", "moderated_categories", "moderated_archives", "tapir_policy_classes", "orcid_id", "flag_is_mod"]:
        if key in update_data:
            del update_data[key]
    return update_data


async def _update_user_property(
        session: Session,
        user: TapirUser,
        demographic: Demographic,
        user_id: int,
        body: UserPropertyUpdateRequest,
        current_user: ArxivUserClaims,
        remote_ip: Optional[str] = None,
        remote_hostname: Optional[str] = None,
        tracking_cookie: Optional[str] = None) -> None:
    """Update user property """

    tapir_fields = TAPIR_USER_FIELDS | ADMIN_TAPIR_USER_FIELDS | ADMIN_AUDIT_TAPIR_USER_FIELDS
    demographic_fields = DEMOGRAPHIC_FIELDS | ADMIN_DEMOGRAPHIC_FIELDS |ADMIN_AUDIT_DEMOGRAPHIC_FIELDS

    def on_update(session, model, field_name, current_value, value):
        if field_name in ADMIN_AUDIT_TAPIR_USER_FIELDS or body.property_name in ADMIN_AUDIT_DEMOGRAPHIC_FIELDS:
            record_user_prop_admin_action(
                session,
                admin_id=str(current_user.user_id),
                session_id=str(current_user.tapir_session_id),
                prop_name=field_name,
                user_id=str(user_id),
                old_value=current_value,
                new_value=value,
                comment=body.comment,
                remote_ip=remote_ip,
                remote_hostname=remote_hostname,
                tracking_cookie=tracking_cookie)

    data = {
        body.property_name: body.property_value,
        "comment": body.comment
    }

    try:
        update_model_fields(session, user, data, updating_fields=tapir_fields, primary_key_value=user_id, on_update=on_update)
    except Exception as e:
        logger.error(f"_update_user_property: update_model_fields", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e

    try:
        update_model_fields(session, demographic, data, updating_fields=demographic_fields, primary_key_value=user_id, on_update=on_update)
    except Exception as e:
        logger.error(f"_update_user_property: update_model_fields", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from e



@router.put('/{user_id:int}/demographic')
async def update_user_demographic(
        user_id: int,
        body: UserPropertyUpdateRequest,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        remote_ip: Optional[str] = Depends(get_client_host),
        remote_hostname: Optional[str] = Depends(get_client_host_name),
        tracking_cookie: Optional[str] = Depends(get_tapir_tracking_cookie),
        session: Session = Depends(get_db)) -> UserModel:
    """Update user property - by PUT"""
    if not current_user.is_admin and user_id != current_user.user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can update user properties")

    user = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    demographic = session.query(Demographic).filter(Demographic.user_id == user_id).one_or_none()
    if demographic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demographic not found")

    await _update_user_property(
        session,
        user,
        demographic,
        user_id,
        body,
        current_user,
        remote_ip,
        remote_hostname,
        tracking_cookie)
    session.commit()
    result = UserModel.one_user(session, str(user_id))
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found after update")
    return result


@router.put('/{user_id:int}')
async def update_user(
        user_id: int,
        body: UserModel,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        remote_ip: Optional[str] = Depends(get_client_host),
        remote_hostname: Optional[str] = Depends(get_client_host_name),
        tracking_cookie: Optional[str] = Depends(get_tapir_tracking_cookie),
        session: Session = Depends(get_db)) -> UserModel:
    """Update user property - by PUT"""

    demographic: Demographic | None = session.query(Demographic).filter(Demographic.user_id == user_id).one_or_none()
    tapir_user: TapirUser | None = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()

    if not demographic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Demographic not found")
    if not tapir_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    data = body.model_dump()

    if current_user.is_admin:
        tapir_user_fields = TAPIR_USER_FIELDS | ADMIN_TAPIR_USER_FIELDS | ADMIN_AUDIT_TAPIR_USER_FIELDS
        demographic_fields = DEMOGRAPHIC_FIELDS | ADMIN_DEMOGRAPHIC_FIELDS | ADMIN_AUDIT_DEMOGRAPHIC_FIELDS
    else:
        demographic_fields = DEMOGRAPHIC_FIELDS
        tapir_user_fields = TAPIR_USER_FIELDS
        pass

    for target, fields in [(demographic, demographic_fields), (tapir_user, tapir_user_fields)]:
        for field in fields:
            # Demographic update does not handle these. This needs to be handled by account management API
            if field in ACCOUNT_MANAGEMENT_FIELDS:
                continue
            old_value = getattr(target, field)
            new_value = data.get(field)
            if new_value is None:
                continue
            if isinstance(new_value, bool) and isinstance(old_value, int):
                # column is boolean but shows up as int
                new_value = 1 if new_value else 0
            if isinstance(new_value, datetime) and isinstance(old_value, int):
                # column is boolean but shows up as int
                new_value = datetime_to_epoch(None, new_value)
            if old_value != new_value:
                if current_user.is_admin:
                    await _update_user_property(
                        session,
                        tapir_user,
                        demographic,
                        user_id,
                        UserPropertyUpdateRequest(
                            property_name=field,
                            property_value=new_value,
                            comment=None
                        ),
                        current_user,
                        remote_ip,
                        remote_hostname,
                        tracking_cookie)
                else:
                    setattr(target, field, new_value)
    session.commit()
    result = UserModel.one_user(session, str(user_id))
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found after update")
    return result

@router.post('/{user_id:int}/comment', status_code=status.HTTP_201_CREATED)
async def create_user_comment(
        user_id: int,
        body: UserCommentRequest,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        remote_ip: Optional[str] = Depends(get_client_host),
        remote_hostname: Optional[str] = Depends(get_client_host_name),
        tracking_cookie: Optional[str] = Depends(get_tapir_tracking_cookie),
        session: Session = Depends(get_db)) -> ReactAdminCreateResult:
    """Add comment to a user by POST"""

    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can update user properties")

    user = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    audit_record = admin_audit(
        session,
        AdminAudit_AddComment(
            str(current_user.user_id),
            str(user_id),
            str(current_user.tapir_session_id),
            remote_ip=remote_ip,
            remote_hostname=remote_hostname,
            tracking_cookie=tracking_cookie,
            comment=body.comment,
    ))
    session.commit()
    return ReactAdminCreateResult(id=audit_record.entry_id)


@router.put('/{user_id:int}/veto-status')
async def update_user_veto_status(
        request: Request,
        user_id: int,
        body: UserVetoStatusRequest,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        remote_ip: Optional[str] = Depends(get_client_host),
        remote_hostname: Optional[str] = Depends(get_client_host_name),
        tracking_cookie: Optional[str] = Depends(get_tapir_tracking_cookie),
        session: Session = Depends(get_db)) -> UserModel:
    """Update user veto status - by PUT"""

    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can update user properties")

    demographic: Demographic | None = session.query(Demographic).filter(Demographic.user_id == user_id).one_or_none()
    if demographic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if demographic.veto_status != body.status_after.value:
        demographic.veto_status = body.status_after.value
        admin_audit(
            session,
            AdminAudit_ChangeStatus(
                current_user.user_id,
                user_id,
                current_user.tapir_session_id,
                remote_ip=remote_ip,
                remote_hostname=remote_hostname,
                tracking_cookie=tracking_cookie,
                status_before=UserVetoStatus(demographic.veto_status),
                status_after=UserVetoStatus(body.status_after.value),
                comment=body.comment,
        ))
        session.commit()
    else:
        raise HTTPException(status_code=status.HTTP_208_ALREADY_REPORTED, detail="No change")
    result = UserModel.one_user(session, str(user_id))
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found after update")
    return result


@router.post('/')
async def create_user(request: Request,
                      _is_admin: bool = Depends(is_admin_user),
                      current_user: ArxivUserClaims = Depends(get_authn_user),
                      session: Session = Depends(get_db)) -> UserModel:
    """Creates a new user - by POST"""
    if not current_user.is_owner:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only owner can create new users")
    body = await request.json()

    user = TapirUser()
    for key, value in body.items():
        if key in user.__dict__:
            setattr(user, key, value)
    session.add(user)
    session.flush()  # Ensure user_id is populated
    result = UserModel.one_user(session, str(user.user_id))
    if result is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")
    return result


@router.delete('/{user_id:int}')
def delete_user(response: Response,
                user_id: int,
                current_user: ArxivUserClaims = Depends(get_authn_user),
                session: Session = Depends(get_db)):
    check_authnz(None, current_user, user_id)
    user: TapirUser | None = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.flag_deleted = True

    session.commit()
    session.refresh(user)  # Refresh the instance with the updated data
    response.status_code = 204
    return


class UserDocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    submitted_count: int
    owns_count: int
    authored_count: int


@router.get("/{user_id:int}/document-summary")
def get_user_document_summary(user_id:int,
                              current_user: ArxivUserClaims = Depends(get_authn_user),
                              db: Session = Depends(get_db)) -> UserDocumentSummary:
    check_authnz(None, current_user, user_id)
    # @ignore-types
    user = UserModel.base_select(db).filter(TapirUser.user_id == user_id).one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserDocumentSummary.model_validate(document_summary(db, str(user_id)))


class CategoryYesNo(BaseModel):
    id: str  # for react-admin, it always heeds a unique ID
    archive: str
    subject_class: str
    positive: bool
    reason: str


def from_submit_to_to_category_yes_no(accessor: EndorsementAccessor, cat: Category, user: UserModel) -> CategoryYesNo:
    canon_archive, canon_subject_class = canonicalize_category(cat.archive, cat.subject_class)
    positive, biz = can_user_submit_to(accessor, user, canon_archive, canon_subject_class)
    return CategoryYesNo(
        id=f"{canon_archive}.{canon_subject_class}",
        archive=canon_archive,
        subject_class=canon_subject_class,
        positive=positive,
        reason=biz.reason
    )


@router.get("/{user_id:int}/can-submit-to")
def get_user_can_submit_to(
        response: Response,
        user_id:int,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        session: Session = Depends(get_db)) -> List[CategoryYesNo]:
    from .biz.endorsement_io import EndorsementDBAccessor
    check_authnz(None, current_user, user_id)

    categories = session.query(Category).all()
    accessor = EndorsementDBAccessor(session)

    result = []
    user = accessor.get_user(str(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    covered: dict[str, bool] = {}

    cat: Category
    for cat in categories:
        canon_archive, canon_subject_class = canonicalize_category(cat.archive, cat.subject_class)
        tag = f"{canon_archive}.{canon_subject_class}"
        if tag in covered:
            continue
        covered[tag] = True
        result.append(from_submit_to_to_category_yes_no(accessor, cat, user))

    response.headers['X-Total-Count'] = str(len(result))
    return result


def from_can_endorse_for_to_category_yes_no(accessor: EndorsementAccessor, cat: Category, user: UserModel) -> CategoryYesNo:
    canon_archive, canon_subject_class = canonicalize_category(cat.archive, cat.subject_class)
    positive, biz = can_user_endorse_for(accessor, user, canon_archive, canon_subject_class)
    return CategoryYesNo(
        id=f"{canon_archive}.{canon_subject_class}",
        archive=canon_archive,
        subject_class=canon_subject_class,
        positive=positive,
        reason=biz.reason
    )


@router.get("/{user_id:int}/can-endorse-for")
def get_user_can_endorse_for(
        response: Response,
        user_id: int,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        session: Session = Depends(get_db)) -> List[CategoryYesNo]:
    check_authnz(None, current_user, user_id)
    categories: List[Category] = session.query(Category).all()
    from .biz.endorsement_io import EndorsementDBAccessor
    accessor = EndorsementDBAccessor(session)

    result = []
    user = accessor.get_user(str(user_id))
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    covered: dict[str, bool] = {}

    cat: Category
    for cat in categories:
        canon_archive, canon_subject_class = canonicalize_category(cat.archive, cat.subject_class)
        tag = f"{canon_archive}.{canon_subject_class}"
        if tag in covered:
            continue
        covered[tag] = True
        result.append(from_can_endorse_for_to_category_yes_no(accessor, cat, user))

    response.headers['X-Total-Count'] = str(len(result))
    return result



class UserByUsernameModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int
    email: str
    first_name: str
    last_name: str
    suffix_name: Optional[str] = None
    share_first_name: bool = True
    share_last_name: bool = True
    share_email: int = 8
    email_bouncing: bool = False
    joined_date: datetime
    joined_ip_num: Optional[str] = None
    joined_remote_host: str
    flag_internal: bool = False
    flag_edit_users: bool = False
    flag_edit_system: bool = False
    flag_email_verified: bool = False
    flag_approved: bool = True
    flag_deleted: bool = False
    flag_banned: bool = False
    flag_wants_email: Optional[bool] = None
    flag_html_email: Optional[bool] = None
    tracking_cookie: Optional[str] = None
    flag_allow_tex_produced: Optional[bool] = None
    flag_can_lock: Optional[bool] = None

    @field_validator('first_name', 'last_name', 'suffix_name', 'id')
    @classmethod
    def strip_field_value(cls, value: str | None) -> str | None:
        return value.strip() if value else value


    @staticmethod
    def base_select(session: Session):

        return (session.query(
            TapirNickname.nickname.label("id"),
            TapirUser.user_id,
            cast(TapirUser.email, LargeBinary).label("email"),
            cast(TapirUser.first_name, LargeBinary).label("first_name"),
            cast(TapirUser.last_name, LargeBinary).label("last_name"),
            cast(TapirUser.suffix_name, LargeBinary).label("suffix_name"),
            TapirUser.share_first_name,
            TapirUser.share_last_name,
            TapirUser.share_email,
            TapirUser.email_bouncing,
            TapirUser.joined_date,
            TapirUser.joined_ip_num,
            TapirUser.joined_remote_host,
            TapirUser.flag_internal,
            TapirUser.flag_edit_users,
            TapirUser.flag_edit_system,
            TapirUser.flag_email_verified,
            TapirUser.flag_approved,
            TapirUser.flag_deleted,
            TapirUser.flag_banned,
            TapirUser.flag_wants_email,
            TapirUser.flag_html_email,
            TapirUser.tracking_cookie,
            TapirUser.flag_allow_tex_produced,
            TapirUser.flag_can_lock,
        )
        .join(TapirUser, TapirUser.user_id == TapirNickname.user_id))

    @property
    def is_admin(self) -> bool:
        return self.flag_edit_users or self.flag_edit_system


    @staticmethod
    def to_model(user: UserByUsernameModel | Row | dict, session: Optional[Session] = None) -> 'UserByUsernameModel':
        """
        Given data to user model data.
        :param user:  DB row, dict or UserByUsernameModel.
        :param session: SQLAlchemy db session
        :return: result: UserByUsernameModel data
        """
        # If the incoming is already a dict, to_model is equivalet of calling model_validate
        if isinstance(user, dict):
            result = UserByUsernameModel.model_validate(user)
        elif isinstance(user, UserByUsernameModel):
            # This is just a copy
            return UserByUsernameModel.model_validate(user.model_dump())
        elif isinstance(user, Row):
            row = user._asdict()
            for field in _tapir_user_utf8_fields_ + _demographic_user_utf8_fields_:
                if field == "username":
                    field = "id"
                if field not in row:
                    continue
                if row[field] is None:
                    continue
                if isinstance(row[field], bytes):
                    row[field] = row[field].decode("utf-8") if row[field] is not None else None
                elif isinstance(row[field], str):
                    logger.warning(f"Field {field} is unexpectedly string. value = '{row[field]}'. You may need to fix it")
                    pass
                else:
                    raise ValueError(f"Field {field} needs to be BLOB access")
            result = UserByUsernameModel.model_validate(row)
        else:
            raise ValueError("Not Row, UserByUsernameModel or dict")
        return result


@users_by_username_router.get("/")
async def list_users_by_username(
        response: Response,
        _sort: Optional[str] = Query("last_name,first_name", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        flag_is_mod: Optional[bool] = Query(None, description="moderator"),
        email: Optional[str] = Query(None),
        name: Optional[str] = Query(None),
        last_name: Optional[str] = Query(None),
        first_name: Optional[str] = Query(None),
        flag_edit_users: Optional[bool] = Query(None),
        flag_email_verified: Optional[bool] = Query(None),
        start_joined_date: Optional[date] = Query(None, description="Start date for filtering"),
        end_joined_date: Optional[date] = Query(None, description="End date for filtering"),
        id: Optional[List[str]] = Query(None, description="List of username  to filter by"),
        db: Session = Depends(get_db),
        _is_admin: bool = Depends(is_admin_user),
) -> List[UserByUsernameModel]:
    """
    List users
    """
    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    order_columns = []
    sort_nickname_alias = None
    if _sort:
        keys = _sort.split(",")
        for key in keys:
            if key == "id":
                key = "user_id"
            if key == "username":
                if sort_nickname_alias is None:
                    sort_nickname_alias = aliased(TapirNickname)
                order_columns.append(sort_nickname_alias.nickname)
            else:
                try:
                    order_column = getattr(TapirUser, key)
                    order_columns.append(order_column)
                except AttributeError:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Invalid sort field")

    query = UserByUsernameModel.base_select(db)

    # Join with TapirNickname if needed for sorting by username
    if sort_nickname_alias is not None:
        query = query.join(sort_nickname_alias, TapirUser.user_id == sort_nickname_alias.user_id)

    if id is not None:
        nick1 = aliased(TapirNickname)
        query = query.join(nick1, nick1.user_id == TapirUser.user_id)
        query = query.filter(nick1.nickname.in_(id))

    else:
        if flag_edit_users is not None:
            query = query.filter(TapirUser.flag_edit_users == flag_edit_users)

        if flag_is_mod is not None:
            subquery = select(distinct(t_arXiv_moderators.c.user_id))
            if flag_is_mod:
                # I think this is faster but I cannot make it work...
                # query = query.join(t_arXiv_moderators, TapirUser.user_id == t_arXiv_moderators.c.user_id)
                query = query.filter(TapirUser.user_id.in_(subquery))
            else:
                query = query.filter(~TapirUser.user_id.in_(subquery))

        if name and first_name is None and last_name is None:
            if "," in name:
                names = name.split(",")
                if len(names) > 1:
                    last_name = names[0].strip()
                    first_name = names[1].strip()
                else:
                    last_name = names[0].strip()
            elif " " in name:
                names = [elem.strip() for elem in name.split(' ') if elem.strip()]
                if len(names) > 1:
                    last_name = names[0]
                    first_name = names[1]
                else:
                    last_name = names[0]
                pass
            elif re.match(r"^[0-9]+$", name):
                query = query.filter(TapirUser.user_id == name)
            else:
                last_name = name.strip()
                pass
            pass

        if first_name:
            query = query.filter(TapirUser.first_name.startswith(first_name))

        if last_name:
            query = query.filter(TapirUser.last_name.startswith(last_name))

        if email:
            query = query.filter(TapirUser.email.startswith(email))

        if flag_email_verified is not None:
            query = query.filter(TapirUser.flag_email_verified == flag_email_verified)

        if start_joined_date or end_joined_date:
            t_begin = datetime_to_epoch(start_joined_date, VERY_OLDE)
            t_end = datetime_to_epoch(end_joined_date, date.today(), hour=23, minute=59, second=59)
            query = query.filter(TapirUser.joined_date.between(t_begin, t_end))


    for column in order_columns:
        if _order == "DESC":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [UserByUsernameModel.to_model(user) for user in query.offset(_start).limit(_end - _start).all()]
    return result


class UserActivitySummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    tapir_sessions_count: int
    admin_log_count: int
    # email_history_count: int
    # it is in AAA - I could borrow the code but not worth it


@router.get("/{user_id:int}/activity-summary")
def get_user_activity_summary(user_id:int,
                              current_user: ArxivUserClaims = Depends(get_authn_user),
                              session: Session = Depends(get_db)) -> UserActivitySummary:
    check_authnz(None, current_user, user_id)
    tapir_sessions_count = session.query(TapirSession).filter(TapirSession.user_id == user_id).count()
    admin_log_count = session.query(TapirAdminAudit).filter(or_(TapirAdminAudit.admin_user == user_id,
                                                                TapirAdminAudit.affected_user == user_id)).count()
    return UserActivitySummary(
        tapir_sessions_count=tapir_sessions_count,
        admin_log_count=admin_log_count,
    )
