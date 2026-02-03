"""Provides integration for the external user interface."""
import json
from arxiv_bizlogic.audit_event import admin_audit, AdminAudit_EndorsementDomains, AuditAction, AuditChangeData
from arxiv_bizlogic.fastapi_helpers import get_authn_user, get_client_host, get_client_host_name, get_tapir_tracking_cookie
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from typing import Optional, List

from sqlalchemy.orm import Session, Query as OrmQuery
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, field_validator, field_serializer, ConfigDict

from arxiv.base import logging
from arxiv.db.models import EndorsementDomain
from arxiv.auth.user_claims import ArxivUserClaims

from . import is_admin_user, get_db

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_admin_user)], prefix="/endorsement_domains")

class EndorsementDomainModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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
    def base_select(db: Session) -> OrmQuery:
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
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
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


class EndorsementDomainDAO(EndorsementDomainModel):
    comment: str

@router.put('/{id:str}')
async def update_endorsement_domain(
        request: Request,
        id: str,
        dao: EndorsementDomainDAO,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        remote_ip: Optional[str] = Depends(get_client_host),
        remote_hostname: Optional[str] = Depends(get_client_host_name),
        tracking_cookie: Optional[str] = Depends(get_tapir_tracking_cookie),
        session: Session = Depends(get_db)) -> EndorsementDomainModel:

    item: EndorsementDomain | None = session.query(EndorsementDomain).filter(EndorsementDomain.endorsement_domain == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement Domain '{id}' not found'")

    # Define field mappings for boolean->string conversion
    field_conversions = {
        'endorse_all': 'y' if dao.endorse_all else 'n',
        'mods_endorse_all': 'y' if dao.mods_endorse_all else 'n',
        'endorse_email': 'y' if dao.endorse_email else 'n',
        'papers_to_endorse': dao.papers_to_endorse
    }

    audit_data: List[AuditChangeData] = []
    for field_name, new_value in field_conversions.items():
        old_value = getattr(item, field_name)
        if old_value != new_value:
            setattr(item, field_name, new_value)
            audit_data.append(AuditChangeData(
                name=field_name,
                before=old_value,
                after=new_value
            ))

    session.commit()

    comment = dao.comment
    admin_audit(session, AdminAudit_EndorsementDomains(
        current_user.user_id,
        current_user.tapir_session_id,
        data=AuditAction(
            id=id,
            action="update",
            audit_data=audit_data
        ),
        remote_ip=remote_ip,
        remote_hostname=remote_hostname,
        tracking_cookie=tracking_cookie,
        comment=comment
    ))

    mint = EndorsementDomainModel.base_select(session).filter(EndorsementDomain.endorsement_domain == id).one_or_none()
    if mint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement Domain '{id}' not found'")
    return EndorsementDomainModel.model_validate(mint._asdict())


@router.post('/')
async def create_endorsement_domain(
        dao: EndorsementDomainDAO,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        remote_ip: Optional[str] = Depends(get_client_host),
        remote_hostname: Optional[str] = Depends(get_client_host_name),
        tracking_cookie: Optional[str] = Depends(get_tapir_tracking_cookie),
        session: Session = Depends(get_db)) -> EndorsementDomainModel:


    # Create the new EndorsementDomain record with manual boolean to y/n conversion
    item = EndorsementDomain(
        endorsement_domain=dao.id,
        endorse_all='y' if dao.endorse_all else 'n',
        mods_endorse_all='y' if dao.mods_endorse_all else 'n',
        endorse_email='y' if dao.endorse_email else 'n',
        papers_to_endorse=dao.papers_to_endorse,
    )
    
    try:
        session.add(item)
        session.flush()
        session.refresh(item)
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Endorsement Domain '{dao.id}' already exists")

    mint = EndorsementDomainModel.base_select(session).filter(EndorsementDomain.endorsement_domain == item.endorsement_domain).one_or_none()
    if mint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Endorsement Domain '{item.endorsement_domain}' not found")
    mint_model = EndorsementDomainModel.model_validate(mint)

    audit_data = [
        AuditChangeData(name=key, before="", after=value) for key, value in mint_model.model_dump(mode="json", exclude_unset=True, exclude_none=True).items()
    ]

    admin_audit(session, AdminAudit_EndorsementDomains(
        current_user.user_id,
        current_user.tapir_session_id,
        data=AuditAction(
            id=item.endorsement_domain,
            action="create",
            audit_data=audit_data,
        ),
        remote_ip=remote_ip,
        remote_hostname=remote_hostname,
        tracking_cookie=tracking_cookie,
        comment=dao.comment
    ))

    try:
        session.commit()
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Endorsement Domain '{dao.id}' already exists")
    return dao


@router.delete('/{id:str}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_endorsement_domain(
        id: str,
        comment: str = Query("", description="Optional audit comment"),
        current_user: ArxivUserClaims = Depends(get_authn_user),
        remote_ip: Optional[str] = Depends(get_client_host),
        remote_hostname: Optional[str] = Depends(get_client_host_name),
        tracking_cookie: Optional[str] = Depends(get_tapir_tracking_cookie),
        session: Session = Depends(get_db)) -> None:
    item = session.query(EndorsementDomain).filter(EndorsementDomain.endorsement_domain == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail=f"Item {id} not found")

    before = {"endorse_all": item.endorse_all,
              "mods_endorse_all": item.mods_endorse_all,
              "endorse_email": item.endorse_email,
              "papers_to_endorse": item.papers_to_endorse}

    session.delete(item)
    session.commit()

    audit_data = [AuditChangeData(name=key, before=value, after="") for key, value in before.items()]

    admin_audit(session, AdminAudit_EndorsementDomains(
        current_user.user_id,
        current_user.tapir_session_id,
        data=AuditAction(
            id=id,
            action="delete",
            audit_data=audit_data
        ),
        remote_ip=remote_ip,
        remote_hostname=remote_hostname,
        tracking_cookie=tracking_cookie,
        comment=comment
    ))
    return
