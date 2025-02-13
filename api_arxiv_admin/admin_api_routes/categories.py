"""arXiv category routes."""
import re
from datetime import timedelta, datetime, date
from enum import Enum
from typing import Optional, List, Any

from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response

from sqlalchemy import select, update, func, case, Select, distinct, exists, and_
from sqlalchemy.orm import Session, joinedload

from pydantic import BaseModel, Field
from arxiv.base import logging
from arxiv.db import transaction
from arxiv.db.models import Category

from . import is_admin_user, get_db, datetime_to_epoch, VERY_OLDE

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/categories")

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
        response: Response,
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
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,)
    return CategoryModel.model_validate(category)


@router.get('/{id:str}')
async def get_category(id: str, db: Session = Depends(get_db)) -> CategoryModel:
    [archive, subject_class] = id.split(".")
    item = db.query(Category).filter(
        and_(
            Category.archive == archive,
            Category.subject_class == subject_class)).all()
    if item:
        return CategoryModel.model_validate(item[0])
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)


@router.put('/{id:str}')
async def update_category(
        request: Request,
        id: str,
        session: Session = Depends(transaction)) -> CategoryModel:
    body = await request.json()
    [archive, subject_class] = id.split(".")
    item = session.query(Category).filter(
        and_(
            Category.archive == archive,
            Category.subject_class == subject_class).one_or_none())
    if item is None:
        raise HTTPException(status_code=404, detail="User not found")

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
        session: Session = Depends(transaction)) -> CategoryModel:
    body = await request.json()

    item = Category(**body)
    session.add(item)
    session.commit()
    session.refresh(item)
    return CategoryModel.model_validate(item)


@router.delete('/{id:str}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
        id: str,
        session: Session = Depends(transaction)) -> Response:

    [archive, subject_class] = id.split(".")
    item = session.query(Category).filter(
        and_(
            Category.archive == archive,
            Category.subject_class == subject_class)).one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="User not found")
    item.delete_instance()
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
