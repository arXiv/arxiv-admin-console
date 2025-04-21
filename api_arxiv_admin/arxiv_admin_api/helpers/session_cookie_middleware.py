import os
import logging
from datetime import datetime

from typing import Any, Callable, Optional

import httpcore
import httpx
from cachetools import TTLCache
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.applications import ASGIApp

import jwt
import jwcrypto
import jwcrypto.jwt

from arxiv.auth.user_claims import ArxivUserClaims
from arxiv.auth.legacy.cookies import unpack as legacy_cookie_unpack

from arxiv_admin_api.helpers.user_session import UserSession, TapirSessionData

logger = logging.getLogger(__name__)

refresh_timeout = int(os.environ.get('KC_TIMEOUT', '2'))
refresh_retry = int(os.environ.get('KC_RETRY', '5'))

async def refresh_token(aaa_url: str,
                        cookies: dict,
                        session_cookie: str,
                        classic_cookie: str) -> Optional[dict]:
    for iter in range(refresh_retry):
        try:
            async with httpx.AsyncClient() as client:
                refresh_response = await client.post(
                    aaa_url,
                    json={
                        "session": session_cookie,
                        "classic": classic_cookie,
                    },
                    cookies=cookies,
                    timeout=refresh_timeout,
                )

            if refresh_response.status_code == 200:
                # Extract the new token from the response
                refreshed_tokens = refresh_response.json()
                return refreshed_tokens
            elif refresh_response.status_code in [401, 422]:
                logger.info("post to %s: bad/expired refresh token", aaa_url)
                # return {"session": None, "classic": None, "max_age": 0, "secure": False, "samesite": ""}
                return None
            elif refresh_response.status_code >= 500 and refresh_response.status_code <= 599:
                # This needs a retry
                logger.warning("post to %s status %s. iter=%d", aaa_url, refresh_response.status_code,
                               iter)
                continue
            else:
                logger.warning("calling %s failed. status = %s: %s",
                               aaa_url,
                               refresh_response.status_code,
                               str(refresh_response.content))
                break

        except httpcore.ConnectTimeout:
            logger.warning("post to %s timed out. iter=%d", aaa_url, iter)
            continue

        except Exception as exc:
            logger.warning("calling %s failed.", aaa_url, exc_info=exc)
            break

    return None

# Define custom middleware to add a cookie to the response
class SessionCookieMiddleware(BaseHTTPMiddleware):

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)


    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        session_cookie_name = request.app.extra['AUTH_SESSION_COOKIE_NAME']
        classic_cookie_name = request.app.extra['CLASSIC_COOKIE_NAME']
        cookies = request.cookies
        session_cookie = cookies.get(session_cookie_name)
        legacy_cookie = cookies.get(classic_cookie_name)

        user_session: UserSession = request.app.extra['user_session']
        secret = request.app.extra['JWT_SECRET']
        if not secret:
            logger.error("The app is misconfigured or no JWT secret has been set")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        refreshed_tokens = None
        claims = None

        if legacy_cookie is not None:
            try:
                tprs = legacy_cookie_unpack(legacy_cookie)
                tpr_session = TapirSessionData(
                    session_id=tprs[0],
                    user_id=tprs[1],
                    client_ip=tprs[2],
                    session_created=tprs[3],
                    session_exp=tprs[4],
                    privilege=tprs[5]
                )
                request.state.tapir_session = tpr_session
            except Exception as exc:
                request.state.tapir_session = None
                pass
        else:
            request.state.tapir_session = None

        if session_cookie is not None:
            tokens, jwt_payload = ArxivUserClaims.unpack_token(session_cookie)
            user_id = tokens['sub']

            while claims is None and session_cookie is not None:
                try:
                    await user_session.lock(user_id)

                    # cached cookies
                    user_cookies = user_session.get_user_cookies(user_id)
                    # cache exists
                    if user_cookies and user_cookies.get('session') and user_cookies.get('session') != session_cookie:
                        # I already have the valid cookie in the cache. So use it
                        refreshed_tokens = user_cookies
                        session_cookie = user_cookies['session']
                        if session_cookie:
                            tokens, jwt_payload = ArxivUserClaims.unpack_token(session_cookie)

                    try:
                        claims = ArxivUserClaims.decode_jwt_payload(tokens, jwt_payload, secret)
                        break

                    except jwcrypto.jwt.JWTExpired:
                        pass

                    except jwt.ExpiredSignatureError:
                        pass

                    except jwcrypto.jwt.JWTInvalidClaimFormat:
                        logger.warning(f"Chowed cookie '{session_cookie}'")
                        from arxiv_admin_api import BadCookie
                        raise BadCookie()

                    except jwt.DecodeError:
                        logger.warning(f"Chowed cookie '{session_cookie}'")
                        from arxiv_admin_api import BadCookie
                        raise BadCookie()

                    except Exception as exc:
                        logger.warning(f"token {session_cookie} is wrong?", exc_info=exc)
                        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

                    refreshed_tokens = await refresh_token(request.app.extra['AAA_TOKEN_REFRESH_URL'],
                                                           cookies, session_cookie, legacy_cookie)
                    user_session.set_user_cookies(user_id, refreshed_tokens)
                    if refreshed_tokens is None:
                        break
                except Exception as exc:
                    logger.debug("foo!", exc_info=exc)
                    raise

                finally:
                    user_session.unlock(user_id)

        request.state.user_claims = claims
        response = await call_next(request)

        if refreshed_tokens:
            max_age = refreshed_tokens.get("max_age")
            domain = refreshed_tokens.get("domain")
            secure = refreshed_tokens.get("secure")
            samesite = refreshed_tokens.get("samesite")
            new_session_cookie = refreshed_tokens.get("session")
            new_classic_cookie = refreshed_tokens.get("classic")

            response.set_cookie(session_cookie_name, new_session_cookie,
                                max_age=max_age, domain=domain, secure=secure, samesite=samesite)

            if new_classic_cookie:
                response.set_cookie(classic_cookie_name, new_classic_cookie,
                                    max_age=max_age, domain=domain, secure=secure, samesite=samesite)
            pass
        return response
