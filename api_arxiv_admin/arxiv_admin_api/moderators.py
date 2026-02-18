"""arXiv moderator routes."""
from typing import Optional, List, cast

from arxiv.auth.user_claims import ArxivUserClaims
from arxiv_bizlogic.audit_event import admin_audit, AdminAudit_MakeModerator, AdminAudit_UnmakeModerator
from arxiv_bizlogic.fastapi_helpers import get_authn_user, get_client_host, get_client_host_name, \
    get_tapir_tracking_cookie
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response

from sqlalchemy import insert, func, and_, select # case, Select, distinct, exists, update,
from sqlalchemy.engine import CursorResult
from sqlalchemy.orm import Session, joinedload, Query as SAQuery

from pydantic import BaseModel, Field, ConfigDict
from arxiv.base import logging
# from arxiv.db import transaction
from arxiv.db.models import t_arXiv_moderators, TapirUser

from . import is_admin_user, get_db, datetime_to_epoch, VERY_OLDE
from .biz.modapi_clear_user_cache import modapi_clear_user_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/moderators")


async def _modapi_clear_user_cache(user_id: int, request: Request):
    try:
        await modapi_clear_user_cache(
            user_id,
            base_url=request.app.extra["MODAPI_URL"],
            modkey=request.app.extra["MODAPI_MODKEY"])
    except:
        logger.warning("Failed to clear user cache", exc_info=True, extra={"user_id": user_id})
    pass

"""
<?php

   require "tapir-auth-plus.php";
   require "tapir-audit.php";

   $auth=new Tapir_Auth_Plus(tapir_connect_rw());
   $auth->required(M4_CAP_EDIT_USERS);

   $user_id=$_GET["user_id"] ;
   $category=trim($_GET["category"]);
   $tapir_dest=$_GET["tapir_dest"];

   list($archive,$subject_class)=split("\.",$category);

   if (!$subject_class)
     $subject_class="";

   $_user_id=addslashes($user_id);
   $_archive=addslashes($archive);
   $_subject_class=addslashes($subject_class);

   $sql="SELECT COUNT(*) FROM arXiv_categories WHERE archive='$_archive' AND subject_class='$_subject_class'";
   $category_count=$auth->conn->select_scalar($sql);

   if (!$category_count) {
      $auth->perish("Invalid category [$category]");
   };

   $sql="SELECT COUNT(*) FROM arXiv_moderators WHERE archive='$_archive' AND subject_class='$_subject_class' AND user_id=$user_id";
   $moderator_count=$auth->conn->select_scalar($sql); 

   if ($moderator_count) {
      $sql="DELETE FROM arXiv_moderators WHERE user_id=$user_id AND archive='$_archive' AND subject_class='$_subject_class'";
      $auth->conn->query($sql);
      tapir_audit_admin($user_id,"unmake-moderator",$category);
   } else {
      $auth->conn->query("INSERT INTO arXiv_moderators (user_id,archive,subject_class) VALUES($user_id,'$_archive','$_subject_class')");
      tapir_audit_admin($user_id,"make-moderator",$category);
   };

?>
"""

class ModeratorModel(BaseModel):
    id: str
    user_id: int
    archive: str
    subject_class: Optional[str] = None
    is_public: bool
    no_email: bool
    no_web_email: bool
    no_reply_to: bool
    daily_update: bool

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def base_query(cls, db: Session) -> SAQuery:
        return db.query(
            func.concat(t_arXiv_moderators.c.user_id, "+",
                        t_arXiv_moderators.c.archive, "+",
                        t_arXiv_moderators.c.subject_class).label("id"),
            t_arXiv_moderators.c.user_id,
            t_arXiv_moderators.c.archive,
            t_arXiv_moderators.c.subject_class,
            t_arXiv_moderators.c.is_public,
            t_arXiv_moderators.c.no_email,
            t_arXiv_moderators.c.no_web_email,
            t_arXiv_moderators.c.no_reply_to,
            t_arXiv_moderators.c.daily_update,
        )


