"""Provides integration for the external user interface."""
import datetime
import os
import json

from google.cloud import pubsub_v1
from arxiv_bizlogic.fastapi_helpers import get_authn, get_authn_user, datetime_to_epoch
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request, Response
from typing import Optional, List

from sqlalchemy import cast, LargeBinary, update, func
from sqlalchemy.orm import Session
from pydantic import BaseModel, field_validator
from enum import IntEnum

from arxiv.base import logging
from arxiv.db.models import TapirEmailTemplate #, TapirNickname
from arxiv.auth.user_claims import ArxivUserClaims

from . import is_admin_user, get_db

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

    @staticmethod
    def base_select(db: Session) -> Query:
        return db.query(
            TapirEmailTemplate.template_id.label("id"),
            cast(TapirEmailTemplate.short_name, LargeBinary).label("short_name"),
            TapirEmailTemplate.lang,
            cast(TapirEmailTemplate.long_name, LargeBinary).label("long_name"),
            cast(TapirEmailTemplate.data, LargeBinary).label("data"),
            TapirEmailTemplate.sql_statement,
            TapirEmailTemplate.update_date,
            TapirEmailTemplate.created_by,
            TapirEmailTemplate.updated_by,
            TapirEmailTemplate.workflow_status,
            TapirEmailTemplate.flag_system,
        )

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

    @field_validator("short_name", mode="before")
    @classmethod
    def convert_short_name(cls, value) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return value

    @field_validator("long_name", mode="before")
    @classmethod
    def convert_short_name(cls, value) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return value

    @field_validator("data", mode="before")
    @classmethod
    def convert_short_name(cls, value) -> str:
        if isinstance(value, bytes):
            return value.decode("utf-8")
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
                          current_user: ArxivUserClaims = Depends(get_authn_user),
                          session: Session = Depends(get_db)) -> EmailTemplateModel:
    body = await request.json()
    item = EmailTemplateModel.base_select(session).filter(TapirEmailTemplate.template_id == id).one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Template '{id}' not found'")

    record = session.query(TapirEmailTemplate).filter(TapirEmailTemplate.template_id == id).one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Template '{id}' not found'")

    for key, value in body.items():
        match key:
            case "id" | "created_by" | "flag_system" | "sql_statement":
                # cannot change these
                pass

            case "workflow_status":
                # ntai: 2025-08-20 I think this is not used.
                # wf = [wf.value for wf in list(WorkflowStatus) if wf.name.lower() == value]
                # setattr(item, key, wf[0].value if wf else 0)
                pass

            case "short_name" | "long_name" | "data":
                old_value = getattr(item, key)
                new_value = value.encode("utf-8")
                if old_value != new_value:
                    session.execute(
                        update(TapirEmailTemplate)
                        .where(TapirEmailTemplate.template_id == id)
                        .values({key: func.binary(new_value)})
                    )
                pass

            case _:
                pass

    record.updated_date = datetime_to_epoch(None, datetime.datetime.now(tz=datetime.timezone.utc))
    record.updated_by = int(current_user.user_id)
    session.commit()

    mint = EmailTemplateModel.base_select(session).filter(TapirEmailTemplate.template_id == id).one_or_none()
    return EmailTemplateModel.model_validate(mint)


@router.post('/')
async def create_email_template(request: Request,
                                user: ArxivUserClaims = Depends(get_authn),
                                session: Session = Depends(get_db)) -> EmailTemplateModel:
    body = await request.json()

    body['lang'] = 'en'
    body['sql_statement'] = ''
    body['update_date'] = datetime_to_epoch(None, datetime.datetime.now(tz=datetime.timezone.utc))
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
                                   subject: str = Query("Test email template", description="Subject of the test email"),
                                   current_user: ArxivUserClaims = Depends(get_authn_user),
                                   session: Session = Depends(get_db)) -> EmailTemplateModel:
    template: TapirEmailTemplate | None = session.query(TapirEmailTemplate).filter(TapirEmailTemplate.template_id == id).one_or_none()
    if template is None:
        raise HTTPException(status_code=404, detail=f"Template {id} not found")

    payload = {
        "subject": subject,
        "mail_to": current_user.email,
        "mail_from": current_user.email,
        "body": template.data,
        "timestamp": datetime.datetime.now(tz=datetime.timezone.utc).isoformat(),
    }

    # Get topic name and project ID from environment variables
    topic_name = os.environ.get('GCP_EMAIL_TOPIC_ID')
    project_id = os.environ.get('GCP_PROJECT')
    
    if not topic_name:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GCP_EMAIL_TOPIC_ID environment variable is not configured"
        )
    
    if not project_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GCP_PROJECT_ID environment variable is not configured"
        )

    try:
        # Initialize Pub/Sub publisher client
        publisher = pubsub_v1.PublisherClient()
        
        # Construct full topic path
        topic_path = publisher.topic_path(project_id, topic_name)
        
        # Convert payload to JSON bytes
        message_data = json.dumps(payload).encode('utf-8')
        
        # Publish message to Pub/Sub topic
        future = publisher.publish(topic_path, message_data)
        message_id = future.result()  # Wait for publish to complete
        
        logger.info(f"Test email published to Pub/Sub topic {topic_path} with message ID: {message_id}")
        
    except Exception as e:
        logger.error(f"Failed to publish test email to Pub/Sub: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send test email: {str(e)}"
        )

    # Return the template data
    mint = EmailTemplateModel.base_select(session).filter(TapirEmailTemplate.template_id == id).one_or_none()
    return EmailTemplateModel.model_validate(mint)
