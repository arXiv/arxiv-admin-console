import logging
import os
import time
from datetime import timezone, datetime

import httpx
from typing import Callable, Optional, Tuple, Any

from fastapi import FastAPI, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from asgi_logger import AccessLoggerMiddleware

import sqlalchemy
import sqlalchemy.event
from sqlalchemy.engine import ExecutionContext
from asgi_correlation_id import CorrelationIdMiddleware
from asgi_correlation_id.middleware import is_valid_uuid4
from uuid import uuid4

from arxiv.base.globals import get_application_config
from arxiv.auth.user_claims import ArxivUserClaims

from arxiv_admin_api import AccessTokenExpired, LoginRequired, BadCookie, get_session_cookie
# from arxiv_admin_api.authentication import router as auth_router
from arxiv_admin_api.admin_logs import router as admin_log_router
from arxiv_admin_api.categories import router as categories_router, archive_group_router
from arxiv_admin_api.email_template import router as email_template_router, notification_pubsub_router
from arxiv_admin_api.endorsement_requests import router as endorsement_request_router, endorsers_router
from arxiv_admin_api.endorsement_requests_audit import router as endorsement_request_audit_router
from arxiv_admin_api.endorsements import router as endorsement_router
from arxiv_admin_api.demographic import router as demographic_router
from arxiv_admin_api.documents import router as document_router
from arxiv_admin_api.metadata import router as metadata_router
from arxiv_admin_api.moderators import router as moderator_router
from arxiv_admin_api.ownership_requests import router as ownership_request_router
from arxiv_admin_api.ownership_requests_audit import router as ownership_request_audit_router
from arxiv_admin_api.paper_owners import router as paper_owner_router, paper_pw_router
from arxiv_admin_api.submissions import router as submission_router, meta_router as submission_meta_router
from arxiv_admin_api.submission_categories import router as submission_categories_router
from arxiv_admin_api.user import router as user_router, users_by_username_router
from arxiv_admin_api.tapir_sessions import router as tapir_session_router
from arxiv_admin_api.member_institutions import router as member_institution_router, institution_ip_router
from arxiv_admin_api.countries import router as countries_router
from arxiv_admin_api.tapir_admin_audit import router as tapir_admin_audit_router
from arxiv_admin_api.taxonomy import router as taxonomy_router
from arxiv_admin_api.orcid_ids import router as orcid_router
from arxiv_admin_api.author_ids import router as author_id_router
from arxiv_admin_api.show_email_requests import router as show_email_requests_router
from arxiv_admin_api.licenses import router as licenses_router
from arxiv_admin_api.email_patterns import router as email_patterns_router
from arxiv_admin_api.endorsement_domains import router as endorsement_domains_router

from arxiv_admin_api.frontend import router as frontend_router
from arxiv_admin_api.helpers.session_cookie_middleware import SessionCookieMiddleware
from arxiv_admin_api.helpers.user_session import UserSession

from arxiv_admin_api.public_users import router as public_users_router

from arxiv.base.logging import getLogger

from arxiv.config import Settings

from app_logging import setup_logger

# API root path (excluding the host)
ADMIN_API_ROOT_PATH = os.environ.get('ADMIN_API_ROOT_PATH', '/admin-api')

# Admin app URL
#
ADMIN_APP_URL = os.environ.get('ADMIN_APP_URL', 'http://localhost.arxiv.org:5100/admin-console')
#
DB_URI = os.environ.get('CLASSIC_DB_URI')
#
#
#
AAA_LOGIN_REDIRECT_URL = os.environ.get("AAA_LOGIN_REDIRECT_URL", "http://localhost.arxiv.org:5100/aaa/login")
# When it got the expired, ask the oauth server to refresh the token
# This is still WIP.
AAA_TOKEN_REFRESH_URL = os.environ.get("AAA_TOKEN_REFRESH_URL", "http://localhost.arxiv.org:5100/aaa/refresh")
#
LOGOUT_REDIRECT_URL = os.environ.get("LOGOUT_REDIRECT_URL", ADMIN_APP_URL)
#
JWT_SECRET = os.environ.get("JWT_SECRET")
AUTH_SESSION_COOKIE_NAME = os.environ.get("AUTH_SESSION_COOKIE_NAME", "arxiv_oidc_session")
CLASSIC_COOKIE_NAME = os.environ.get("CLASSIC_COOKIE_NAME", "tapir_session")
TRACKING_COOKIE_NAME = os.environ.get("TRACKING_COOKIE_NAME", "tapir_tracking")

