"""
Member institution
"""
from arxiv_bizlogic.sqlalchemy_helper import update_model_fields
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import Optional, List

from pydantic.types import conint
from sqlalchemy.orm import Session
from pydantic import BaseModel

from arxiv.base import logging
from arxiv.db.models import MemberInstitution, MemberInstitutionContact, MemberInstitutionIP

from . import is_admin_user, get_db

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_admin_user)], prefix="/membership_institutions")

institution_ip_router = APIRouter(dependencies=[Depends(is_admin_user)], prefix="/membership_institutions_ip")


class MemberInstitutionIPModel(BaseModel):
    id: Optional[int] = None  # Auto-incrementing primary key, might not be provided when creating
    sid: Optional[int] = None
    exclude: Optional[int] = None
    start: conint(ge=0)
    end: conint(ge=0)

    class Config:
        from_attributes = True

    @staticmethod
    def base_query(session: Session) -> sqlalchemy.orm.Query:
        """
        Returns a basic query for member institutions.
        """
        return session.query(
            MemberInstitutionIP.id,
            MemberInstitutionIP.sid,
            MemberInstitutionIP.exclude,
            MemberInstitutionIP.start,
            MemberInstitutionIP.end,
        )


class MemberInstitutionModel(BaseModel):
    __tablename__ = 'Subscription_UniversalInstitution'

    id: Optional[int] = None  # Auto-incrementing primary key, might not be provided when creating
    resolver_URL: Optional[str] = None
    name: str
    label: Optional[str] = None
    alt_text: Optional[str] = None
    link_icon: Optional[str] = None
    note: Optional[str] = None
    email: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None

    ip_ranges: Optional[List[MemberInstitutionIPModel]] = None

    class Config:
        from_attributes = True

    @staticmethod
    def base_query(session: Session) -> sqlalchemy.orm.Query:
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
            MemberInstitutionContact.phone,
        ).outerjoin(
            MemberInstitutionContact,
            MemberInstitutionContact.sid == MemberInstitution.id
        )