@router.get('/')
async def list_moderators_0(
        response: Response,
        _sort: Optional[str] = Query("archive,subject_class", description="keys"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        id: Optional[List[str]] = Query(None, description="List of Moderator IDs."),
        user_id: Optional[int] = Query(None),
        archive: Optional[str] = Query(None),
        subject_class: Optional[str] = Query(None),
        first_name: Optional[str] = Query(None),
        last_name: Optional[str] = Query(None),
        email: Optional[str] = Query(None, description="Moderator email"),
        db: Session = Depends(get_db)
    ) -> List[ModeratorModel]:
    if id:
        mods = []
        for combind_id in id:
            u_a_c = combind_id.split("+")
            if len(u_a_c) != 3:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="ID must have 3 elements separated by +, user id, archive, subject class.")
            mod = ModeratorModel.base_query(db).filter(and_(
                t_arXiv_moderators.c.user_id == u_a_c[0],
                t_arXiv_moderators.c.archive == u_a_c[1],
                t_arXiv_moderators.c.subject_class == u_a_c[2])).one_or_none()
            if mod is not None:
                mods.append(ModeratorModel.model_validate(mod))
        response.headers['X-Total-Count'] = str(mods)
        return mods
    else:
        if _start < 0 or _end < _start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid start or end index")
        query = ModeratorModel.base_query(db)
        order_columns = []
        if _sort:
            keys = _sort.split(",")
            for key in keys:
                if key in order_columns:
                    continue
                if key == "id":
                    order_columns = [
                        getattr(t_arXiv_moderators.c, col) for col in ["archive", "subject_class", "user_id"]
                    ]
                    continue
                try:
                    order_column = getattr(t_arXiv_moderators.c, key)
                    order_columns.append(order_column)
                except AttributeError:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Invalid start or end index")

        if user_id is not None:
            query = query.filter(t_arXiv_moderators.c.user_id == user_id)

        if archive is not None:
            query = query.filter(t_arXiv_moderators.c.archive.ilike(archive + "%"))

        if subject_class is not None:
            query = query.filter(t_arXiv_moderators.c.subject_class.ilike(subject_class + "%"))

        if first_name is not None or last_name is not None or email is not None:
            query = query.join(
                TapirUser,
                TapirUser.user_id == t_arXiv_moderators.c.user_id,
                )

            if first_name is not None:
                query = query.filter(TapirUser.first_name.like(first_name + "%"))
                pass
            if last_name is not None:
                query = query.filter(TapirUser.last_name.like(last_name + "%"))
                pass
            if email is not None:
                query = query.filter(TapirUser.email.like(email + "%"))
                pass
            pass

        for column in order_columns:
            if _order == "DESC":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())

        count = query.count()
        response.headers['X-Total-Count'] = str(count)
        return [ModeratorModel.model_validate(mod) for mod in query.offset(_start).limit(_end - _start).all()]


