"""arXiv publci user routes."""
from __future__ import annotations
from functools import reduce
from http.client import HTTPException
from typing import Optional

from arxiv.auth.user_claims import ArxivUserClaims
from arxiv_bizlogic.fastapi_helpers import get_authn
from fastapi import APIRouter, Query, HTTPException, status, Depends, Request

from sqlalchemy import select, case, exists, LargeBinary, cast
from sqlalchemy.orm import Session

from pydantic import BaseModel

from arxiv.db.models import (TapirUser, TapirNickname, t_arXiv_moderators, Demographic, TapirCountry,
                             t_arXiv_black_email, t_arXiv_white_email, Category)
from sqlalchemy_helper import sa_model_to_pydandic_model

from . import is_admin_user, get_db, VERY_OLDE, datetime_to_epoch, is_any_user, get_current_user

router = APIRouter(prefix="/public-users")


class PublicUserModel(BaseModel):

    class Config:
        from_attributes = True

    id: int
    flag_is_mod: Optional[bool]

    email: Optional[str]
    first_name: str
    last_name: str
    suffix_name: str

    flag_deleted: bool

    # From Demographic
    country: Optional[str]  # = mapped_column(String(2), nullable=False, index=True, server_default=FetchedValue())
    affiliation: Optional[str]  # = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    url: Optional[str]  # = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    type: Optional[int]  # = mapped_column(SmallInteger, index=True)
    archive: Optional[str]  # = mapped_column(String(16))
    subject_class: Optional[str]  # = mapped_column(String(16))

    flag_group_physics: Optional[int]  # = mapped_column(Integer, index=True)
    flag_group_math: Optional[
        int]  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_cs: Optional[int]  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_nlin: Optional[
        int]  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_test: Optional[int]  # = mapped_column(Integer, nullable=False, server_default=text("'0'"))
    flag_group_q_bio: Optional[
        int]  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_q_fin: Optional[
        int]  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_stat: Optional[
        int]  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_eess: Optional[
        int]  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_econ: Optional[
        int]  # = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))

    @staticmethod
    def base_select(db: Session):
        is_mod_subquery = exists().where(t_arXiv_moderators.c.user_id == TapirUser.user_id).correlate(TapirUser)
        nick_subquery = select(TapirNickname.nickname).where(TapirUser.user_id == TapirNickname.user_id).correlate(TapirUser).limit(1).scalar_subquery()
        """
        mod_subquery = select(
            func.concat(t_arXiv_moderators.c.user_id, "+",
                        t_arXiv_moderators.c.archive, "+",
                        t_arXiv_moderators.c.subject_class)
        ).where(t_arXiv_moderators.c.user_id == TapirUser.user_id).correlate(TapirUser)
        """

        return (db.query(
            TapirUser.user_id.label("id"),
            TapirUser.email,
            cast(TapirUser.first_name, LargeBinary).label("first_name"),
            cast(TapirUser.last_name, LargeBinary).label("last_name"),
            cast(TapirUser.suffix_name, LargeBinary).label("suffix_name"),
            TapirUser.flag_deleted,
            case(
                (is_mod_subquery, True),  # Pass each "when" condition as a separate positional argument
                else_=False
            ).label("flag_is_mod"),
            # mod_subquery.label("moderator_id"),
            Demographic.country,
            cast(Demographic.affiliation, LargeBinary).label("affiliation"),
            cast(Demographic.url, LargeBinary).label("url"),
            Demographic.type,
            Demographic.archive,
            Demographic.subject_class,

            Demographic.flag_group_physics,
            Demographic.flag_group_math,
            Demographic.flag_group_cs,
            Demographic.flag_group_nlin,
            Demographic.flag_group_test,
            Demographic.flag_group_q_bio,
            Demographic.flag_group_q_fin,
            Demographic.flag_group_stat,
            Demographic.flag_group_eess,
            Demographic.flag_group_econ,
        ).outerjoin(Demographic, TapirUser.user_id == Demographic.user_id)
        )

    @staticmethod
    def one_user(db: Session, user_id: int) -> Optional[PublicUserModel]:
        user = PublicUserModel.base_select(db).filter(TapirUser.user_id == user_id).one_or_none()
        if user:
            return PublicUserModel.model_validate(user)
        return None
    pass

@router.get("/{user_id:int}")
def get_one_public_user(user_id:int, db: Session = Depends(get_db)) -> PublicUserModel:
    # @ignore-types
    user = PublicUserModel.base_select(db).filter(TapirUser.user_id == user_id).one_or_none()
    if user:
        return PublicUserModel.model_validate(sa_model_to_pydandic_model(user, PublicUserModel))
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.get("/")
def get_one_public_user_with_query(
        user_id: str = Query(None),
        email: str = Query(None),
        username: str = Query(None),
        current_user: ArxivUserClaims = Depends(get_authn),
        db: Session = Depends(get_db)) -> PublicUserModel:
    count = reduce(lambda t, s: t + (1 if s else 0), [user_id, email, username], 0)
    if count == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No query given")
    elif count > 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many query given. user_id, email or username")

    user = None
    if user_id:
        user = PublicUserModel.base_select(db).filter(TapirUser.user_id == user_id).one_or_none()
    elif email:
        user = PublicUserModel.base_select(db).filter(TapirUser.email == email).one_or_none()
    elif username:
        nick:TapirNickname | None = db.query(TapirNickname).filter(TapirNickname.nickname == username).one_or_none()
        if not nick:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="username not found")
        user = PublicUserModel.base_select(db).filter(TapirUser.user_id == nick.user_id).one_or_none()

    if user:
        # @ignore-types
        public_user = PublicUserModel.model_validate(sa_model_to_pydandic_model(user, PublicUserModel))
        if current_user is None or (not current_user.is_admin):
            # You'd be able to get email only when you query email
            public_user.email = email
        return public_user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