@router.get('/')
async def list_membership_institutions(
        response: Response,
        _sort: Optional[str] = Query("short_name", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
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

        for column in order_columns:
            if _order == "DESC":
                query = query.order_by(column.desc())
            else:
                query = query.order_by(column.asc())


    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [MemberInstitutionModel.model_validate(item) for item in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get('/{id:int}')
async def get_membership_institution_data(id: int, db: Session = Depends(get_db)) -> MemberInstitutionModel:
    item = MemberInstitutionModel.base_query(db).filter(MemberInstitution.id == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    data = MemberInstitutionModel.model_validate(item)
    data.ip_ranges = [MemberInstitutionIPModel.model_validate(row) for row in
                      MemberInstitutionIPModel.base_query(db).filter(MemberInstitutionIP.sid == id).all()]
    return data


@router.put('/{id:int}')
async def update_membership_institution_data(
        id: int,
        body: MemberInstitutionModel,
        db: Session = Depends(get_db)) -> MemberInstitutionModel:
    item = db.query(MemberInstitution).filter(MemberInstitution.id == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"MembershipInstitution {id} not found")

    updated = []

    updated.append(update_model_fields(
        db, item, body.model_dump(exclude_unset=True),
        updating_fields={ "name", "label", "resolver_URL", "alt_text", "link_icon",  "note"},
        primary_key_field="id", primary_key_value=id))

    item2: List[MemberInstitutionContact] = db.query(MemberInstitutionContact).filter(MemberInstitutionContact.sid == id).all()

    if item2 and len(item2) > 0:
        item2_1 = item2[0]
        if item2_1.email != body.email or item2_1.contact_name != body.contact_name or item2_1.phone != body.phone:
            updated.append(update_model_fields(
                db, item2_1, body.model_dump(exclude_unset=True),
                updating_fields={"email", "contact_name", "phone"},
                primary_key_field="id", primary_key_value=item2_1.id))
    elif body.email or body.contact_name or body.phone:
        item2_1 = MemberInstitutionContact(email="", contact_name="", phone=body.phone, sid=item.id)
        db.add(item2_1)
        db.flush()
        db.refresh(item2_1)
        update_model_fields(
            db, item2_1, body.model_dump(exclude_unset=True),
            updating_fields={"email", "contact_name", "phone"},
            primary_key_field="id", primary_key_value=item2_1.id)

    existing_ip_ranges = [MemberInstitutionIPModel.model_validate(row) for row in
                          db.query(MemberInstitutionIP).filter(MemberInstitutionIP.sid == id).all()]

    # Handle IP ranges updates
    if body.ip_ranges is not None:
        # Create sets for comparison using (start, end, exclude) tuples
        existing_set = {(ip.start, ip.end, ip.exclude or 0) for ip in existing_ip_ranges}
        new_set = {(ip.start, ip.end, ip.exclude or 0) for ip in body.ip_ranges}
        
        # Find ranges to delete and add
        to_delete = existing_set - new_set
        to_add = new_set - existing_set
        
        # Delete removed IP ranges
        if to_delete:
            for start, end, exclude in to_delete:
                db.query(MemberInstitutionIP).filter(
                    MemberInstitutionIP.sid == id,
                    MemberInstitutionIP.start == start,
                    MemberInstitutionIP.end == end,
                    MemberInstitutionIP.exclude == exclude
                ).delete()
        
        # Add new IP ranges
        for start, end, exclude in to_add:
            new_ip_range = MemberInstitutionIP(
                sid=id,
                start=start,
                end=end,
                exclude=exclude
            )
            db.add(new_ip_range)

    db.commit()
    
    # Return updated data
    updated_item = MemberInstitutionModel.base_query(db).filter(MemberInstitution.id == id).one_or_none()
    if updated_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    data = MemberInstitutionModel.model_validate(updated_item)
    data.ip_ranges = [MemberInstitutionIPModel.model_validate(row) for row in
                      MemberInstitutionIPModel.base_query(db).filter(MemberInstitutionIP.sid == id).all()]
    return data


@router.post('/')
async def create_membership_institution_data(
        body: MemberInstitutionModel,
        db: Session = Depends(get_db)) -> MemberInstitutionModel:

    item = MemberInstitution(name="", label="", resolver_URL="", alt_text="", note="")
    db.add(item)
    db.flush()
    db.refresh(item)

    id = item.id
    update_model_fields(
        db, item, body.model_dump(exclude_unset=True),
        updating_fields={"name", "label", "resolver_URL", "alt_text", "link_icon", "note"},
        primary_key_field="id", primary_key_value=id)

    if body.email or body.contact_name or body.phone:
        item2_1 = MemberInstitutionContact(sid=item.id, email="", contact_name="", phone=body.phone)
        db.add(item2_1)
        db.flush()
        db.refresh(item2_1)
        update_model_fields(
            db, item2_1, body.model_dump(exclude_unset=True),
            updating_fields={"email", "contact_name", "phone"},
            primary_key_field="id", primary_key_value=item2_1.id)

    if body.ip_ranges is not None:
        # Add new IP ranges
        for ip_range in body.ip_ranges:
            start = ip_range.start
            end = ip_range.end
            exclude = ip_range.exclude or 0
            new_ip_range = MemberInstitutionIP(
                sid=id,
                start=start,
                end=end,
                exclude=exclude
            )
            db.add(new_ip_range)

    db.commit()

    # Return the created record

    created_item = MemberInstitutionModel.base_query(db).filter(MemberInstitution.id == id).one_or_none()
    if created_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"MembershipInstitution {id} not found???")
    data = MemberInstitutionModel.model_validate(created_item)
    data.ip_ranges = [MemberInstitutionIPModel.model_validate(row) for row in
                      MemberInstitutionIPModel.base_query(db).filter(MemberInstitutionIP.sid == id).all()]
    return data


@router.delete('/{id:int}')
async def delete_membership_institution_data(
        id: int,
        db: Session = Depends(get_db)) -> MemberInstitutionModel:

    item = db.query(MemberInstitution).filter(MemberInstitution.id == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"MembershipInstitution {id} not found")
    name = item.name
    db.query(MemberInstitutionContact).filter(MemberInstitutionContact.sid == id).delete()
    db.query(MemberInstitutionIP).filter(MemberInstitutionIP.sid == id).delete()
    db.delete(item)
    db.commit()
    return MemberInstitutionModel.model_validate({"id": id, "name": name})


@institution_ip_router.get('/')
async def list_membership_institutions_ip(
        response: Response,
        _sort: Optional[str] = Query("short_name", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        id: Optional[List[str]] = Query(None, description="List of primary keys"),
        sid: Optional[str] = Query(None, description="Member institution ID"),
        db: Session = Depends(get_db)
) -> List[MemberInstitutionIPModel]:
    query = MemberInstitutionIPModel.base_query(db)

    if id:
        query = query.filter(MemberInstitutionIP.id.in_(id))
    else:
        order_columns = []
        if _sort:
            keys = _sort.split(",")
            for key in keys:
                try:
                    order_column = getattr(MemberInstitutionIP, key)
                    order_columns.append(order_column)
                except AttributeError:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Invalid start or end index")

        if sid:
            query = query.filter(MemberInstitutionIP.sid == sid)

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [MemberInstitutionIPModel.model_validate(item) for item in query.offset(_start).limit(_end - _start).all()]
    return result
