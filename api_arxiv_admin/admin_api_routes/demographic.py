"""arXiv paper display routes."""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import Optional, List
from arxiv.base import logging
from arxiv.db.models import Demographic
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, date, timedelta
from .models import CrossControlModel
import re

from . import is_admin_user, get_db, datetime_to_epoch, VERY_OLDE

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_admin_user)], prefix="/demographics")

class DemographicModel(BaseModel):
    id: int # user_id: int #  = mapped_column(ForeignKey('tapir_users.user_id'), primary_key=True, server_default=FetchedValue())
    country: str # = mapped_column(String(2), nullable=False, index=True, server_default=FetchedValue())
    affiliation: str # = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    url: str # = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    type: Optional[int] # = mapped_column(SmallInteger, index=True)
    archive: Optional[str] # = mapped_column(String(16))
    subject_class: Optional[str] # = mapped_column(String(16))
    original_subject_classes: str # = mapped_column(String(255), nullable=False, server_default=FetchedValue())
    flag_group_physics: Optional[int] # = mapped_column(Integer, index=True)
    flag_group_math: int #  = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_cs: int #  = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_nlin: int #  = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_proxy: int #  = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_journal: int #  = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_xml: int #  = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    dirty: int #  = mapped_column(Integer, nullable=False, server_default=text("'0'"))
    flag_group_test: int #  = mapped_column(Integer, nullable=False, server_default=text("'0'"))
    flag_suspect: int #  = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_q_bio: int #  = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_q_fin: int #  = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_stat: int #  = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_eess: int #  = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    flag_group_econ: int #  = mapped_column(Integer, nullable=False, index=True, server_default=text("'0'"))
    veto_status: str # Mapped[Literal['ok', 'no-endorse', 'no-upload', 'no-replace']] = mapped_column(Enum('ok', 'no-endorse', 'no-upload', 'no-replace'), nullable=False, server_default=text("'ok'"))

    class Config:
        orm_mode = True
        from_attributes = True

    @staticmethod
    def base_select(db: Session):
        return db.query(
            Demographic.user_id.label("id"),
            Demographic.country,
            Demographic.affiliation,
            Demographic.url,
            Demographic.type,
            Demographic.archive,
            Demographic.subject_class,
            Demographic.original_subject_classes,
            Demographic.flag_group_physics,
            Demographic.flag_group_math,
            Demographic.flag_group_cs,
            Demographic.flag_group_nlin,
            Demographic.flag_proxy,
            Demographic.flag_journal,
            Demographic.flag_xml,
            Demographic.dirty,
            Demographic.flag_group_test,
            Demographic.flag_suspect,
            Demographic.flag_group_q_bio,
            Demographic.flag_group_q_fin,
            Demographic.flag_group_stat,
            Demographic.flag_group_eess,
            Demographic.flag_group_econ,
            Demographic.veto_status)


@router.get('/')
async def list_demographics(
        response: Response,
        _sort: Optional[str] = Query("id", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        id: Optional[List[int]] = Query(None, description="List of user IDs to filter by"),
        db: Session = Depends(get_db)
    ) -> List[DemographicModel]:
    query = DemographicModel.base_select(db)

    if id is not None:
        query = query.filter(Demographic.user_id.in_(id))
    else:
        if _start < 0 or _end < _start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid start or end index")

    order_columns = []
    if _sort:
        keys = _sort.split(",")
        for key in keys:
            if key == "id":
                key = "user_id"
            try:
                order_column = getattr(Demographic, key)
                order_columns.append(order_column)
            except AttributeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid start or end index")
    for column in order_columns:
        if _order == "DESC":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [DemographicModel.from_orm(item) for item in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get("/{id:int}")
def get_demographic(id:int,
                    session: Session = Depends(get_db)) -> DemographicModel:
    """Display a paper."""
    doc = DemographicModel.base_select(session).filter(Demographic.user_id == id).one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Demographic not found for {id}")
    return doc

