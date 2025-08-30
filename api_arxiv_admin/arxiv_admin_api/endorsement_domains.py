"""Provides integration for the external user interface."""

from arxiv_bizlogic.fastapi_helpers import get_authn_user
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from typing import Optional, List

from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator, field_serializer

from arxiv.base import logging
from arxiv.db.models import EndorsementDomain
from arxiv.auth.user_claims import ArxivUserClaims

from . import is_admin_user, get_db

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_admin_user)], prefix="/endorsement_domains")

class EndorsementDomainModel(BaseModel):
    class Config:
        from_attributes = True

    id: str #  endorsement_domain: str # mapped_column(String(32), primary_key=True, server_default=FetchedValue())
    endorse_all: bool # YesNoEnum # Mapped[Literal["y", "n"]] = mapped_column(Enum("y", "n"), nullable=False, server_default=FetchedValue())
    mods_endorse_all: bool # YesNoEnum # Mapped[Literal["y", "n"]] = mapped_column(Enum("y", "n"), nullable=False, server_default=FetchedValue())
    endorse_email: bool # YesNoEnum # Mapped[Literal["y", "n"]] = mapped_column(Enum("y", "n"), nullable=False, server_default=FetchedValue())
    papers_to_endorse: int

    @field_validator('endorse_all', 'mods_endorse_all', 'endorse_email', mode='before')
    @classmethod
    def convert_yn_to_bool(cls, v):
        """Convert 'y'/'n' strings from database to boolean"""
        if isinstance(v, str):
            return v.lower() == 'y'
        return v


    @staticmethod
    def base_select(db: Session) -> Query:
        return db.query(
            EndorsementDomain.endorsement_domain.label("id"),
            EndorsementDomain.endorse_all,
            EndorsementDomain.mods_endorse_all,
            EndorsementDomain.endorse_email,
            EndorsementDomain.papers_to_endorse,
        )

    pass

@router.get('/')
async def list_endorsement_domains(
        response: Response,
        _sort: Optional[str] = Query("endorsement_domain", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        name: Optional[str] = Query(None),
        id: Optional[List[str]] = Query(None),
        db: Session = Depends(get_db)
    ) -> List[EndorsementDomainModel]:
    query = EndorsementDomainModel.base_select(db)

    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    order_columns = []
    if _sort:
        keys = _sort.split(",")
        for key in keys:
            if key == "id":
                key = "endorsement_domain"
            try:
                order_column = getattr(EndorsementDomain, key)
                order_columns.append(order_column)
            except AttributeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid start or end index")

    if id:
        query = query.filter(EndorsementDomain.endorsement_domain.in_(id))
    else:
        if name:
            query = query.filter(EndorsementDomain.endorsement_domain.contains(name))

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    items = query.offset(_start).limit(_end - _start).all()
    result = []
    for item in items:
        # Convert Row to dict and ensure field validators are triggered
        data = dict(item._mapping)
        validated_item = EndorsementDomainModel.model_validate(data)
        result.append(validated_item)
    return result


@router.get('/{id:str}')
async def get_endorsement_domain_data(
        id: str, 
        current_user: ArxivUserClaims = Depends(get_authn_user),
        db: Session = Depends(get_db)) -> EndorsementDomainModel:
    item = EndorsementDomainModel.base_select(db).filter(EndorsementDomain.endorsement_domain == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement Domain '{id}' not found'")
    return EndorsementDomainModel.model_validate(item._asdict())


@router.put('/{id:str}')
async def update_endorsement_domain(
        request: Request,
        id: str,
        body: EndorsementDomainModel,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        session: Session = Depends(get_db)) -> EndorsementDomainModel:

    item: EndorsementDomain | None = session.query(EndorsementDomain).filter(EndorsementDomain.endorsement_domain == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement Domain '{id}' not found'")

    # Update the record fields with manual boolean to y/n conversion
    item.endorse_all = 'y' if body.endorse_all else 'n'
    item.mods_endorse_all = 'y' if body.mods_endorse_all else 'n'
    item.endorse_email = 'y' if body.endorse_email else 'n'
    item.papers_to_endorse = body.papers_to_endorse
    
    session.commit()

    mint = EndorsementDomainModel.base_select(session).filter(EndorsementDomain.endorsement_domain == id).one_or_none()
    return EndorsementDomainModel.model_validate(mint._asdict())


@router.post('/')
async def create_endorsement_domain(
        body: EndorsementDomainModel,
        user: ArxivUserClaims = Depends(get_authn_user),
        session: Session = Depends(get_db)) -> EndorsementDomainModel:

    # Create the new EndorsementDomain record with manual boolean to y/n conversion
    item = EndorsementDomain(
        endorsement_domain=body.id,
        endorse_all='y' if body.endorse_all else 'n',
        mods_endorse_all='y' if body.mods_endorse_all else 'n',
        endorse_email='y' if body.endorse_email else 'n',
        papers_to_endorse=body.papers_to_endorse,
    )
    
    session.add(item)
    session.commit()
    session.refresh(item)
    
    # Return the created record
    mint = EndorsementDomainModel.base_select(session).filter(EndorsementDomain.endorsement_domain == item.endorsement_domain).one_or_none()
    return EndorsementDomainModel.model_validate(mint._asdict())


@router.delete('/{id:str}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_endorsement_domain(
        id: str,
        user: ArxivUserClaims = Depends(get_authn_user),
        db: Session = Depends(get_db)) -> None:
    item = db.query(EndorsementDomain).filter(EndorsementDomain.endorsement_domain == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail=f"Item {id} not found")
    db.delete(item)
    db.commit()
    return
