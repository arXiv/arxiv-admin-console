"""arXiv endorsement routes."""
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy.orm import Session

from pydantic import BaseModel
from arxiv.base import logging
from arxiv.db.models import Endorsement

from ..categories import CategoryModel

logger = logging.getLogger(__name__)

class EndorsementCodeModel(BaseModel):
    endorser_id: str
    endorsement_code: str
    comment: str
    knows_personally: bool
    seen_paper: bool


class EndorsementType(str, Enum):
    user = "user"
    admin = "admin"
    auto = "auto"


class EndorsementModel(BaseModel):
    class Config:
        from_attributes = True

    id: int # Mapped[intpk]
    endorser_id: Optional[int] # Mapped[Optional[int]] = mapped_column(ForeignKey('tapir_users.user_id'), index=True)
    endorsee_id: int # Mapped[int] = mapped_column(ForeignKey('tapir_users.user_id'), nullable=False, index=True, server_default=FetchedValue())
    archive: str #  mapped_column(String(16), nullable=False, server_default=FetchedValue())
    subject_class: str # Mapped[str] = mapped_column(String(16), nullable=False, server_default=FetchedValue())
    flag_valid: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    type: EndorsementType | None # Mapped[Optional[Literal['user', 'admin', 'auto']]] = mapped_column(Enum('user', 'admin', 'auto'))
    point_value: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    issued_when: datetime # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    request_id: int | None # Mapped[Optional[int]] = mapped_column(ForeignKey('arXiv_endorsement_requests.request_id'), index=True)

    arXiv_categories: Optional[CategoryModel] #  = relationship('Category', primaryjoin='and_(Endorsement.archive == Category.archive, Endorsement.subject_class == Category.subject_class)', back_populates='arXiv_endorsements')
    # endorsee_of: List[UserModel] # = relationship('TapirUser', primaryjoin='Endorsement.endorsee_id == TapirUser.user_id', back_populates='endorsee_of')
    # endorser: UserModel # = relationship('TapirUser', primaryjoin='Endorsement.endorser_id == TapirUser.user_id', back_populates='endorses')
    #request: List['EndorsementRequestModel'] # = relationship('EndorsementRequest', primaryjoin='Endorsement.request_id == EndorsementRequest.request_id', back_populates='endorsement')

    @staticmethod
    def base_select(db: Session):
        return db.query(
            Endorsement.endorsement_id.label("id"),
            Endorsement.endorser_id,
            Endorsement.endorsee_id,
            Endorsement.archive,
            Endorsement.subject_class,
            Endorsement.flag_valid,
            Endorsement.type,
            Endorsement.point_value,
            Endorsement.issued_when,
            Endorsement.request_id,
        )

