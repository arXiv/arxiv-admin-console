"""Things used for API implementation"""

from arxiv_bizlogic.gcp_helper import verify_gcp_oidc_token
from fastapi import Request, status as http_status, Depends, HTTPException
import os

# This is used by others. Don't remove
from arxiv_bizlogic.fastapi_helpers import (
    is_any_user, is_admin_user, get_current_user, get_db, get_hostname,
    get_client_host_name, get_client_host, datetime_to_epoch, VERY_OLDE, get_authn_or_none)
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

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


def get_tapir_session(request: Request,
                      current_user: ArxivUserClaims | None = Depends(get_authn_or_none)
                      ) -> TapirSessionData | None:
    if current_user:
        ts_data = TapirSessionData(
            session_id=str(current_user.tapir_session_id or ""),
            user_id=current_user.user_id or "",
            client_ip=current_user.client_ip4v,
            session_created=current_user.issued_at,
            session_exp=current_user.expires_at,
            privilege=str(current_user.classic_capability_code)
        )
        return ts_data

    return request.state.tapir_session


def get_tracking_cookie(request: Request) -> str | None:
    tracking_cookie_key = request.app.extra['TRACKING_COOKIE_NAME']
    return request.cookies.get(tracking_cookie_key)


def gate_admin_user(user: ArxivUserClaims):
    if not user:
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Not logged in")

    if not user.is_admin:
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Not admin")


def is_authenticated(_token: None, current_user: ArxivUserClaims | None) -> bool:
    return current_user is not None

def is_authorized(_token: None, current_user: ArxivUserClaims | None, user_id: str) -> bool:
    return (current_user is not None) and (current_user.is_admin or (str(current_user.user_id) == str(user_id)))


def check_authnz(_token: None, current_user: ArxivUserClaims | None, user_id: str | int):
    """
    Sugar to do both authentication and authorization check
    """
    if not is_authenticated(None, current_user):
        raise HTTPException(status_code=http_status.HTTP_401_UNAUTHORIZED, detail="Not logged in")

    if not is_authorized(None, current_user, str(user_id)):
        raise HTTPException(status_code=http_status.HTTP_403_FORBIDDEN, detail="Unauthorized")

_security_ = HTTPBearer()

async def get_gcp_token_or_none(request: Request,
                                credentials: HTTPAuthorizationCredentials = Depends(_security_)
                                ):
    try:
        return await verify_gcp_oidc_token(request, credentials)
    except HTTPException:
        return None
