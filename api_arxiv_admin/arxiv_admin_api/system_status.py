"""admin-api system status"""
from arxiv_bizlogic.fastapi_helpers import COOKIE_ENV_NAMES, get_db
from fastapi import APIRouter, status, Request, HTTPException, Depends

from arxiv.base import logging
from arxiv.db.models import Category
from sqlalchemy.orm import Session
from starlette.responses import JSONResponse

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