@router.get('/{archive}/subject-class')
async def list_moderators_1(
        response: Response,
        archive: str,
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        db: Session = Depends(get_db)
    ) -> List[ModeratorModel]:
    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    query = ModeratorModel.base_query(db).filter(t_arXiv_moderators.c.archive == archive)

    if _order == "DESC":
        query = query.order_by(t_arXiv_moderators.c.subject_class.desc())
    else:
        query = query.order_by(t_arXiv_moderators.c.subject_class.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    return [ModeratorModel.model_validate(mod) for mod in query.offset(_start).limit(_end - _start).all()]


@router.get('/{archive}/subject-class/{subject_class}')
async def list_moderators_2(
        response: Response,
        archive: str,
        subject_class: str,
        db: Session = Depends(get_db)
    ) -> List[ModeratorModel]:
    query = ModeratorModel.base_query(db).filter(
        and_(
            t_arXiv_moderators.c.archive == archive,
            t_arXiv_moderators.c.subject_class == subject_class)
    )
    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    return [ModeratorModel.model_validate(row) for row in query.all()]


@router.get('/{id:str}')
async def get_moderator(id: str, db: Session = Depends(get_db)) -> ModeratorModel:
    [user_id, archive, subject_class] = id.split("+")
    uid = int(user_id)
    mod = ModeratorModel.base_query(db).filter(
        and_(
            t_arXiv_moderators.c.user_id == uid,
            t_arXiv_moderators.c.archive == archive,
            t_arXiv_moderators.c.subject_class == subject_class
        )).one_or_none()
    if mod:
        return ModeratorModel.model_validate(mod)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.put('/{id:str}')
async def update_moderator(request: Request, id: str,
                           session: Session = Depends(get_db)) -> ModeratorModel:
    body = await request.json()
    [user_id, archive, subject_class] = id.split("+")
    uid = int(user_id)
    item = ModeratorModel.base_query(session).filter(
        and_(
            t_arXiv_moderators.c.user_id == uid,
            t_arXiv_moderators.c.archive == archive,
            t_arXiv_moderators.c.subject_class == subject_class)).one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Verify?
    for key, value in body.items():
        if key in item.__dict__:
            setattr(item, key, value)

    session.commit()
    session.refresh(item)  # Refresh the instance with the updated data
    await _modapi_clear_user_cache(uid, request)
    return ModeratorModel.model_validate(item)


class ModeratorCreateModel(BaseModel):
    user_id: int
    categories: List[str]
    is_public: bool
    no_email: bool
    no_web_email: bool
    no_reply_to: bool
    daily_update: bool

@router.post('/')
async def create_moderator(
        request: Request,
        body: ModeratorCreateModel,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        remote_ip: Optional[str] = Depends(get_client_host),
        remote_hostname: Optional[str] = Depends(get_client_host_name),
        tracking_cookie: Optional[str] = Depends(get_tapir_tracking_cookie),
        session: Session = Depends(get_db)) -> List[ModeratorModel]:

    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    user_id = body.user_id
    if session.query(TapirUser).filter(TapirUser.user_id == user_id).count() == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    data = body.model_dump()
    mods = []

    for category in body.categories:
        [archive, subject_class] = category.split(".")
        existing = ModeratorModel.base_query(session).filter(
            and_(
                t_arXiv_moderators.c.user_id == int(body.user_id),
                t_arXiv_moderators.c.archive == archive,
                t_arXiv_moderators.c.subject_class == subject_class,
            )
        ).one_or_none()

        if existing:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Moderator already exists.")

        one = data.copy()
        del one['categories']
        one['archive'] = archive
        one['subject_class'] = subject_class

        stmt = insert(t_arXiv_moderators).values(**one)

        try:
            result = session.execute(stmt)
            session.flush()

            # Retrieve the inserted row using a SELECT query

            item = ModeratorModel.base_query(session).filter(
                and_(
                    t_arXiv_moderators.c.user_id == int(body.user_id),
                    t_arXiv_moderators.c.archive == archive,
                    t_arXiv_moderators.c.subject_class == subject_class)).one_or_none()

            if not item:
                raise HTTPException(status_code=500, detail="Failed to fetch inserted record")

            admin_audit(
                session,
                AdminAudit_MakeModerator(
                    current_user.user_id,
                    body.user_id,
                    current_user.tapir_session_id,
                    category=category,
                    remote_ip=remote_ip,
                    remote_hostname=remote_hostname,
                    tracking_cookie=tracking_cookie,
                )
            )

            mods.append(ModeratorModel.model_validate(item))

        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    session.commit()
    await _modapi_clear_user_cache(user_id, request)
    return mods


async def _delete_moderator(request: Request,
                      session: Session,
                      current_user: ArxivUserClaims,
                      user_id: str, archive: str, subject_class: str,
                      remote_ip: str, remote_hostname: str, tracking_cookie: str
    ) -> Response:
    uid = int(user_id)
    result = cast(CursorResult, session.execute(
        t_arXiv_moderators.delete().where(
            and_(
                t_arXiv_moderators.c.user_id == uid,
                t_arXiv_moderators.c.archive == archive,
                t_arXiv_moderators.c.subject_class == subject_class
            )
        )
    ))

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Moderator not found")

    admin_audit(
        session,
        AdminAudit_UnmakeModerator(
            current_user.user_id,
            user_id,
            current_user.tapir_session_id,
            category=f"{archive}.{subject_class}",
            remote_ip=remote_ip,
            remote_hostname=remote_hostname,
            tracking_cookie=tracking_cookie,
        )
    )

    session.commit()
    await _modapi_clear_user_cache(uid, request)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete('/{id:str}', status_code=status.HTTP_204_NO_CONTENT,
               description="""parameter ID is user_id "+" archive "+" subject_class where + is a literal character.
 This is because react-admin's delete row must have a single ID, and I chose to use + as separator."""
               )
async def delete_moderator(
        request: Request,
        id: str,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        remote_ip: Optional[str] = Depends(get_client_host),
        remote_hostname: Optional[str] = Depends(get_client_host_name),
        tracking_cookie: Optional[str] = Depends(get_tapir_tracking_cookie),
        session: Session = Depends(get_db)) -> Response:
    """
    delete_moderator:
    """
    [user_id, archive, subject_class] = id.split("+")

    return await _delete_moderator(request, session, current_user, user_id, archive, subject_class,
                                   remote_ip or "",
                                   remote_hostname or "",
                                   tracking_cookie or "")


@router.delete('/user/{user_id:str}/archive/{archive:str}/subject_class/{subject_class:str}',
               status_code=status.HTTP_204_NO_CONTENT,
               description="Delete moderator operation in a straightforward interface."
               )
async def delete_moderator_2(
        request: Request,
        user_id: str,
        archive: str,
        subject_class: str,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        remote_ip: Optional[str] = Depends(get_client_host),
        remote_hostname: Optional[str] = Depends(get_client_host_name),
        tracking_cookie: Optional[str] = Depends(get_tapir_tracking_cookie),
        session: Session = Depends(get_db)) -> Response:
    return await _delete_moderator(request, session, current_user, user_id, archive, subject_class,
                                   remote_ip or "",
                                   remote_hostname or "",
                                   tracking_cookie or "")

