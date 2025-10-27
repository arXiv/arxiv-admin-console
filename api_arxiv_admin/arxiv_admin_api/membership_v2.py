"""
Member institution
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import Optional, List
from sqlalchemy.orm import Session
from pydantic import BaseModel

from arxiv.base import logging
from arxiv.db.models import MembershipInstitutions, MembershipUsers
from sqlalchemy import func

from . import is_admin_user, get_db

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_admin_user)], prefix="/membership_v2")


class V2MembershipInstitutionModel(BaseModel):
    __tablename__ = 'membership_institutions'

    id: Optional[int] = None  # Auto-incrementing primary key, might not be provided when creating
    name: str
    label: Optional[str] = None
    is_active: Optional[bool] = None
    country: Optional[str] = None
    country_code: Optional[str] = None
    consortia_code: Optional[str] = None
    member_type: Optional[str] = None
    ror_id: Optional[str] = None
    is_consortium: Optional[bool] = None
    comment: Optional[str] = None
    users: Optional[List[int]] = None

    class Config:
        from_attributes = True

    @staticmethod
    def base_query(session: Session) -> Query:
        """
        Returns a basic query for member institutions with aggregated users.
        """

        # First, create a subquery that groups users by institution
        users_subquery = session.query(
            MembershipUsers.sid,
            func.array_agg(MembershipUsers.user_id).label("users")
        ).group_by(MembershipUsers.sid).subquery()
        
        # Then join this subquery with the main institutions table
        return session.query(
            MembershipInstitutions.sid.label("id"),
            MembershipInstitutions.name,
            MembershipInstitutions.label,
            MembershipInstitutions.is_active,
            MembershipInstitutions.country,
            MembershipInstitutions.country_code,
            MembershipInstitutions.consortia_code,
            MembershipInstitutions.member_type,
            MembershipInstitutions.ror_id,
            MembershipInstitutions.is_consortium,
            MembershipInstitutions.comment,
            users_subquery.c.users
        ).outerjoin(
            users_subquery,
            users_subquery.c.sid == MembershipInstitutions.sid
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
) -> List[V2MembershipInstitutionModel]:
    query = V2MembershipInstitutionModel.base_query(db)

    if id:
        query = query.filter(MembershipInstitutions.sid.in_(id))
    else:
        if _start < 0 or _end < _start:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                detail="Invalid start or end index")

        order_columns = []
        if _sort:
            keys = _sort.split(",")
            for key in keys:
                try:
                    order_column = getattr(MembershipInstitutions, key)
                    order_columns.append(order_column)
                except AttributeError:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Invalid start or end index")

        if name:
            query = query.filter(MembershipInstitutions.name.contains(name))

        for column in order_columns:
            if _order == "DESC":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())


    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [V2MembershipInstitutionModel.model_validate(item) for item in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get('/{id:int}')
async def get_membership_institution_data(id: int, db: Session = Depends(get_db)) -> V2MembershipInstitutionModel:
    item = V2MembershipInstitutionModel.base_query(db).filter(MembershipInstitutions.sid == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    data = V2MembershipInstitutionModel.model_validate(item)
    return data


@router.put('/{id:int}')
async def update_membership_institution_data(
        id: int,
        body: V2MembershipInstitutionModel,
        db: Session = Depends(get_db)) -> V2MembershipInstitutionModel:
    item: MembershipInstitutions = db.query(MembershipInstitutions).filter(MembershipInstitutions.sid == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"MembershipInstitution {id} not found")

    # The record and body fields are not 1-to-1
    updated = set()
    updates = body.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if key == "users":
            continue
        if getattr(item, key) != value:
            setattr(item, key, value)
            updated.add(item)

    current_users: List[MembershipUsers] = db.query(MembershipUsers).filter(MembershipUsers.sid == id).all()
    u: MembershipUsers
    current_user_ids = {u.user_id for u in current_users}
    next_user_ids = set(body.users)

    disappearing_users = current_user_ids - next_user_ids
    appearing_users = next_user_ids - current_user_ids

    if len(disappearing_users):
        db.query(MembershipUsers).filter(
            MembershipUsers.sid == id,
            MembershipUsers.user_id.in_(disappearing_users)).delete()

    if len(appearing_users):
        for user_id in appearing_users:
            db.add(MembershipUsers(sid=id, user_id=user_id))

    db.commit()
    
    # Return updated data
    updated_item = V2MembershipInstitutionModel.base_query(db).filter(MembershipInstitutions.sid == id).one_or_none()
    if updated_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    data = V2MembershipInstitutionModel.model_validate(updated_item)
    return data


@router.post('/')
async def create_membership_institution_data(
        body: V2MembershipInstitutionModel,
        db: Session = Depends(get_db)) -> V2MembershipInstitutionModel:

    item = MembershipInstitutions(
        name=body.name,
        label=body.label,
        is_active=body.is_active,
        country=body.country,
        country_code=body.country_code,
        consortia_code=body.consortia_code,
        member_type=body.member_type,
        ror_id=body.ror_id,
        is_consortium=body.is_consortium,
        comment=body.comment)

    db.add(item)
    db.flush()
    db.refresh(item)

    for user_id in body.users:
        member_user = MembershipUsers(
            sid=item.sid,
            user_id=user_id)
        db.add(member_user)

    db.commit()
    # Return the created record

    created_item = V2MembershipInstitutionModel.base_query(db).filter(MembershipInstitutions.sid == item.sid).one_or_none()
    if created_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"MembershipInstitution {id} not found???")
    data = V2MembershipInstitutionModel.model_validate(created_item)
    return data


@router.delete('/{id:int}')
async def delete_membership_institution_data(
        id: int,
        db: Session = Depends(get_db)) -> V2MembershipInstitutionModel:

    item = db.query(MembershipInstitutions).filter(MembershipInstitutions.sid == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"MembershipInstitution {id} not found")
    db.delete(item)
    db.commit()
    mi = V2MembershipInstitutionModel.base_query(db).filter(MembershipInstitutions.sid == id).one_or_none()
    return V2MembershipInstitutionModel.model_validate(mi)
