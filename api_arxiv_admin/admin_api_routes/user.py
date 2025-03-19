"""arXiv user routes."""
from http.client import HTTPException
from typing import Optional, List
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Query, HTTPException, status, Depends, Request
from fastapi.responses import Response

from sqlalchemy import select, case, distinct, exists, and_, cast, LargeBinary
from sqlalchemy.orm import Session, aliased

from pydantic import BaseModel

from arxiv.db.models import (TapirUser, TapirNickname, t_arXiv_moderators, Demographic,
                             t_arXiv_black_email, Category)
from arxiv_bizlogic.bizmodels.user_model import UserModel

from . import is_admin_user, get_db, VERY_OLDE, datetime_to_epoch

router = APIRouter(dependencies=[Depends(is_admin_user)], prefix="/users")


class UserUpdateModel(UserModel):
    pass


@router.get("/{user_id:int}")
def get_one_user(user_id:int, db: Session = Depends(get_db)) -> UserModel:
    # @ignore-types
    user = UserModel.base_select(db).filter(TapirUser.user_id == user_id).one_or_none()
    if user:
        return UserModel.to_model(user)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")


@router.get("/username/")
def list_user_by_username(response: Response,
                          _sort: Optional[str] = Query("last_name,first_name", description="sort by"),
                          _order: Optional[str] = Query("ASC", description="sort order"),
                          _start: Optional[int] = Query(0, alias="_start"),
                          _end: Optional[int] = Query(100, alias="_end"),
                          id: Optional[List[str]] = Query(None, description="List of user IDs to filter by"),
                          db: Session = Depends(get_db)
                          ) -> List[UserModel]:
    """
    List users by username
    """
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
                          db: Session = Depends(get_db)
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
        email_bouncing: Optional[bool] = Query(None),
        clue: Optional[str] = Query(None),
        suspect: Optional[bool] = Query(None),
        start_joined_date: Optional[date] = Query(None, description="Start date for filtering"),
        end_joined_date: Optional[date] = Query(None, description="End date for filtering"),
        id: Optional[List[int]] = Query(None, description="List of user IDs to filter by"),
        q: Optional[str] = Query(None, description="Query string"),
        db: Session = Depends(get_db)
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
            query = query.filter(TapirUser.tapir_nicknames.contains(username))

        if first_name:
            query = query.filter(TapirUser.first_name.contains(first_name))

        if last_name:
            query = query.filter(TapirUser.last_name.contains(last_name))

        if email:
            query = query.filter(TapirUser.email.contains(email))

        if flag_email_verified is not None:
            query = query.filter(TapirUser.flag_email_verified == flag_email_verified)

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
                      session: Session = Depends(get_db)) -> UserModel:
    """Update user - by PUT"""
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

    for key, value in update_data.items():
        if hasattr(user, key):
            setattr(user, key, value)  # Update the user's fields
        elif demographic and hasattr(demographic, key):
            setattr(demographic, key, value)
        else:
            raise HTTPException(status_code=404, detail="Bad update data")

    session.commit()
    session.refresh(user)  # Refresh the instance with the updated data
    return UserModel.one_user(session, user.user_id)


@router.post('/')
async def create_user(request: Request, session: Session = Depends(get_db)) -> UserModel:
    """Creates a new user - by POST"""
    body = await request.json()

    user = TapirUser()
    for key, value in body.items():
        if key in user.__dict__:
            setattr(user, key, value)
    session.add(user)
    return UserModel.one_user(session, user.user_id)


@router.delete('/{user_id:int}')
def delete_user(response: Response, user_id: int, session: Session = Depends(get_db)):
    user: TapirUser | None = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.flag_deleted = True

    session.commit()
    session.refresh(user)  # Refresh the instance with the updated data
    response.status_code = 204
    return
