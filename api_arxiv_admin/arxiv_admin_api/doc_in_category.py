"""arXiv moderator routes."""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response

from sqlalchemy import func, and_ # case, Select, distinct, exists, update,
from sqlalchemy.orm import Session, Query as SAQuery

from pydantic import BaseModel, ConfigDict
from arxiv.base import logging
# from arxiv.db import transaction
from arxiv.db.models import t_arXiv_in_category

from . import is_admin_user, get_db, datetime_to_epoch, VERY_OLDE
from .dao.doc_in_category_model import DocInCategoryModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/doc-in-category", tags=["document"])


class DocInCategoryWithId(DocInCategoryModel):
    id: str

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def base_query(cls, db: Session) -> SAQuery:
        return db.query(
            func.concat(t_arXiv_in_category.c.document_id, "+",
                        t_arXiv_in_category.c.archive, "+",
                        t_arXiv_in_category.c.subject_class).label("id"),
            t_arXiv_in_category.c.is_primary,
        )


@router.get('/')
async def list_documents_in_category(
        response: Response,
        _sort: Optional[str] = Query("document_id,archive,subject_class", description="keys"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        document_id: Optional[int] = Query(None),
        archive: Optional[str] = Query(None),
        subject_class: Optional[str] = Query(None),
        id: Optional[List[str]] = Query(None, description="List of IDs to filter by"),
        db: Session = Depends(get_db)
    ) -> List[DocInCategoryWithId]:
    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    if id is not None:
        result = []
        for combind_id in id:
            fragments = combind_id.split("+")
            if len(fragments) != 3:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID")
            document_id = int(fragments[0])
            archive = fragments[1] 
            subject_class = fragments[2]
            record = DocInCategoryWithId.base_query(db).filter(and_(
                t_arXiv_in_category.c.document_id == document_id,
                t_arXiv_in_category.c.archive == archive,
                t_arXiv_in_category.c.subject_class == subject_class
            )).one_or_none()
            if record:
                result.append(record)

        response.headers['X-Total-Count'] = str(len(result))
        return [DocInCategoryWithId.model_validate(rec) for rec in result[_start:_end]]

    query = DocInCategoryWithId.base_query(db)
    order_columns = []
    if _sort:
        keys = _sort.split(",")
        for key in keys:
            if key in order_columns:
                continue
            if key == "id":
                order_columns = [
                    getattr(t_arXiv_in_category.c, col) for col in ["document_id", "archive", "subject_class"]
                ]
                continue
            try:
                order_column = getattr(t_arXiv_in_category.c, key)
                order_columns.append(order_column)
            except AttributeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid start or end index")

    query = DocInCategoryWithId.base_query(db)
    if document_id is not None:
        query = query.filter(t_arXiv_in_category.c.document_id == document_id)

    if archive is not None:
        query = query.filter(t_arXiv_in_category.c.archive == archive)

    if subject_class is not None:
        query = query.filter(t_arXiv_in_category.c.subject_class == subject_class)

    for column in order_columns:
        if _order == "DESC":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    return [DocInCategoryWithId.model_validate(mod) for mod in query.offset(_start).limit(_end - _start).all()]


@router.get('/{id: str}')
async def get_documents_in_category(
        response: Response,
        _sort: Optional[str] = Query("document_id,archive,subject_class", description="keys"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        id: str = Query("", description="In cat ID"),
        db: Session = Depends(get_db)
    ) -> Optional[DocInCategoryWithId]:

    fragments = id.split("+")
    document_id = fragments[0]
    archive = fragments[1]
    subject_class = fragments[2]
    record = DocInCategoryWithId.base_query(db).filter(and_(
        t_arXiv_in_category.c.document_id == document_id,
        t_arXiv_in_category.c.archive == archive,
        t_arXiv_in_category.c.subject_class == subject_class
    )).one_or_none()

    if not record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    response.headers['X-Total-Count'] = "1"
    return DocInCategoryWithId.model_validate(record)

