from arxiv.auth.user_claims import ArxivUserClaims
from arxiv_bizlogic.fastapi_helpers import get_authn_user
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from typing import Optional, List
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict

from arxiv.base import logging
from arxiv.db.models import License

from . import get_db # , is_admin_user, get_current_user
# from arxiv_bizlogic.fastapi_helpers import get_authn

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/licenses")


class LicenseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str  # name
    label: Optional[str] = None
    active: Optional[bool] = None
    note: Optional[str] = None
    sequence: Optional[int] = None

    @staticmethod
    def base_select(session: Session):
        return session.query(
            License.name.label("id"),
            License.label,
            License.active,
            License.note,
            License.sequence
        )


@router.get('/')
async def list_licenses(
        response: Response,
        _sort: Optional[str] = Query("sequence", description="sort by"),
        _order: Optional[str] = Query("ASC", description="sort order"),
        _start: int = Query(0, alias="_start"),
        _end: int = Query(100, alias="_end"),
        id: Optional[List[str]] = Query(None, description="List of licenses"),
        active: Optional[bool] = Query(None, description="Active licenses"),
        session: Session = Depends(get_db)
    ) -> List[LicenseModel]:
    query = LicenseModel.base_select(session)

    if _start < 0 or _end < _start:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Invalid start or end index")

    if id is not None:
        query = query.filter(License.name.in_(id))

    if active is not None:
        active_value = 1 if active else 0
        query = query.filter(License.active == active_value)

    order_columns = []
    if _sort:
        keys = _sort.split(",")
        for key in keys:
            if key == "id":
                key = "name"
            try:
                order_column = getattr(License, key)
                order_columns.append(order_column)
            except AttributeError:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="Invalid sort field")

    # Apply sorting
    for column in order_columns:
        if _order == "DESC":
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())

    count = query.count()
    response.headers['X-Total-Count'] = str(count)
    result = [LicenseModel.model_validate(item) for item in query.offset(_start).limit(_end - _start).all()]
    return result


@router.put('/{id:str}')
async def update_license(
        response: Response,
        id: str,
        body: LicenseModel,
        current_user: ArxivUserClaims = Depends(get_authn_user),
        session: Session = Depends(get_db)
    ) -> LicenseModel:

    if not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    lic = session.query(License).filter(License.name == id).one_or_none()
    if lic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="License not found")

    body_dict = body.model_dump(exclude_unset=True)
    changed = False
    for key, value in body_dict.items():
        if getattr(lic, key) != value:
          setattr(lic, key, value)
          changed = True

    if changed:
        session.commit()

    return LicenseModel.model_validate(LicenseModel.base_select(session).filter(License.name == id).one())