SQLALCHMEY_MAPPING = {
    'pool_size': 8,
    'max_overflow': 8,
    'pool_timeout': 30,
    'pool_recycle': 900
}

# Auth is now handled by auth service
# No need for keycloak URL, etc.

origins = [
    "http://localhost",
    "http://localhost:5000",
    "http://localhost:5000/",
    "http://localhost:5000/admin-console",
    "http://localhost:5000/admin-console/",
    "http://localhost:5222",
    "http://localhost:5222/",
    "https://arxiv.org",
    "https://arxiv.org/",
    "https://dev.arxiv.org",
    "https://dev.arxiv.org/",
    "https://dev3.arxiv.org",
    "https://dev3.arxiv.org/",
    "https://dev9.arxiv.org",
    "https://dev9.arxiv.org/",
    "https://web40.arxiv.org",
    "https://web40.arxiv.org/",
    "https://web41.arxiv.org",
    "https://web41.arxiv.org/",
]

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Log request details
        body = await request.body()
        print(f"Request: {request.method} {request.url}")
        print(f"Request Headers: {request.headers}")
        #print(f"Request Body: {body.decode('utf-8')}")

        # Call the next middleware or endpoint
        response = await call_next(request)

        # Capture response body properly
        response_body = []
        async for chunk in response.body_iterator:
            response_body.append(chunk)
        
        # Create a proper async iterator
        async def generate_body():
            for chunk in response_body:
                yield chunk
        
        # Replace the body iterator with our async generator
        response.body_iterator = generate_body()
        
        # Log response details
        response_body_str = b''.join(response_body).decode('utf-8')
        print(f"Response: {response.status_code}")
        #print(f"Response Headers: {response.headers}")
        #print(f"Response Body: {response_body_str}")

        return response



