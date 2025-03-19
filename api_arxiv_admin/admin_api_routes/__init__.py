"""Things used for API implementation"""
from http.client import HTTPException
from fastapi import Request, HTTPException, status as http_status
import os

from arxiv_bizlogic.fastapi_helpers import (
    is_any_user, is_admin_user, get_current_user, get_db, get_hostname,
    get_client_host_name, get_client_host, datetime_to_epoch, VERY_OLDE)
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


async def get_session_cookie(request: Request) -> str | None:
    session_cookie_key = request.app.extra['AUTH_SESSION_COOKIE_NAME']
    return request.cookies.get(session_cookie_key)


def get_tapir_session(request: Request) -> TapirSessionData | None:
    return request.state.tapir_session


def get_tracking_cookie(request: Request) -> str | None:
    tracking_cookie_key = request.app.extra['TRACKING_COOKIE_NAME']
    return request.cookies.get(tracking_cookie_key)


def gate_admin_user(user: ArxivUserClaims):
    if not user:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Not logged in")

    if not user.is_admin:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not admin")

