"""arXiv category routes."""
from enum import Enum
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response, Request

from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from pydantic import BaseModel
from arxiv.base import logging
from arxiv.db.models import Category, ArchiveGroup

from . import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/categories", tags=["metadata"])
archive_group_router = APIRouter(prefix="/archive_group", tags=["metadata"])

class EndorseOption(str, Enum):
    y = 'y'
    n = 'n'
    d = 'd'

class ArchiveModel(BaseModel):
    id: str
    name: str
    description: str

class SubjectClassModel(BaseModel):
    id: str
    name: str
    description: str

class CategoryModel(BaseModel):
    id: str
    archive: str
    subject_class: Optional[str]
    definitive: bool
    active: bool
    category_name: Optional[str]
    endorse_all: str # Mapped[Literal['y', 'n', 'd']] = mapped_column(Enum('y', 'n', 'd'), nullable=False, server_default=text("'d'"))
    endorse_email: str # Mapped[Literal['y', 'n', 'd']] = mapped_column(Enum('y', 'n', 'd'), nullable=False, server_default=text("'d'"))
    papers_to_endorse: int
    endorsement_domain: Optional[str]

    class Config:
        from_attributes = True

    @classmethod
    def base_query(cls, db: Session) -> Query:
        return db.query(
            func.concat(Category.archive, ".", Category.subject_class).label("id"),
            Category.archive,
            Category.subject_class,
            Category.definitive,
            Category.active,
            Category.category_name,
            Category.endorse_all,
            Category.endorse_email,
            Category.papers_to_endorse,
            Category.endorsement_domain
        )

@router.get('/')
async def list_categories(
        response: Response,
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        archive: Optional[str] = Query(""),
        subject_class: Optional[str] = Query(""),
        active: Optional[bool] = Query(None, description="active"),
        db: Session = Depends(get_db)
    ) -> List[CategoryModel]:
    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    query = CategoryModel.base_query(db)
    if archive:
        query = query.filter(Category.archive.ilike(archive + "%"))

    if subject_class:
        query = query.filter(Category.subject_class.ilike(subject_class + "%"))

    if active is not None:
        state = 1 if active else 0
        query = query.filter(Category.active == state)

    if _order == "DESC":
        query = query.order_by(Category.archive.desc())
        query = query.order_by(Category.subject_class.desc())
    else:
        query = query.order_by(Category.archive.asc())
        query = query.order_by(Category.subject_class.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    return [CategoryModel.model_validate(cat) for cat in query.offset(_start).limit(_end - _start).all()]


@router.get('/{archive}/subject-class')
async def list_subject_classes(
        response: Response,
        archive: str,
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        db: Session = Depends(get_db)
    ) -> List[CategoryModel]:
    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    query = CategoryModel.base_query(db).filter(Category.archive == archive)

    if _order == "DESC":
        query = query.order_by(Category.subject_class.desc())
    else:
        query = query.order_by(Category.subject_class.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    return [CategoryModel.model_validate(cat) for cat in query.offset(_start).limit(_end - _start).all()]


@router.get('/{archive}/subject-class/{subject_class}')
async def get_category(
        archive: str,
        subject_class: str,
        db: Session = Depends(get_db)
    ) -> CategoryModel:
    if subject_class == "*":
        subject_class = ""
    category = CategoryModel.base_query(db).filter(
        and_(
            Category.archive == archive,
            Category.subject_class == subject_class
        )).one_or_none()

    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No such category {archive}/{subject_class}")
    return CategoryModel.model_validate(category)


@router.get('/{id:str}')
async def get_category(id: str, db: Session = Depends(get_db)) -> CategoryModel:
    [archive, subject_class] = id.split(".")
    item = CategoryModel.base_query(db).filter(
        and_(
            Category.archive == archive,
            Category.subject_class == subject_class)).one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No such category {archive}/{subject_class}")
    return CategoryModel.model_validate(item)


@router.put('/{id:str}')
async def update_category(
        request: Request,
        id: str,
        session: Session = Depends(get_db)) -> CategoryModel:
    body = await request.json()
    [archive, subject_class] = id.split(".")
    item = session.query(Category).filter(
        and_(
            Category.archive == archive,
            Category.subject_class == subject_class).one_or_none())
    if item is None:
        raise HTTPException(status_code=404, detail=f"Category {archive}/{subject_class} does not exist.")

    # Verify?
    for key, value in body.items():
        if key in item.__dict__:
            setattr(item, key, value)

    session.commit()
    session.refresh(item)  # Refresh the instance with the updated data
    return CategoryModel.model_validate(item)


@router.post('/')
async def create_category(
        request: Request,
        session: Session = Depends(get_db)) -> CategoryModel:
    body = await request.json()

    item = Category(**body)
    session.add(item)
    session.commit()
    session.refresh(item)
    return CategoryModel.model_validate(item)


@router.delete('/{id:str}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
        id: str,
        session: Session = Depends(get_db)) -> Response:

    [archive, subject_class] = id.split(".")
    item = session.query(Category).filter(
        and_(
            Category.archive == archive,
            Category.subject_class == subject_class)).one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail=f"Category {archive}/{subject_class} does not exist.")
    session.delete(item)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


class ArchiveGroupModel(BaseModel):
    archive: str
    group: str

    @classmethod
    def base_query(cls, db: Session) -> Query:
        return db.query(
            ArchiveGroup.archive_id.label("archive"),
            ArchiveGroup.group_id.label("group"),
        )

@archive_group_router.get('/')
async def list_archive_groups(
        response: Response,
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        archive: Optional[str] = Query(""),
        group: Optional[str] = Query(""),
        active: Optional[bool] = Query(None, description="active"),
        db: Session = Depends(get_db)
) -> List[ArchiveGroupModel]:
    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    query = ArchiveGroupModel.base_query(db)
    if archive:
        query = query.filter(ArchiveGroup.archive_id == archive)

    if _order == "DESC":
        query = query.order_by(ArchiveGroup.archive_id.desc())
        query = query.order_by(ArchiveGroup.group_id.desc())
    else:
        query = query.order_by(ArchiveGroup.archive_id.asc())
        query = query.order_by(ArchiveGroup.group_id.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    results = query.offset(_start).limit(_end - _start).all()
    return [ArchiveGroupModel(archive=row.archive, group=row.group) for row in results]
