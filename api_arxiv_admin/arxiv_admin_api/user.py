"""arXiv user routes."""
from typing import Optional, List
from datetime import date, timedelta

from arxiv.auth.user_claims import ArxivUserClaims
from arxiv_bizlogic.fastapi_helpers import get_current_user, get_authn
from fastapi import APIRouter, Query, status, Depends, Request
from fastapi.responses import Response
from fastapi.exceptions import HTTPException
from pydantic import BaseModel

from sqlalchemy import select, distinct, and_
from sqlalchemy.orm import Session, aliased

from arxiv.db.models import (TapirUser, TapirNickname, t_arXiv_moderators, Demographic,
                             t_arXiv_black_email, Category)
from arxiv_bizlogic.bizmodels.user_model import UserModel

from . import is_admin_user, get_db, VERY_OLDE, datetime_to_epoch, check_authnz
from .biz import canonicalize_category
from .biz.document_biz import document_summary
from .biz.endorsement_biz import can_user_submit_to, can_user_endorse_for, EndorsementAccessor


router = APIRouter(prefix="/users")


class UserUpdateModel(UserModel):
    pass


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

    query = UserModel.base_select(db)

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

        if first_name:
            query = query.filter(TapirUser.first_name.contains(first_name))

        if last_name:
            query = query.filter(TapirUser.last_name.contains(last_name))

        if email:
            query = query.filter(TapirUser.email.contains(email))

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


@router.put('/{user_id:int}')
async def update_user(request: Request,
                      user_id: int,
                      user_update: UserUpdateModel,
                      current_user: ArxivUserClaims = Depends(get_authn),
                      session: Session = Depends(get_db)) -> UserModel:
    """Update user - by PUT"""
    check_authnz(None, current_user, user_id)
    user: TapirUser | None = session.query(TapirUser).filter(TapirUser.user_id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    demographic = session.query(Demographic).filter(Demographic.user_id == user_id).first()
    update_data = user_update.model_dump(exclude_unset=True)  # Exclude fields that were not provided

    # check new category
    if hasattr(update_data, 'archive'):
        if hasattr(update_data, 'subject_class'):
            new_category = session.query(Category).filter(and_(
                Category.archive == update_data.archive,
                Category.subject_class == update_data.subject_class
            )).one_or_none()
            if new_category is None:
                raise HTTPException(status_code=404, detail="Category not found")
        else:
            raise HTTPException(status_code=404, detail="Need archive and subject_class")
    elif hasattr(update_data, 'subject_class'):
        raise HTTPException(status_code=404, detail="Need archive and subject_class")

    _ = '''
    email: EmailStr
    first_name: str
    last_name: str
    suffix_name: Optional[str] = None
    share_first_name: bool = True
    share_last_name: bool = True
    username: str
    share_email: int = 8
    email_bouncing: bool = False
    policy_class: int
    joined_date: int
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

    # From Demographic
    country: Optional[
        str] = None  # = mapped_column(String(2), nullable=False, index=True, server_default=FetchedValue())
    affiliation: Optional[str] = None  # = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    url: Optional[str] = None  # = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    type: Optional[int] = None  # = mapped_column(SmallInteger, index=True)
    archive: Optional[str] = None  # = mapped_column(String(16))
    subject_class: Optional[str] = None  # = mapped_column(String(16))
    original_subject_classes: str  # = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    flag_group_physics: Optional[int] = None  # = mapped_column(Integer, index=True)
    flag_group_math: Optional[
        int]  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_cs: Optional[
        int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_nlin: Optional[
        int]  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_proxy: Optional[int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_journal: Optional[
        int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_xml: Optional[int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    dirty: Optional[int] = None  # = mapped_column(Integer, nullable=False, server_default=text("'0'"))
    flag_group_test: Optional[int] = None  # = mapped_column(Integer, nullable=False, server_default=text("'0'"))
    flag_suspect: Optional[
        int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_q_bio: Optional[
        int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_q_fin: Optional[
        int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_stat: Optional[
        int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_eess: Optional[
        int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_econ: Optional[
        int] = None  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    veto_status: Optional[
        VetoStatusEnum] = None  # Mapped[Literal['ok', 'no-endorse', 'no-upload', 'no-replace']] = mapped_column(Enum('ok', 'no-endorse', 'no-upload', 'no-replace'), nullable=False, server_default=text("'ok'"))

    flag_is_mod: Optional[bool] = None
    moderated_categories: Optional[List[str]] = None
    moderated_archives: Optional[List[str]] = None

    tapir_policy_classes: Optional[List[int]] = None

    orcid_id: Optional[str] = None

    @field_validator('first_name', 'last_name', 'suffix_name', 'username', 'country', 'affiliation', 'url',
                     'archive', 'subject_class', 'original_subject_classes', 'orcid_id',)
    @classmethod
    def strip_field_value(cls, value: str | None) -> str | None:
        return value.strip() if value else value


'''


    session.commit()
    session.refresh(user)  # Refresh the instance with the updated data
    return UserModel.one_user(session, user.user_id)


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
                current_user: ArxivUserClaims = Depends(get_authn),
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


    categories: List[Category] = session.query(Category).all()
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

    response.headers['X-Total-Count'] = str(result)
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

    response.headers['X-Total-Count'] = str(result)
    return result
