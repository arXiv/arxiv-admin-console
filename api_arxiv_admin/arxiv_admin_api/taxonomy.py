"""arXiv moderator routes."""
from typing import Optional, List, Dict

from fastapi import APIRouter, HTTPException, status, Query, Response

# from pydantic import BaseModel
from arxiv.base import logging
from arxiv.taxonomy import definitions
from arxiv.taxonomy.category import Group

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/taxonomy", tags=["Taxonomy"])



shadow_groups : Dict[str, Group] = {
    "grp_q-stat": Group(
        id="grp_q-stat",
        full_name="Quantitative Statistics",
        is_active=True,
        start_year=1992,
        default_archive="stat",
    ),
    "grp_q-econ": Group(
        id="grp_q-econ",
        full_name="Quantitative Economics",
        is_active=True,
        start_year=1992,
        default_archive="econ",
    ),
}


@router.get('/groups')
async def list_category_groups(
        response: Response,
        _sort: Optional[str] = Query("id", description="ID"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        id: Optional[List[str]] = Query(None, description="List of IDs to filter by"),
    ) -> List[definitions.Group]:

    if _start and _end:
        if _end < _start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid start or end index")

    if id is not None:
        return [group for key, group in definitions.GROUPS.items() if key in id]

    groups: List[definitions.Group] = list(definitions.GROUPS.values())

    if _sort:
        attr = definitions.Group.model_fields.get(_sort, None)
        if attr is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"{_sort} does not exist on Group")
        if _order is None:
            _order = "ASC"
        groups.sort(key=lambda group: getattr(group, _sort), reverse=_order !="ASC")
    return groups[_start:_end]


@router.get('/groups/{group_id:str}')
async def get_group(group_id: str ) -> definitions.Group:

    group = definitions.GROUPS.get(group_id, None)
    if group is None:
        group = shadow_groups.get(group_id, None)
        if group is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"{group_id} does not exist")
    return group


@router.get('/categories')
async def list_categories(
        response: Response,
        _sort: Optional[str] = Query("document_id,archive,subject_class", description="keys"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        id: Optional[List[str]] = Query(None, description="List of IDs to filter by"),
    ) -> List[definitions.Category]:

    if _start and _end:
        if _end < _start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid start or end index")
    if id is not None:
        return [group for key, group in definitions.CATEGORIES.items() if key in id]

    categories: List[definitions.Category] = list(definitions.CATEGORIES.values())

    if _sort:
        attr = definitions.Category.model_fields.get(_sort, None)
        if attr is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"{_sort} does not exist on Group")
        if _order is None:
            _order = "ASC"
        categories.sort(key = lambda x: getattr(x, _sort), reverse=_order !="ASC")
    return categories[_start:_end]


@router.get('/categories/{category_id:str}')
async def get_category(category_id: str) -> definitions.Category:
    category = definitions.CATEGORIES.get(category_id, None)
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"{category_id} does not exist")
    return category


@router.get('/archives')
async def list_archives(
        response: Response,
        _sort: Optional[str] = Query("document_id,archive,subject_class", description="keys"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        id: Optional[List[str]] = Query(None, description="List of IDs to filter by"),
    ) -> List[definitions.Archive]:

    if _start and _end:
        if _end < _start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid start or end index")
    if id is not None:
        return [group for key, group in definitions.ARCHIVES.items() if key in id]

    archives: List[definitions.Archive] = definitions.ARCHIVES.values()

    if _sort:
        attr = definitions.Archive.model_fields.get(_sort, None)
        if attr is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"{_sort} does not exist on Group")
        if _order is None:
            _order = "ASC"
        archives.sort(key=lambda x: getattr(x, _sort), reverse=_order !="ASC")
    return archives[_start:_end]

@router.get('/archives/{archive_id:str}')
async def get_archive(archive_id: str) -> definitions.Archive:
    archive = definitions.ARCHIVES.get(archive_id, None)
    if archive is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail=f"{archive_id} does not exist")
    return archive
