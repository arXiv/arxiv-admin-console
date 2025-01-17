"""
Member institution
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import Optional, List

from pydantic.types import constr
from sqlalchemy.orm import Session
from pydantic import BaseModel

from arxiv.base import logging
from arxiv.db.models import MemberInstitution, MemberInstitutionContact

from . import is_admin_user, get_db

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_admin_user)], prefix="/membership_institutions")


class MemberInstitutionModel(BaseModel):
    __tablename__ = 'Subscription_UniversalInstitution'

    id: Optional[int]  # Auto-incrementing primary key, might not be provided when creating
    resolver_URL: Optional[constr(max_length=255)] = None
    name: constr(max_length=255)
    label: Optional[constr(max_length=255)] = None
    alt_text: Optional[constr(max_length=255)] = None
    link_icon: Optional[constr(max_length=255)] = None
    note: Optional[constr(max_length=255)] = None
    email: Optional[str] = None
    contact_name: Optional[str] = None

    class Config:
        from_attributes = True

    @staticmethod
    def base_query(session: Session) -> Query:
        """
        Returns a basic query for member institutions.
        """
        return session.query(
            MemberInstitution.id,
            MemberInstitution.name,
            MemberInstitution.label,
            MemberInstitution.resolver_URL,
            MemberInstitution.alt_text,
            MemberInstitution.link_icon,
            MemberInstitution.note,
            MemberInstitutionContact.email,
            MemberInstitutionContact.contact_name,
        ).outerjoin(
            MemberInstitutionContact,
            MemberInstitutionContact.id == MemberInstitution.id
        )

@router.get('/')
async def list_membership_institutions(
        response: Response,
        _sort: Optional[str] = Query("short_name", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        id: Optional[List[str]] = Query(None, description="List of member institution IDs to filter by"),
        name: Optional[str] = Query(None),
        db: Session = Depends(get_db)
    ) -> List[MemberInstitutionModel]:
    query = MemberInstitutionModel.base_query(db)

    if id:
        query = query.filter(MemberInstitution.id.in_(id))
    else:
        if _start < 0 or _end < _start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid start or end index")

        order_columns = []
        if _sort:
            keys = _sort.split(",")
            for key in keys:
                try:
                    order_column = getattr(MemberInstitution, key)
                    order_columns.append(order_column)
                except AttributeError:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Invalid start or end index")

        if name:
            query = query.filter(MemberInstitution.name.contains(name))

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [MemberInstitutionModel.from_orm(item) for item in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get('/{id:int}')
async def membership_institution_data(id: int, db: Session = Depends(get_db)) -> MemberInstitutionModel:
    item = MemberInstitutionModel.base_select(db).filter(MemberInstitution.id == id).one_or_none()
    if item:
        return MemberInstitutionModel.from_orm(item)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
