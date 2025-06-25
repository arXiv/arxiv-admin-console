"""arXiv endorsement routes."""
from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import case
from sqlalchemy.orm import Session

from pydantic import BaseModel
from arxiv.base import logging
from arxiv.db.models import Endorsement, EndorsementsAudit

from ..categories import CategoryModel
from ..endorsement_requests import EndorsementRequestModel
from ..public_users import PublicUserModel

logger = logging.getLogger(__name__)


class EndorsementCodeModel(BaseModel):
    preflight: bool
    endorser_id: str
    positive: bool
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
    endorser_id: Optional[int] = None # Mapped[Optional[int]] = mapped_column(ForeignKey('tapir_users.user_id'), index=True)
    endorsee_id: int # Mapped[int] = mapped_column(ForeignKey('tapir_users.user_id'), nullable=False, index=True, server_default=FetchedValue())
    archive: str #  mapped_column(String(16), nullable=False, server_default=FetchedValue())
    subject_class: str # Mapped[str] = mapped_column(String(16), nullable=False, server_default=FetchedValue())
    flag_valid: bool # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    type: EndorsementType | None = None # Mapped[Optional[Literal['user', 'admin', 'auto']]] = mapped_column(Enum('user', 'admin', 'auto'))
    positive_endorsement: bool
    point_value: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    issued_when: datetime # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    request_id: int | None = None # Mapped[Optional[int]] = mapped_column(ForeignKey('arXiv_endorsement_requests.request_id'), index=True)

    arXiv_category: Optional[CategoryModel] = None #  = relationship('Category', primaryjoin='and_(Endorsement.archive == Category.archive, Endorsement.subject_class == Category.subject_class)', back_populates='arXiv_endorsements')
    # endorsee_of: List[UserModel] # = relationship('TapirUser', primaryjoin='Endorsement.endorsee_id == TapirUser.user_id', back_populates='endorsee_of')
    # endorser: UserModel # = relationship('TapirUser', primaryjoin='Endorsement.endorser_id == TapirUser.user_id', back_populates='endorses')
    #request: List['EndorsementRequestModel'] # = relationship('EndorsementRequest', primaryjoin='Endorsement.request_id == EndorsementRequest.request_id', back_populates='endorsement')

    session_id: Optional[int] = None
    comment: Optional[str] = None
    remote_addr: Optional[str] = None
    remote_host: Optional[str] = None
    tracking_cookie: Optional[str] = None
    flag_knows_personally: Optional[bool] = None
    flag_seen_paper: Optional[bool] = None

    @staticmethod
    def base_select(db: Session):
        return db.query(
            Endorsement.endorsement_id.label("id"),
            Endorsement.endorser_id,
            Endorsement.endorsee_id,
            Endorsement.archive,
            Endorsement.subject_class,
            case((Endorsement.flag_valid != 0, True), else_=False).label("flag_valid"),
            Endorsement.type,
            Endorsement.point_value,
            case((Endorsement.point_value > 0, True), else_=False).label("positive_endorsement"),
            Endorsement.issued_when,
            Endorsement.request_id,
            EndorsementsAudit.session_id,
            EndorsementsAudit.comment,
            EndorsementsAudit.remote_addr,
            EndorsementsAudit.remote_host,
            EndorsementsAudit.tracking_cookie,
            case((EndorsementsAudit.flag_knows_personally == 1, True), else_=False).label("flag_knows_personally"),
            case((EndorsementsAudit.flag_seen_paper == 1, True), else_=False).label("flag_seen_paper"),
        ).outerjoin(
            EndorsementsAudit,
            EndorsementsAudit.endorsement_id == Endorsement.endorsement_id
        )


class EndorserCapabilityType(str, Enum):
    unknown = "unknown"
    credited = "credited"
    uncredited = "uncredited"
    prohibited = "prohibited"
    oneself = "oneself"


class EndorsementOutcomeModel(BaseModel):
    submitted: bool           # Endorser has submitted an endorsement
    accepted: bool            # Endorsee has the endorsement accepted
    request_acceptable: bool  # Endorsee can accept ths endorsementa
    endorser_capability: EndorserCapabilityType   # Endorser's capability for submitting
    endorser_n_papers: Optional[int] = None  # number of credible papers
    reason: str
    endorsement_request: Optional[EndorsementRequestModel] = None
    endorsee: Optional[PublicUserModel] = None
    endorsement: Optional[EndorsementModel] = None