def create_app(*args, **kwargs) -> FastAPI:
    setup_logger()

    settings = Settings (
        CLASSIC_DB_URI = DB_URI,
        LATEXML_DB_URI = None
    )
    from arxiv_bizlogic.database import Database
    database = Database(settings)
    database.set_to_global()

    # from arxiv.db import init as arxiv_db_init
    # arxiv_db_init(settings)
    # from arxiv.db import _classic_engine

    @sqlalchemy.event.listens_for(database.engine, "before_cursor_execute")
    def before_execute(conn: ExecutionContext, _cursor, _str_statement: str, _effective_parameters: Tuple[Any],
                       _context, _context_executemany: bool):
        conn.connection.info["query_start_time"] = time.time()

    @sqlalchemy.event.listens_for(database.engine, "after_cursor_execute")
    def after_execute(conn: ExecutionContext, _cursor, str_statement: str, effective_parameters: Tuple[Any],
                      _context, _context_executemany: bool):
        total_time = time.time() - conn.connection.info["query_start_time"]
        logging.info(f"Query Time: {total_time:.4f} seconds: {str_statement} with {effective_parameters!r}")

    jwt_secret = get_application_config().get('JWT_SECRET', settings.SECRET_KEY)

    for key in ['CLASSIC_SESSION_HASH', 'SESSION_DURATION', 'CLASSIC_COOKIE_NAME']:
        if get_application_config().get(key) is None:
            logging.warning(f"{key} is not set, and will fail Tapir Cookie operations")
            # Fill in a default. Okay for test and local dev.
            os.environ[key] = {
                "CLASSIC_SESSION_HASH": "classic-secret",
                "SESSION_DURATION": "36000",
                "CLASSIC_COOKIE_NAME": "tapir_session"
            }.get(key)

    pwc_secret = get_application_config().get('PWC_SECRET', "not-very-secret")
    pwc_arxiv_user_secret = get_application_config().get('PWC_ARXIV_USER_SECRET', "not-very-secret")

    app = FastAPI(
        root_path=ADMIN_API_ROOT_PATH,
        arxiv_db_engine=database.engine,
        arxiv_settings=settings,
        JWT_SECRET=jwt_secret,
        LOGIN_REDIRECT_URL=AAA_LOGIN_REDIRECT_URL,
        LOGOUT_REDIRECT_URL=LOGOUT_REDIRECT_URL,
        AUTH_SESSION_COOKIE_NAME=AUTH_SESSION_COOKIE_NAME,
        CLASSIC_COOKIE_NAME=CLASSIC_COOKIE_NAME,
        AAA_TOKEN_REFRESH_URL=AAA_TOKEN_REFRESH_URL,
        TRACKING_COOKIE_NAME=TRACKING_COOKIE_NAME,
        DATABASE=database,
        user_session=UserSession(),
        PWC_SECRET=pwc_secret,
        PWC_ARXIV_USER_SECRET=pwc_arxiv_user_secret,
        SMTP_URL = os.environ.get('SMTP_URL', "ssmtp://smtp.gmail.com:465?user=smtp-relay@arxiv.org&password=pwd"),
        API_SHARED_SECRET = os.environ.get('API_SHARED_SECRET', "not-very-secret"),
    )

    if ADMIN_APP_URL not in origins:
        origins.append(ADMIN_APP_URL)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )

    app.add_middleware(
        CorrelationIdMiddleware,  # type: ignore
        header_name='X-Request-ID',
        update_request_header=True,
        generator=lambda: uuid4().hex,
        validator=is_valid_uuid4,
        transformer=lambda a: a
        )

    app.add_middleware(AccessLoggerMiddleware) # type: ignore

    app.add_middleware(LogMiddleware)
    # app.add_middleware(SessionMiddleware, secret_key="SECRET_KEY")
    app.add_middleware(SessionCookieMiddleware)

    # app.include_router(auth_router)
    app.include_router(admin_log_router, prefix="/v1")
    app.include_router(categories_router, prefix="/v1")
    app.include_router(archive_group_router, prefix="/v1")
    app.include_router(demographic_router, prefix="/v1")
    app.include_router(user_router, prefix="/v1")
    app.include_router(users_by_username_router, prefix="/v1")
    app.include_router(email_template_router, prefix="/v1")
    app.include_router(notification_pubsub_router, prefix="/v1")
    app.include_router(endorsement_router, prefix="/v1")
    app.include_router(endorsement_request_router, prefix="/v1")
    app.include_router(endorsers_router, prefix="/v1")
    app.include_router(endorsement_request_audit_router, prefix="/v1")
    app.include_router(paper_owner_router, prefix="/v1")
    app.include_router(paper_pw_router, prefix="/v1")
    app.include_router(ownership_request_router, prefix="/v1")
    app.include_router(ownership_request_audit_router, prefix="/v1")
    app.include_router(moderator_router, prefix="/v1")
    app.include_router(document_router, prefix="/v1")
    app.include_router(metadata_router, prefix="/v1")
    app.include_router(submission_router, prefix="/v1")
    app.include_router(submission_meta_router, prefix="/v1")
    app.include_router(member_institution_router, prefix="/v1")
    app.include_router(institution_ip_router, prefix="/v1")
    app.include_router(frontend_router)
    app.include_router(tapir_session_router, prefix="/v1")
    app.include_router(submission_categories_router, prefix="/v1")
    app.include_router(countries_router, prefix="/v1")
    app.include_router(public_users_router, prefix="/v1")
    app.include_router(tapir_admin_audit_router, prefix="/v1")
    app.include_router(taxonomy_router, prefix="/v1")
    app.include_router(orcid_router, prefix="/v1")
    app.include_router(author_id_router, prefix="/v1")
    app.include_router(show_email_requests_router, prefix="/v1")
    app.include_router(licenses_router, prefix="/v1")
    app.include_router(email_patterns_router, prefix="/v1")
    app.include_router(endorsement_domains_router, prefix="/v1")

    @app.middleware("http")
    async def apply_response_headers(request: Request, call_next: Callable) -> Response:
        """Apply response headers to all responses.
           Prevent UI redress attacks.
        """
        response: Response = await call_next(request)
        response.headers['Content-Security-Policy'] = "frame-ancestors 'none'"
        response.headers['X-Frame-Options'] = 'DENY'
        return response

    @app.get("/v1/ping")
    async def ping(request: Request,
                   response: Response,
                   token: Optional[str] = Depends(get_session_cookie)):
        logger = getLogger(__name__)
        logger.debug(f"Ping: {token}")
        response.status_code = status.HTTP_200_OK
        try:
            secret = request.app.extra['JWT_SECRET']
            if secret and token:
                tokens, jwt_payload = ArxivUserClaims.unpack_token(token)
                expires_at = datetime.strptime(tokens['expires_at'], '%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
                remain = expires_at - datetime.now(timezone.utc)
                need_token_refresh = remain.total_seconds() < 60
                if need_token_refresh and 'refresh' in tokens:
                    logger.debug(f"Ping: refresh {token}")
                    cookies = request.cookies
                    AAA_TOKEN_REFRESH_URL = request.app.extra['AAA_TOKEN_REFRESH_URL']
                    session_cookie_name = request.app.extra['AUTH_SESSION_COOKIE_NAME']
                    classic_cookie_name = request.app.extra['CLASSIC_COOKIE_NAME']
                    async with httpx.AsyncClient() as client:
                        refresh_response = await client.post(
                            AAA_TOKEN_REFRESH_URL,
                            json={
                                "session": token,
                                "classic": cookies.get(classic_cookie_name),
                            },
                            cookies=cookies)

                        if refresh_response.status_code == 200:
                            refreshed_tokens = refresh_response.json()
                            # Extract the new token from the response
                            new_session_cookie = refreshed_tokens.get("session")
                            new_classic_cookie = refreshed_tokens.get("classic")
                            max_age = refreshed_tokens.get("max_age")
                            domain = refreshed_tokens.get("domain")
                            secure = refreshed_tokens.get("secure")
                            samesite = refreshed_tokens.get("samesite")
                            response.set_cookie(session_cookie_name, new_session_cookie,
                                                max_age=max_age, domain=domain, secure=secure, samesite=samesite)
                            if new_classic_cookie:
                                response.set_cookie(classic_cookie_name, new_classic_cookie,
                                                    max_age=max_age, domain=domain, secure=secure, samesite=samesite)
                        else:
                            logger.warning("calling /fefresh failed. status = %s", refresh_response.status_code)
                            pass
                        pass
                    pass
                else:
                    logger.debug("No refresh token")
                    pass
                pass
            else:
                logger.debug("No token")
                pass
            pass

        except Exception as _exc:
            logger.debug("ping", exc_info=True)
            pass

        return response

    @app.get("/")
    async def root(_request: Request):
        return RedirectResponse("/frontend")

    @app.exception_handler(AccessTokenExpired)
    async def user_not_authenticated_exception_handler(request: Request,
                                                       _exc: AccessTokenExpired):
        logger = logging.getLogger(__name__)
        original_url = str(request.url)
        logger.info('Handling access token expired %s', original_url)
        cookie_name = request.app.extra['AUTH_SESSION_COOKIE_NAME']
        classic_cookie_name = request.app.extra['CLASSIC_COOKIE_NAME']

        cookies = request.cookies
        refresh_payload = {
            "session": cookies.get(cookie_name),
            "classic": cookies.get(classic_cookie_name),
        },
        try:
            async with httpx.AsyncClient() as client:
                refresh_response = await client.post(AAA_TOKEN_REFRESH_URL, json=refresh_payload, cookies=cookies)

            if refresh_response.status_code != 200:
                logger.info('Token refresh returned not OK %s %s',  refresh_response.status_code,
                            original_url, extra=refresh_payload)
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"message": "Failed to refresh access token"}
                )
            # Extract the new token from the response
            refreshed_tokens = refresh_response.json()
            new_session_cookie = refreshed_tokens.get("session")
            new_classic_cookie = refreshed_tokens.get("classic")
            max_age = refreshed_tokens.get("max_age")
            domain = refreshed_tokens.get("domain")
            secure = refreshed_tokens.get("secure")
            samesite = refreshed_tokens.get("samesite")
            # Step 3: Redirect back to the original URL and set the new cookie
            response = RedirectResponse(url=original_url, status_code=status.HTTP_302_FOUND)
            response.set_cookie(cookie_name, new_session_cookie,
                                max_age=max_age, domain=domain, secure=secure, samesite=samesite)
            response.set_cookie(classic_cookie_name, new_classic_cookie,
                                max_age=max_age, domain=domain, secure=secure, samesite=samesite)
            logger.debug('Token refresh success')
            return response

        except Exception as _exc:
            logger.warning("Failed to refresh access token: %s", _exc)
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"message": "Failed to refresh access token"}
            )

    @app.exception_handler(LoginRequired)
    async def login_required_exception_handler(request: Request,
                                               _exc: LoginRequired):
        logger = logging.getLogger(__name__)
        original_url = str(request.url)
        login_url = f"{AAA_LOGIN_REDIRECT_URL}?next_page={original_url}"
        logger.info('Login required %s -> %s ', original_url, login_url)
        #return RedirectResponse(url=login_url, status_code=status.HTTP_302_FOUND)
        return Response(status_code=status.HTTP_401_UNAUTHORIZED)

    @app.exception_handler(BadCookie)
    async def bad_cookie_exception_handler(request: Request,
                                           _exc: BadCookie):
        logger = logging.getLogger(__name__)
        original_url = str(request.url)
        login_url = f"{AAA_LOGIN_REDIRECT_URL}?next_page={original_url}"
        logger.info('Bad cookie %s -> %s ', original_url, login_url)
        return RedirectResponse(url=login_url, status_code=status.HTTP_302_FOUND)

    return app