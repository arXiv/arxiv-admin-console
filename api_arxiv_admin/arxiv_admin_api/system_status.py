"""admin-api system status"""
from typing import Optional, List

import httpx
from arxiv_bizlogic.fastapi_helpers import COOKIE_ENV_NAMES, get_db
from fastapi import APIRouter, status, Request, HTTPException, Depends

from arxiv.base import logging
from arxiv.db.models import Category
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

from arxiv_admin_api.apis.modapi.modapi_client import (
    SharedNavSection,
    AdminApi,
    ApiClient,
    Configuration
)

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/system", tags=["System"])


@router.get('/')
async def report_ping(
    ) -> JSONResponse:
    """Report system status."""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "ok"}
    )

@router.get('/database_status')
async def report_dtabase_status(
        session: Session = Depends(get_db)
    ) -> JSONResponse:
    """Report connection status."""

    try:
        _category_count = session.query(Category).count()
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ok"}
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database connection error: " + str(e)
        )


@router.get('/cookie_names')
async def report_cookie_names(
        request: Request,
    ) -> JSONResponse:
    """Report system status."""

    return JSONResponse(content={
        "session": request.app.extra[COOKIE_ENV_NAMES.auth_session_cookie_env],
        "classic": request.app.extra[COOKIE_ENV_NAMES.classic_cookie_env],
        "keycloak_access": request.app.extra[COOKIE_ENV_NAMES.keycloak_access_token_env],
        "keycloak_refresh": request.app.extra[COOKIE_ENV_NAMES.keycloak_refresh_token_env],
        "ng": request.app.extra[COOKIE_ENV_NAMES.ng_cookie_env],
    })

SHARED_NAV_HEADER_URL: Optional[List[SharedNavSection]] = None

@router.get('/navigation_urls')
async def get_navigation_urls(
        request: Request,
    ) -> List[SharedNavSection]:
    """
    prod:      modapi.arxiv.org/admin/shared_nav_header
    dev: services.dev.arxiv.org/admin/shared_nav_header
    """
    global SHARED_NAV_HEADER_URL
    if SHARED_NAV_HEADER_URL is None:
        # Get the modapi URL from app config
        modapi_url = request.app.extra["MODAPI_URL"]

        # Configure the API client
        configuration = Configuration(host=modapi_url)

        # Get all cookies from the request and pass them along
        cookies = request.cookies

        # Build Cookie header from all cookies
        cookie_header = '; '.join([f"{k}={v}" for k, v in cookies.items()])
        headers = {'Cookie': cookie_header }

        bearer_token = request.headers.get("Authorization")
        if bearer_token is None:
            ng_token = cookies.get(request.app.extra[COOKIE_ENV_NAMES.ng_cookie_env])
            if ng_token:
                bearer_token = "Bearer " + ng_token
                headers['Authorization'] = bearer_token

        # Call the modapi endpoint with the API client
        with ApiClient(configuration) as api_client:
            api_instance = AdminApi(api_client)
            try:
                SHARED_NAV_HEADER_URL = api_instance.status_admin_shared_nav_header_get(
                    _headers=headers
                )
            except Exception as exc:
                logger.error("Failed to fetch navigation URLs from modapi", exc_info=exc)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="shared_nav_header endpoint is not available"
                )

    return SHARED_NAV_HEADER_URL


@router.get('/navigations_url')
async def get_navigations_url(
        request: Request,
    ) -> str:
    """
    prod:      modapi.arxiv.org/admin/shared_nav_header
    dev: services.dev.arxiv.org/admin/shared_nav_header
    """
    return request.app.extra["MODAPI_URL"] + "/admin/shared_nav_header"
