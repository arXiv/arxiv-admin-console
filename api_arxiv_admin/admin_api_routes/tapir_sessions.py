"""arXiv paper display routes."""
import re
import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Request
from typing import Optional, List
from arxiv.base import logging
from arxiv.db.models import TapirSession
from pydantic import BaseModel
from sqlalchemy.orm import Session, Query as SAQuery
from sqlalchemy import case

from . import is_admin_user, get_db, datetime_to_epoch, VERY_OLDE

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_admin_user)], prefix="/tapir_sessions")

class TapirSessionModel(BaseModel):
    id: int
    user_id: int
    last_reissue: Optional[datetime.datetime]
    start_time: Optional[datetime.datetime]
    end_time: Optional[datetime.datetime]
    close_session: bool

    class Config:
        orm_mode = True
        from_attributes = True

    @classmethod
    def base_query(cls, db: Session) -> SAQuery:
        return db.query(
            TapirSession.session_id.label("id"),
            TapirSession.user_id,
            case(
                (TapirSession.last_reissue == 0, None),
                else_ = TapirSession.last_reissue
            ).label("last_reissue"),
            case(
                (TapirSession.start_time == 0, None),
                else_= TapirSession.start_time
            ).label("start_time"),
            case(
                (TapirSession.end_time == 0, None),
                else_= TapirSession.end_time
            ).label("end_time"),
            case(
                (TapirSession.end_time == 0, False),
                else_=True
            ).label("close_session"),
        )


@router.get('/')
async def list_tapir_sessions(
        response: Response,
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        user_id: Optional[int] = Query(None, description="User id"),
        id: Optional[List[int]] = Query(None, description="List of user IDs to filter by"),
        preset: Optional[str] = Query(None),
        start_date: Optional[datetime.date] = Query(None, description="Start date for filtering"),
        end_date: Optional[datetime.date] = Query(None, description="End date for filtering"),
        session: Session = Depends(get_db)
    ) -> List[TapirSessionModel]:
    query = TapirSessionModel.base_query(session)

    if id is not None:
        query = query.filter(TapirSession.user_id.in_(id))
    else:
        if _start < 0 or _end < _start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid start or end index")
        if preset is not None or start_date is not None or end_date is not None:
            t0 = datetime.datetime.now(datetime.UTC)
            if preset is not None:
                matched = re.search(r"last_(\d+)_days", preset)
                if matched:
                    t_begin = datetime_to_epoch(None, t0 - datetime.timedelta(days=int(matched.group(1))))
                    t_end = datetime_to_epoch(None, t0)
                    query = query.filter(TapirSession.start_time.between(t_begin, t_end))
                else:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Invalid preset format")
            else:
                if start_date or end_date:
                    t_begin = datetime_to_epoch(start_date, VERY_OLDE)
                    t_end = datetime_to_epoch(end_date, datetime.date.today(), hour=23, minute=59, second=59)
                    query = query.filter(TapirSession.start_time.between(t_begin, t_end))

        if user_id:
            query = query.filter(TapirSession.user_id == user_id)

    order_columns = []
    if _sort:
        keys = _sort.split(",")
        for key in keys:
            if key == "id":
                key = "session_id"
            try:
                order_column = getattr(TapirSession, key)
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
    result = [TapirSessionModel.from_orm(item) for item in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get("/{id:int}")
async def get_tapir_session(
        id:int, session: Session = Depends(get_db)) -> TapirSessionModel:
    """Display a paper."""
    tapir_session = TapirSessionModel.base_query(session).filter(TapirSession.session_id == id).one_or_none()
    if not tapir_session:
        raise HTTPException(status_code=404, detail=f"TapirSession not found for {id}")
    return tapir_session


@router.get("/user/{user_id:int}")
async def get_tapir_session_for_user(
        response: Response,
        user_id:int,
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        session: Session = Depends(get_db)) -> List[TapirSessionModel]:
    """List tapir sessions for a user"""
    return list_tapir_sessions(response, _sort, _order, _start, _end, user_id=user_id, session=session)



@router.put("/{id:int}")
async def close_tapir_session(
        request: Request,
        id:int,
        session: Session = Depends(get_db)) -> TapirSessionModel:
    # This part of logic, I have no clue.
    # I think last_reissue can be null (or 0) so not sure how correct this is.
    #
    # 	function _expire_session() {
	#
	# 	$session_id=$this->session_id;
	#
	# 	if($session_id) {
	# 		$sql="UPDATE tapir_sessions SET end_time=last_reissue+M4_SESSION_COOKIE_REISSUE WHERE session_id=$session_id AND end_time=0;";
	#       $this->_rw_conn->query($sql);
	# 	};
    #
	# 	$this->_clear_session_cookie();
	# }

    tapir_session: TapirSession = session.query(TapirSession).filter(TapirSession.session_id == id).one_or_none()
    if not tapir_session:
        raise HTTPException(status_code=404, detail=f"TapirSession not found for {id}")
    body = await request.json()
    if body.get("close_session") and not tapir_session.end_time:
        cookie_reissue = 30
        try:
            cookie_reissue = int(request.app.extra.get("TAPIR_SESSION_COOKIE_REISSUE", "30"))
        except ValueError:
            pass
        if tapir_session.last_reissue:
            tapir_session.end_time = tapir_session.last_reissue + cookie_reissue
        elif tapir_session.start_time:
            tapir_session.end_time = tapir_session.start_time + cookie_reissue
        else:
            tapir_session.end_time = datetime.datetime.now().timestamp() + cookie_reissue
        session.commit()
        session.refresh(tapir_session)

    return TapirSessionModel.from_orm(TapirSessionModel.base_query(session).filter(TapirSession.session_id == id).one_or_none())

