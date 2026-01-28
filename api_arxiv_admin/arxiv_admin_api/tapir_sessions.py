"""arXiv paper display routes."""
import re
import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response #, Request
from typing import Optional, List
from arxiv.base import logging
from arxiv.db.models import TapirSession, TapirSessionsAudit
from pydantic import BaseModel
from sqlalchemy.orm import Session, Query as SAQuery
from sqlalchemy import case #, text

from . import is_admin_user, get_db, datetime_to_epoch, VERY_OLDE

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_admin_user)], prefix="/tapir_sessions")

class TapirSessionModel(BaseModel):
    id: Optional[int] = None
    user_id: int
    last_reissue: Optional[datetime.datetime] = None
    start_time: Optional[datetime.datetime] = None
    end_time: Optional[datetime.datetime] = None
    close_session: bool
    remote_ip: Optional[str] = None
    remote_host: Optional[str] = None

    class Config:
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
            ).label("close_session")
        )

    @classmethod
    def to_model(cls, session: Session, data) -> 'TapirSessionModel':
        data0 = TapirSessionModel.model_validate(data).model_dump()
        supplement = session.query(TapirSessionsAudit.ip_addr, TapirSessionsAudit.remote_host).filter(TapirSessionsAudit.session_id == data0['id']).all()
        if len(supplement) > 0:
            data0['remote_ip'] = supplement[0][0]
            data0['remote_host'] = supplement[0][1]
        return TapirSessionModel.model_validate(data0)


@router.get('/')
async def list_tapir_sessions(
        response: Response,
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        user_id: Optional[int] = Query(None, description="User id"),
        is_open: Optional[bool] = Query(None, description="Open sessions"),
        id: Optional[List[int]] = Query(None, description="List of user IDs to filter by"),
        preset: Optional[str] = Query(None),
        start_date: Optional[datetime.date] = Query(None, description="Start date for filtering"),
        end_date: Optional[datetime.date] = Query(None, description="End date for filtering"),
        remote_ip: Optional[str] = Query(None, description="Remode IP address"),
        session: Session = Depends(get_db)
    ) -> List[TapirSessionModel]:
    """List tapir sessions."""
    return await _list_tapir_sessions(session, response, _sort, _order, _start, _end, user_id, is_open, id, preset, start_date, end_date, remote_ip)


async def _list_tapir_sessions(
            session: Session,
            response: Response,
            _sort: Optional[str] = None,
            _order: Optional[str] = None,
            _start: Optional[int] = None,
            _end: Optional[int] = None,
            user_id: Optional[int] = None,
            is_open: Optional[bool] = None,
            id: Optional[List[int]] = None,
            preset: Optional[str] = None,
            start_date: Optional[datetime.date] = None,
            end_date: Optional[datetime.date] = None,
            remote_ip: Optional[str] = None,
    ) -> List[TapirSessionModel]:

    audit_joined = False
    all_rows = True
    query = TapirSessionModel.base_query(session)
    start: int = _start if _start is not None else 0
    end: int = _end if _end is not None else 100

    if id is not None:
        query = query.filter(TapirSession.session_id.in_(id))
    else:
        if start < 0 or end < start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid start or end index")
        if preset is not None or start_date is not None or end_date is not None:
            all_rows = False
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
            all_rows = False
            query = query.filter(TapirSession.user_id == user_id)

        if is_open is not None:
            all_rows = False
            if is_open:
                query = query.filter(TapirSession.end_time == 0)
            else:
                query = query.filter(TapirSession.end_time != 0)

        if remote_ip is not None:
            all_rows = False
            audit_joined = True
            # Convert integer IP address to IPv4 dotted notation
            if "." not in remote_ip and remote_ip.isdigit():
                ip_int = int(remote_ip)
                # Convert 32-bit integer to 4 octets: a.b.c.d
                remote_ip = f"{(ip_int >> 24) & 0xFF}.{(ip_int >> 16) & 0xFF}.{(ip_int >> 8) & 0xFF}.{ip_int & 0xFF}"
            query = query.join(TapirSessionsAudit, TapirSessionsAudit.session_id == TapirSession.session_id).filter(TapirSessionsAudit.ip_addr.startswith(remote_ip))

    order_columns = []
    if _sort:
        keys = _sort.split(",")
        for key in keys:
            if key == "remote_ip":
                if not audit_joined:
                    query = query.join(TapirSessionsAudit,
                                       TapirSessionsAudit.session_id == TapirSession.session_id)
                    audit_joined = True
                    pass
                order_column = getattr(TapirSessionsAudit, key)
                order_columns.append(order_column)
                continue

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

    if all_rows:
        count = session.query(TapirSession.session_id).count()
    else:
        count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [TapirSessionModel.to_model(session, item) for item in query.offset(start).limit(end - start).all()]

    return result


@router.get("/{id:int}")
async def get_tapir_session(
        id:int, session: Session = Depends(get_db)) -> TapirSessionModel:
    """Display a paper."""
    tapir_session = TapirSessionModel.base_query(session).filter(TapirSession.session_id == id).one_or_none()
    if not tapir_session:
        raise HTTPException(status_code=404, detail=f"TapirSession not found for {id}")
    return TapirSessionModel.to_model(session, tapir_session)


@router.get("/user/{user_id:int}")
async def get_tapir_session_for_user(
        response: Response,
        user_id:int,
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        session: Session = Depends(get_db)) -> List[TapirSessionModel]:
    """List tapir sessions for a user"""
    return await _list_tapir_sessions(session, response, _sort, _order, _start, _end, user_id=user_id)


class TapirSessionUpdateModel(BaseModel):
    close_session: bool

@router.put("/{id:int}")
async def update_tapir_session(
        id:int,
        response: Response,
        body: TapirSessionModel | TapirSessionUpdateModel,
        session: Session = Depends(get_db)) -> TapirSessionModel:
    # This is part of logic, I have no clue.
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

    tapir_session: TapirSession | None = session.query(TapirSession).filter(TapirSession.session_id == id).one_or_none()
    if not tapir_session:
        raise HTTPException(status_code=404, detail=f"TapirSession not found for {id}")
    if body.close_session:
        if tapir_session.end_time == 0:
            tapir_session.end_time = datetime_to_epoch(None, datetime.datetime.now(datetime.UTC))
            session.commit()
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"TapirSession already closed for {id}")

    return TapirSessionModel.to_model(session, TapirSessionModel.base_query(session).filter(TapirSession.session_id == id).one_or_none())
