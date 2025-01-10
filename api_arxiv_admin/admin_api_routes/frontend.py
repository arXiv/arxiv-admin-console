"""frontend serving router"""

from fastapi import APIRouter
from pathlib import Path
from fastapi.responses import FileResponse

from arxiv.base import logging

from . import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(tags=["frontend"])


# Serve React static files
@router.get("/frontend/{full_path:path}")
async def serve_react_app(full_path: str):
    if full_path and Path(f"frontend/build/{full_path}").exists():
        return FileResponse(f"frontend/build/{full_path}")
    return FileResponse("frontend/build/index.html")

@router.get("/static/{full_path:path}")
async def serve_react_app(full_path: str):
    if full_path and Path(f"frontend/build/static/{full_path}").exists():
        return FileResponse(f"frontend/build/static/{full_path}")
    return FileResponse("frontend/build/index.html")
