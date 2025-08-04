"""arXiv user routes."""
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
from pydantic import BaseModel

from sqlalchemy import select, distinct, and_, inspect
from sqlalchemy.orm import Session, aliased

from arxiv.db.models import (TapirUser, TapirNickname, t_arXiv_moderators, Demographic,
                             t_arXiv_black_email, Category)
from arxiv_bizlogic.bizmodels.user_model import UserModel

from . import is_admin_user, get_db, VERY_OLDE, datetime_to_epoch, check_authnz
from .audit import record_user_prop_admin_action
from .biz import canonicalize_category
from .biz.document_biz import document_summary
from .biz.endorsement_biz import can_user_submit_to, can_user_endorse_for, EndorsementAccessor


router = APIRouter(prefix="/users")


class UserUpdateModel(UserModel):
    pass

class UserPropertyUpdateRequest(BaseModel):
    property_name: str
    property_value: str | bool
    comment: Optional[str]


class UserVetoStatusRequest(BaseModel):
    status_before: UserVetoStatus
    status_after: UserVetoStatus
    comment: Optional[str]


class UserCommentRequest(BaseModel):
    comment: str


@router.get("/{user_id:int}")
def get_one_user(user_id:int,
                 current_user: ArxivUserClaims = Depends(get_authn),
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
                          _start: Optional[int] = Query(0, alias="_start"),
                          _end: Optional[int] = Query(100, alias="_end"),
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
        response: Response,
        _sort: Optional[str] = Query("last_name,first_name", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
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
        start_joined_date: Optional[date] = Query(None, description="Start date for filtering"),
        end_joined_date: Optional[date] = Query(None, description="End date for filtering"),
        id: Optional[List[int]] = Query(None, description="List of user IDs to filter by"),
        q: Optional[str] = Query(None, description="Query string"),
        db: Session = Depends(get_db),
        _is_admin: bool = Depends(is_admin_user),
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

    query = UserModel.base_select(db)
    
    # Join with TapirNickname if needed for sorting by username
    if sort_nickname_alias is not None:
        query = query.join(sort_nickname_alias, TapirUser.user_id == sort_nickname_alias.user_id)

    if id is not None:
        query = query.filter(TapirUser.user_id.in_(id))

    else:
        if q:
            if "@" in q:
                query = query.filter(TapirUser.email == q)
            elif q[0] in "0123456789":
                query = query.filter(TapirUser.user_id == q)
            else:
                query = query.filter(TapirUser.last_name == q)

        if suspect:
            dgfx = aliased(Demographic)
            query = query.join(dgfx, dgfx.user_id == TapirUser.user_id)
            query = query.filter(dgfx.flag_suspect == suspect)

        if user_class in ["owner", "admin"]:
            query = query.filter(TapirUser.policy_class == False)

        if user_class in ["owner"]:
            query = query.filter(TapirUser.flag_edit_system == True)

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

        if username:
            nick1 = aliased(TapirNickname)
            query = query.join(nick1, nick1.user_id == TapirUser.user_id)
            query = query.filter(nick1.nickname.like(username + "%"))

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

        if flag_veto is not None:
            dgfx2 = aliased(Demographic)
            query = query.join(dgfx2, dgfx2.user_id == TapirUser.user_id)
            query = query.filter(dgfx2.flag_suspect == suspect)
            if flag_veto:
                query = query.filter(dgfx2.veto_status != "ok")
            else:
                query = query.filter(dgfx2.veto_status == "ok")

        if flag_proxy is not None:
            dgfx3 = aliased(Demographic)
            query = query.join(dgfx3, dgfx3.user_id == TapirUser.user_id)
            query = query.filter(dgfx3.flag_proxy == flag_proxy)

        if email_bouncing is not None:
            query = query.filter(TapirUser.email_bouncing == email_bouncing)

        # This is how Tapir limits the search
        if is_non_academic and start_joined_date is None:
            start_joined_date = date.today() - timedelta(days=90)

        if start_joined_date or end_joined_date:
            t_begin = datetime_to_epoch(start_joined_date, VERY_OLDE)
            t_end = datetime_to_epoch(end_joined_date, date.today(), hour=23, minute=59, second=59)
            query = query.filter(TapirUser.joined_date.between(t_begin, t_end))

        if is_non_academic:
            # Inner join with arxiv_black_email on pattern match with email
            query = query.join(t_arXiv_black_email, TapirUser.email.like(t_arXiv_black_email.c.pattern))

        if clue is not None:
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

    for column in order_columns:
        if _order == "DESC":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [UserModel.to_model(user) for user in query.offset(_start).limit(_end - _start).all()]
    return result


def sanitize_user_update_data(update_data: dict) -> dict:
    for key in ["id", "user_id", "username", "moderated_categories", "moderated_archives", "tapir_policy_classes", "orcid_id", "flag_is_mod"]:
        if key in update_data:
            del update_data[key]
    return update_data



@router.put('/{user_id:int}/property')
async def update_user_property(
        request: Request,
        user_id: int,
        body: UserPropertyUpdateRequest,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        remote_ip: Optional[str] = Depends(get_client_host),
        remote_hostname: Optional[str] = Depends(get_client_host_name),
        tracking_cookie: Optional[str] = Depends(get_tapir_tracking_cookie),
        session: Session = Depends(get_db)) -> UserModel:
    """Update user property - by PUT"""

    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can update user properties")

    user = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if hasattr(user, body.property_name):
        old_value = getattr(user, body.property_name)
        if old_value is None or old_value != body.property_value:
            setattr(user, body.property_name, body.property_value)
            record_user_prop_admin_action(session, current_user.user_id,
                                          body.property_name, user_id, old_value, body.property_value, body.comment,
                                          remote_ip, remote_hostname, tracking_cookie)
    session.commit()
    return UserModel.one_user(session, user_id)


@router.post('/{user_id:int}/comment')
async def create_user_comment(
        response: Response,
        user_id: int,
        body: UserCommentRequest,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        remote_ip: Optional[str] = Depends(get_client_host),
        remote_hostname: Optional[str] = Depends(get_client_host_name),
        tracking_cookie: Optional[str] = Depends(get_tapir_tracking_cookie),
        session: Session = Depends(get_db)) -> Response:
    """Add comment to a user by POST"""

    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admin can update user properties")

    user = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    admin_audit(AdminAudit_AddComment(
            str(current_user.user_id),
            str(user_id),
            str(current_user.session_id),
            remote_ip=remote_ip,
            remote_hostname=remote_hostname,
            tracking_cookie=tracking_cookie,
            comment=body.comment,
    ))
    response.status_code = status.HTTP_201_CREATED
    return response



@router.put('/{user_id:int}/veto-status/')
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
        admin_audit(AdminAudit_ChangeStatus(
            current_user.user_id,
            user_id,
            current_user.session_id,
            remote_ip=remote_ip,
            remote_hostname=remote_hostname,
            tracking_cookie=tracking_cookie,
            status_before=demographic.veto_status,
            status_after=body.status_after.value,
            comment=body.comment,
        ))
        session.commit()
    else:
        raise HTTPException(status_code=status.HTTP_208_ALREADY_REPORTED, detail="No change")
    return UserModel.one_user(session, user_id)


@router.post('/')
async def create_user(request: Request,
                      _is_admin: bool = Depends(is_admin_user),
                      session: Session = Depends(get_db)) -> UserModel:
    """Creates a new user - by POST"""
    body = await request.json()

    user = TapirUser()
    for key, value in body.items():
        if key in user.__dict__:
            setattr(user, key, value)
    session.add(user)
    return UserModel.one_user(session, user.user_id)


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
    submitted_count: int
    owns_count: int
    authored_count: int
    class Config:
        from_attributes = True


@router.get("/{user_id:int}/document-summary")
def get_user_document_summary(user_id:int,
                              current_user: ArxivUserClaims = Depends(get_authn),
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
        current_user: ArxivUserClaims = Depends(get_authn),
        session: Session = Depends(get_db)) -> List[CategoryYesNo]:
    from .biz.endorsement_io import EndorsementDBAccessor
    check_authnz(None, current_user, user_id)

    categories = session.query(Category).all()
    accessor = EndorsementDBAccessor(session)

    result = []
    user = accessor.get_user(user_id)
    covered = {}

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
        current_user: ArxivUserClaims = Depends(get_authn),
        session: Session = Depends(get_db)) -> List[CategoryYesNo]:
    check_authnz(None, current_user, user_id)
    categories: List[Category] = session.query(Category).all()
    from .biz.endorsement_io import EndorsementDBAccessor
    accessor = EndorsementDBAccessor(session)

    result = []
    user = accessor.get_user(user_id)
    covered = {}

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
