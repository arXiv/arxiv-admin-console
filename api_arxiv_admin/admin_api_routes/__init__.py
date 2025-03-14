"""Contains route information."""
import datetime
import time
from http.client import HTTPException
from logging import getLogger

from fastapi import Request, HTTPException, status
import os

from .database import Database
from .helpers.session_cookie_middleware import TapirSessionData
from .models import *
from arxiv.auth.user_claims import ArxivUserClaims
# from arxiv.auth.openid.oidc_idp import ArxivOidcIdpClient
from .helpers.get_hostname import get_hostname

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"

class AccessTokenExpired(Exception):
    pass


class BadCookie(Exception):
    pass

class LoginRequired(Exception):
    pass


async def is_admin_user(request: Request) -> bool:
    # temporary - use user claims in base

    user = await get_current_user(request)
    if user:
        if user.is_admin:
            return True
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not an admin")
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthenticated")


async def is_any_user(request: Request) -> bool:
    user = await get_current_user(request)
    if user:
        return True
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthenticated")


async def get_session_cookie(request: Request) -> str | None:
    session_cookie_key = request.app.extra['AUTH_SESSION_COOKIE_NAME']
    return request.cookies.get(session_cookie_key)


async def get_current_user(request: Request) -> ArxivUserClaims | None:
    logger = getLogger(__name__)
    return request.state.user_claims


def get_tapir_session(request: Request) -> TapirSessionData | None:
    return request.state.tapir_session


def get_tracking_cookie(request: Request) -> str | None:
    tracking_cookie_key = request.app.extra['TRACKING_COOKIE_NAME']
    return request.cookies.get(tracking_cookie_key)


def get_client_host(request: Request) -> Optional[str]:
    host = request.headers.get('x-real-ip')
    if not host:
        host = request.client.host
    return host


def datetime_to_epoch(timestamp: datetime.datetime | datetime.date | None,
                      default: datetime.date | datetime.datetime,
                      hour=0, minute=0, second=0) -> int:
    if timestamp is None:
        timestamp = default
    if isinstance(timestamp, datetime.date) and not isinstance(timestamp, datetime.datetime):
        # Convert datetime.date to datetime.datetime at midnight
        timestamp = datetime.datetime.combine(timestamp, datetime.time(hour, minute, second))
    # Use time.mktime() to convert datetime.datetime to epoch time
    return int(time.mktime(timestamp.timetuple()))

VERY_OLDE = datetime.datetime(1981, 1, 1)


def get_client_host(request: Request) -> Optional[str]:
    host = request.headers.get('x-real-ip')
    if not host:
        host = request.client.host
    return host


async def get_client_host_name(request: Request) -> Optional[str]:
    return await get_hostname(get_client_host(request))


def get_db():
    db = Database.get_from_global()
    yield from db.get_session()


def gate_admin_user(user: ArxivUserClaims):
    if not user:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Not logged in")

    if not user.is_admin:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not admin")

