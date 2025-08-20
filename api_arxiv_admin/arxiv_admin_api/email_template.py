"""Provides integration for the external user interface."""
import datetime

from arxiv_bizlogic.fastapi_helpers import get_authn, get_authn_user
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from typing import Optional, List
from sqlalchemy.orm import Session, aliased
from pydantic import BaseModel, field_validator
from enum import IntEnum

from arxiv.base import logging
from arxiv.db.models import TapirEmailTemplate, TapirUser #, TapirNickname
from arxiv.auth.user_claims import ArxivUserClaims

from . import is_admin_user, get_db, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(is_admin_user)], prefix="/email_templates")

class WorkflowStatus(IntEnum):
    UNKNOWN = 0
    PENDING = 1
    ACCEPTED = 2
    REJECTED = 3

class EmailTemplateModel(BaseModel):
    class Config:
        from_attributes = True

    id: int
    short_name: str
    long_name: str
    lang: str
    data: str
    sql_statement: str
    created_by: int
    updated_by: int
    updated_date: Optional[datetime.datetime] = None
    workflow_status: str
    flag_system: bool
    creator_first_name: str
    creator_last_name: str
    updater_first_name: str
    updater_last_name: str

    @staticmethod
    def base_select(db: Session):
        creator = aliased(TapirUser)
        updater = aliased(TapirUser)
        return db.query(
            TapirEmailTemplate.template_id.label("id"),
            TapirEmailTemplate.short_name.label("short_name"),
            TapirEmailTemplate.lang,
            TapirEmailTemplate.long_name.label("long_name"),
            TapirEmailTemplate.data,
            TapirEmailTemplate.sql_statement,

            creator.first_name.label("creator_first_name"),
            creator.last_name.label("creator_last_name"),
            updater.first_name.label("updater_first_name"),
            updater.last_name.label("updater_last_name"),
            TapirEmailTemplate.update_date,
            TapirEmailTemplate.created_by,
            TapirEmailTemplate.updated_by,
            TapirEmailTemplate.workflow_status,
            TapirEmailTemplate.flag_system,
        ).join(creator, TapirEmailTemplate.created_by == creator.user_id).join(updater, TapirEmailTemplate.updated_by == updater.user_id)

    @field_validator("workflow_status", mode="before")
    @classmethod
    def convert_workflow_status(cls, value) -> str:
        if isinstance(value, int):
            return WorkflowStatus(value).name.lower()
        return str(value)

    @field_validator("flag_system", mode="before")
    @classmethod
    def convert_flag_system(cls, value) -> bool:
        if not isinstance(value, bool):
            return bool(value)
        return value

    pass

@router.get('/')
async def list_templates(
        response: Response,
        _sort: Optional[str] = Query("short_name", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: Optional[int] = Query(0, alias="_start"),
        _end: Optional[int] = Query(100, alias="_end"),
        short_name: Optional[str] = Query(None),
        long_name: Optional[str] = Query(None),
        start_date: Optional[datetime.datetime] = Query(None, description="Start date for filtering"),
        end_date: Optional[datetime.datetime] = Query(None, description="End date for filtering"),
        db: Session = Depends(get_db)
    ) -> List[EmailTemplateModel]:
    query = EmailTemplateModel.base_select(db)

    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    order_columns = []
    if _sort:
        keys = _sort.split(",")
        for key in keys:
            if key == "id":
                key = "template_id"
            try:
                order_column = getattr(TapirEmailTemplate, key)
                order_columns.append(order_column)
            except AttributeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid start or end index")

    if short_name:
        query = query.filter(TapirEmailTemplate.short_name.contains(short_name))

    if long_name:
        query = query.filter(TapirEmailTemplate.long_name.contains(long_name))

    if start_date:
        query = query.filter(TapirEmailTemplate.update_date >= start_date)

    if end_date:
        query = query.filter(TapirEmailTemplate.update_date <= end_date)

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [EmailTemplateModel.model_validate(item) for item in query.offset(_start).limit(_end - _start).all()]
    return result


@router.get('/{id:int}')
async def template_data(id: int, db: Session = Depends(get_db)) -> EmailTemplateModel:
    item = EmailTemplateModel.base_select(db).filter(TapirEmailTemplate.template_id == id).all()
    if item:
        return EmailTemplateModel.model_validate(item[0])
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Template '{id}' not found'")


@router.put('/{id:int}')
async def update_template(request: Request,
                          id: int,
                          session: Session = Depends(get_db)) -> EmailTemplateModel:
    body = await request.json()

    item = session.query(TapirEmailTemplate).filter(TapirEmailTemplate.template_id == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Template '{id}' not found'")

    # Verify?
    for key, value in body.items():
        if key in item.__dict__:
            setattr(item, key, value)

    session.commit()
    session.refresh(item)  # Refresh the instance with the updated data
    mint = EmailTemplateModel.base_select(session).filter(TapirEmailTemplate.template_id == item.template_id).one_or_none()
    return EmailTemplateModel.model_validate(mint)


@router.post('/')
async def create_email_template(request: Request,
                                user: ArxivUserClaims = Depends(get_authn),
                                session: Session = Depends(get_db)) -> EmailTemplateModel:
    body = await request.json()

    body['lang'] = 'en'
    body['sql_statement'] = ''
    body['update_date'] = datetime.datetime.now()
    body['created_by'] = user.user_id
    body['updated_by'] = user.user_id
    body['workflow_status'] = 2
    body['flag_system'] = 0

    item = TapirEmailTemplate(**body)
    session.add(item)
    session.commit()
    session.refresh(item)
    mint = EmailTemplateModel.base_select(session).filter(TapirEmailTemplate.template_id == item.template_id).one_or_none()
    return EmailTemplateModel.model_validate(mint)


@router.delete('/{id:int}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_email_template(id: int,
                                user: ArxivUserClaims = Depends(get_authn),
                                db: Session = Depends(get_db)) -> None:
    item = db.query(TapirEmailTemplate).filter(TapirEmailTemplate.template_id == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail=f"Item {id} not found")
    if item.flag_system == 1:
        raise HTTPException(status_code=404, detail=f"System email template {id} shall not be deleted.")
    db.delete(item)
    db.commit()
    return


@router.post('/{id:int}/test')
async def send_test_email_template(request: Request,
                                   id: int,
                                   claims: ArxivUserClaims = Depends(get_authn_user),
                                   session: Session = Depends(get_db)) -> EmailTemplateModel:
    template = session.query(EmailTemplateModel).filter(EmailTemplateModel.template_id == id).one_or_none()
    if template is None:
        raise HTTPException(status_code=404, detail=f"Template {id} not found")


    claims.email
