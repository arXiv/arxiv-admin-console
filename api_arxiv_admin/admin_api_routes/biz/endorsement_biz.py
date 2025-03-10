import abc
from typing import Optional, List, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session, aliased
from arxiv.db.models import (Endorsement, Category, EndorsementDomain, TapirNickname, QuestionableCategory,)
from datetime import datetime, timedelta
from pydantic import BaseModel
from ..endorsement_requsets import EndorsementRequestModel
from ..dao.endorsement_model import EndorsementType, EndorsementCodeModel, EndorsementOutcomeModel, EndorsementModel
from ..public_users import PublicUserModel
from ..user import UserModel


# I don't know of the rational of this.
# Someone needs to review this
def canonicalize_category(archive: str, subject_class: str) -> Tuple[str, str]:
    if archive == "math" and subject_class == "MP":
        archive = "math-ph"
        subject_class = ""
    elif archive == "stat" and subject_class == "TH":
        archive = "math"
        subject_class = "ST"
    elif archive == "math" and subject_class == "IT":
        archive = "cs"
    elif archive == "q-fin" and subject_class == "EC":
        archive = "econ"
        subject_class = "GN"
    elif archive == "cs" and subject_class == "NA":
        archive = "math"
        subject_class = "NA"
    elif archive == "cs" and subject_class == "SY":
        archive = "eess"
        subject_class = "SY"

    return archive, subject_class


def pretty_category(archive: str, subject_class: str) -> str:
    if not subject_class:
        subject_class = "*"
    return f"{archive}.{subject_class}"


class EndorsementWithEndorser(BaseModel):
    class Config:
        from_attributes = True

    endorsement_id: int  # Mapped[intpk]
    endorser_id: Optional[int]  # Mapped[Optional[int]] = mapped_column(ForeignKey('tapir_users.user_id'), index=True)
    endorsee_id: int  # Mapped[int] = mapped_column(ForeignKey('tapir_users.user_id'), nullable=False, index=True, server_default=FetchedValue())
    archive: str  # mapped_column(String(16), nullable=False, server_default=FetchedValue())
    subject_class: str  # Mapped[str] = mapped_column(String(16), nullable=False, server_default=FetchedValue())
    flag_valid: int  # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    type: str | None  # Mapped[Optional[Literal['user', 'admin', 'auto']]] = mapped_column(Enum('user', 'admin', 'auto'))
    point_value: int  # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    issued_when: datetime  # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    request_id: int | None  # Mapped[Optional[int]] = mapped_column(ForeignKey('arXiv_endorsement_requests.request_id'), index=True)

    endorser_username: str | None

    @staticmethod
    def base_select(db: Session):
        nick = aliased(TapirNickname)
        return db.query(
            Endorsement.endorsement_id,
            Endorsement.endorser_id,
            Endorsement.endorsee_id,
            Endorsement.archive,
            Endorsement.subject_class,
            Endorsement.flag_valid,
            Endorsement.type,
            Endorsement.point_value,
            Endorsement.issued_when,
            Endorsement.request_id,

            nick.nickname.label('endorser_username'),
        ).join(nick, Endorsement.endorser_id == nick.user_id)


class PaperProps(BaseModel):
    class Config:
        from_attributes = True
    document_id: int
    flag_author: bool
    title: str
    dated: Optional[datetime] = None


class EndorsementAccessor:
    @abc.abstractmethod
    def is_moderator(self, user_id: int, archive: str, subject_class: Optional[str] = None) -> bool:
        raise Exception("Not implemented")

    @abc.abstractmethod
    def get_category(self, archive: str, subject_class: str) -> Category | None:
        raise Exception("Not implemented")

    @abc.abstractmethod
    def get_domain_info(self, category: Category) -> EndorsementDomain | None:
        """Gets Endorsement domain from category"""
        raise Exception("Not implemented")

    @abc.abstractmethod
    def get_endorsements(self, user_id: str, canon_archive: str, canon_subject_class: str) -> List[EndorsementWithEndorser]:
        """SELECT endorser_id, point_value, type FROM arXiv_endorsements
                           WHERE endorsee_id = :user_id AND archive = :archive AND subject_class = :subject_class AND flag_valid = 1"""
        raise Exception("Not implemented")

    @abc.abstractmethod
    def get_questionable_categories(self, archive: str, subject_class: str) -> List[QuestionableCategory]:
        raise Exception("Not implemented")

    @abc.abstractmethod
    def get_papers_by_user(self, user_id: str, domain: str, window: [datetime | None],require_author: bool = True) -> List[PaperProps]:
        raise Exception("Not implemented")

    @abc.abstractmethod
    def is_academic_email(self, email: str) -> Tuple[bool, str]:
        raise Exception("Not implemented")

    @abc.abstractmethod
    def get_user(self, id: str) -> UserModel | None:
        raise Exception("Not implemented")

    @abc.abstractmethod
    def tapir_audit_admin(self,
                          biz: "EndorsementBusiness",
                          affected_user: int,
                          action: str,
                          data: str = "",
                          comment: str = "",
                          user_id: Optional[int] = None,
                          session_id: Optional[int] = None) -> None:
        """
        Logs administrative actions in the `tapir_admin_audit` table.

        This function records administrative actions taken on a user within
        the system, storing relevant metadata such as the acting admin,
        affected user, session details, and additional comments.

        :param self:
        :ppram biz: Endorsement business logic data
        :type biz: EndorsementBusiness
        :param affected_user: The ID of the user who is affected by the action.
        :type affected_user: int
        :param action: A string describing the administrative action performed.
        :type action: str
        :param data: Optional additional data related to the action.
        :type data: str, optional
        :param comment: Optional comment providing further context on the action.
        :type comment: str, optional
        :param user_id: The ID of the admin user who performed the action.
        :type user_id: Optional[int], optional
        :param session_id: The ID of the session in which the action occurred.
        :type session_id: Optional[int], optional

        :return: None
        """
        raise Exception("Not implemented")


    @abc.abstractmethod
    def arxiv_endorse(self, biz: "EndorsementBusiness") -> EndorsementModel | None:
        """
        Registers an endorsement for an arXiv user.

        :param self:
        :ppram biz: Endorsement business logic data
        :type biz: EndorsementBusiness
        :return: EndorsementModel or None - this is the new one
        :rtype: bool
        """
        raise Exception("Not implemented")


    @abc.abstractmethod
    def get_existing_endorsement(self, biz: "EndorsementBusiness") -> EndorsementModel | None:
        """
        Find existing endorsement from the endorser.

        :param self:

        :ppram biz: Endorsement business logic data
        :type biz: EndorsementBusiness
        :return: EndorsementModel or None - this is the existing one
        """
        raise Exception("Not implemented")


# Some magic values
arXiv_endorsement_window: [timedelta] = [timedelta(days=365 * 5 + 1), timedelta(days=30 * 3)]

class EndorsementBusiness:
    accessor: EndorsementAccessor
    endorsement_code: EndorsementCodeModel
    ensorseR: UserModel
    canon_archive: str        # Normalized archive
    canon_subject_class: str  # Normalized subject class
    session_id: str           # Tapir session ID
    endorsement_domain: Optional[EndorsementDomain]
    remote_host_ip: str
    remote_host_name: str
    audit_timestamp: datetime
    # admin_user_id: Optional[str]
    tracking_cookie: str # $_tracking_cookie =$_COOKIE["M4_TRACKING_COOKIE_NAME"];
    endorsement_type: EndorsementType
    total_points: int
    public_reason: bool
    endorsements: List[EndorsementWithEndorser]
    valid_endorsements: List[EndorsementWithEndorser]

    outcome: EndorsementOutcomeModel

    def __init__(self, accessor: EndorsementAccessor,
                 endorsement_code: EndorsementCodeModel,
                 endorseR: UserModel,
                 endorseE: PublicUserModel,
                 endorsement_request: EndorsementRequestModel,
                 session_id: str,
                 remote_host_ip: str,
                 remote_host_name: str,
                 audit_timestamp: datetime,
                 tracking_cookie: str,
                 ):
        super().__init__()
        self.accessor = accessor
        # Original endorsement code input
        self.endorsement_code = endorsement_code
        # Participants
        self.endorseR = endorseR

        assert(isinstance(endorsement_request, EndorsementRequestModel))

        self.canon_archive, self.canon_subject_class = canonicalize_category(endorsement_request.archive, endorsement_request.subject_class)

        self.session_id = session_id
        self.remote_host_ip = remote_host_ip
        self.remote_host_name = remote_host_name
        self.audit_timestamp = audit_timestamp
        # self.admin_user_id = admin_user_id
        self.tracking_cookie = tracking_cookie

        self.public_reason = False
        self.endorsements = []
        self.valid_endorsements = []

        self.outcome = EndorsementOutcomeModel(
            submitted=False,
            accepted = False,
            request_acceptable = False,
            submit_acceptable = False,
            reason = "",
            endorsement = None,
            endorsement_request = endorsement_request,
            endorsee = endorseE)

        self.outcome.accepted = False

        self.total_points = 0
        pass

    @property
    def endorseE(self) -> PublicUserModel | None:
        return self.outcome.endorsee

    @property
    def accepted(self) -> bool:
        return self.outcome.accepted

    @accepted.setter
    def accepted(self, accepted: bool) -> None:
        self.outcome.accepted = accepted

    @property
    def request_acceptable(self) -> bool:
        return self.outcome.request_acceptable

    @request_acceptable.setter
    def request_acceptable(self, acceptable: bool) -> None:
        self.outcome.request_acceptable = acceptable

    @property
    def submit_acceptable(self) -> bool:
        return self.outcome.submit_acceptable

    @submit_acceptable.setter
    def submit_acceptable(self, acceptable: bool) -> None:
        self.outcome.submit_acceptable = acceptable

    @property
    def submitted(self) -> bool:
        return self.outcome.submitted

    @submitted.setter
    def submitted(self, submitted: bool) -> None:
        self.outcome.submitted = submitted

    @property
    def reason(self) -> str:
        return self.outcome.reason

    @reason.setter
    def reason(self, reason):
        self.outcome.reason = reason

    @property
    def endorsement(self) -> EndorsementModel | None:
        return self.outcome.endorsement

    @property
    def endorsement_threshold(self) -> int:
        return 10

    @property
    def endorser_is_proxy_submitter(self) -> bool:
        return bool(self.endorseR.flag_proxy)

    def _is_owner_in_domain(self, user_id: int, domain: str, flag1: bool, flag2: bool):
        pass  # Implement check for owned papers

    def N_papers_to_endorse(self, archive: str, subject_class: str) -> int:
        pass  # Implement the required number of papers for endorsement

    @property
    def is_endorser_vetoed(self) -> bool:
        """Check if the endorseR has a veto status"""
        veto_status = self.endorseR.veto_status
        return veto_status != "ok"

    @property
    def window(self):
        return [self.audit_timestamp - t for t in arXiv_endorsement_window]

    @property
    def endorsement_request(self):
        return self.outcome.endorsement_request

    @property
    def archive(self):
        return self.outcome.endorsement_request.archive

    @property
    def subject_class(self):
        return self.outcome.endorsement_request.subject_class

    @property
    def point_value(self) -> int:
        return 10 if self.endorsement_code.positive else 0

    def reject(self, reason: str, public_reason: bool = False, submit_acceptable: bool = False, request_acceptable: bool = False) -> bool:
        self.submit_acceptable = submit_acceptable
        self.request_acceptable = request_acceptable
        self.public_reason = public_reason
        self.reason = reason
        return self.submit_acceptable and self.request_acceptable

    def accept(self, reason: str, public_reason: bool = True, submit_acceptable: bool = True, request_acceptable: bool = True) -> bool:
        self.submit_acceptable = submit_acceptable
        self.request_acceptable = request_acceptable
        self.public_reason = public_reason
        self.reason = reason
        return self.submit_acceptable and self.request_acceptable


    def is_owner_in_domain(self, user_id: str, domain: str, require_author: bool) -> List[PaperProps]:
        papers = self.accessor.get_papers_by_user(user_id, domain, self.window, require_author=require_author)
        return papers

    def _find_existing_endorsement(self):
        existing_endorsement = self.accessor.get_existing_endorsement(self)
        self.outcome.endorsement = existing_endorsement
        self.submitted = existing_endorsement is not None

    def _find_endorsements(self):
        self.endorsements = self.accessor.get_endorsements(str(self.endorseE.id), self.archive, self.subject_class)
        if self.archive != self.canon_archive and self.subject_class != self.canon_subject_class:
            self.endorsements = self.endorsements + self.accessor.get_endorsements(str(self.endorseE.id), self.canon_archive, self.canon_subject_class)
        self.valid_endorsements = [endorsement for endorsement in self.endorsements if endorsement.point_value and endorsement.flag_valid]


    def can_submit(self) -> bool:
        """
        This is about the endorser is ablet to submit an endorsement.
        """
        self._find_existing_endorsement()

        if self.submitted:
            self.submit_acceptable = False
            return self.reject("You have submitted an endorsement", public_reason=True)

        # self.accepted = False  # This is not strictly true but set the state

        # Check if the endorseR has a veto status
        if self.is_endorser_vetoed:
            self.submit_acceptable = False
            return self.reject("This endorsing user's ability to endorse has been suspended by administrative action.")

        if self.endorser_is_proxy_submitter:
            self.submit_acceptable = False
            return self.reject("Proxy submitters are not allowed to endorse.")

        category = self.accessor.get_category(self.canon_archive, self.canon_subject_class)
        if not category:
            category = self.accessor.get_category(self.archive, self.subject_class)
            if not category:
                return self.reject("We don't issue endorsements for non-definitive categories - no such category.", public_reason=True)

        elif not category.definitive:
            return self.reject("We don't issue endorsements for non-definitive categories.", public_reason=True)

        endorsement_domain = self.accessor.get_domain_info(category)
        if not endorsement_domain:
            return self.reject( "We don't issue endorsements for non-definitive categories - no such domain.", public_reason=True)

        self.endorsement_domain = endorsement_domain

        #
        if endorsement_domain.endorse_all == "y":
            category = pretty_category(self.archive, self.subject_class)
            return self.accept(f"Everyone gets an autoendorsement for category {category}.")

        # ARXIVDEV-3461 - if this endorsement domain has the mod_endorse_all field
        # enabled, then any moderator within that domain should be able to endorse
        # within that domain (not just their moderated category)
        if endorsement_domain.mods_endorse_all == "y" and self.accessor.is_moderator(self.endorseR.id, self.endorsement_request.archive, None):
            return self.accept(f"Endorser {self.endorseR.username} is a moderator in {self.endorsement_request.archive}.")

        if self.accessor.is_moderator(self.endorseR.id, self.endorsement_request.archive, self.endorsement_request.subject_class):
            category = pretty_category(self.archive, self.subject_class)
            return self.accept(f"Endorser {self.endorseR.username} is a moderator in {category}.")

        # can submit?
        endorsee = self.accessor.get_user(str(self.endorseE.id))
        if endorsee is None:
            raise HTTPException(status_code=500, detail="Endorsee is not found")

        if endorsee.veto_status == "no-upload":
            # Endorser is okay but endorsee is not
            return self.reject("Requesting user's ability to upload has been suspended.", submit_acceptable=True)

        # check 1 - has_endorsements
        self._find_endorsements()

        # check 2 - auto endorsed
        # First test to see if there is a reason not to autoendorse (questionable category, marked invalid, is flagged)
        questionable_category = self.accessor.get_questionable_categories(self.canon_archive,
                                                                          self.canon_subject_class)

        if questionable_category:
            invalids = [
                endorsement for endorsement in self.endorsements if
                (not endorsement.flag_valid) and endorsement.type == "auto" and (
                        (endorsement.archive == self.canon_archive and endorsement.subject_class == self.canon_subject_class) or
                        (endorsement.archive == self.archive and endorsement.subject_class == self.subject_class))
            ]
            if invalids:
                return self.reject("User's autoendorsement has been invalidated (strong case).", submit_acceptable=True)

        else:
            invalidated = [endorsement for endorsement in self.endorsements if
                           not endorsement.flag_valid and endorsement.type == 'auto']
            # if not invalidated: ? REVIEW THIS
            if invalidated:
                return self.reject("User's autoendorsement has been invalidated.", submit_acceptable=True)

            if endorsee.flag_suspect:
                return self.reject("User is flagged, does not get autoendorsed.", submit_acceptable=True)

        # Now we have done tests to see if there are reasons not to autoendorse this
        # user, do tests to find out whether we should...
        # (I don't think this has nothing to do with submitting endorsement.)
        papers = self.accessor.get_papers_by_user(str(self.endorseE.id), endorsement_domain.endorsement_domain,
                                                  self.window, require_author=False)

        # I'm not quite sure of this section
        not_enough_papers = (len(papers) < endorsement_domain.papers_to_endorse)
        not_academic_email = endorsement_domain.endorse_email == "y" and (
            not self.accessor.is_academic_email(self.endorseE.email)[0])
        does_not_accept_email = endorsement_domain.endorse_email != "y"
        if not_enough_papers and not_academic_email and does_not_accept_email:
            category = pretty_category(self.endorsement_request.archive, self.endorsement_request.subject_class)
            reason = f"User is not allowed to submit to {category}."
            if not_enough_papers:
                reason = reason + " Not enough papers endorsed."
            if does_not_accept_email:
                reason = reason + " The domain does not accept email based endorsement."
            if not not_academic_email:
                reason = reason + " The submitter email is not academic institution."
            return self.reject(reason)

        # ==============================================================================================================
        # Look at the endorser
        papers = self.accessor.get_papers_by_user(str(self.endorseR.id),
                                                  endorsement_domain.endorsement_domain,
                                                  [None, None], require_author=False)

        if not papers:
            category = pretty_category(self.endorsement_request.archive, self.endorsement_request.subject_class)
            # The original message did not make any sense to me.
            # Added the first part of error message.
            reason = f"Endorser does not have enough registered papers in {category} in the 3mo-5yr window."
            return self.reject(reason, request_acceptable=True, public_reason=True)

        authored_papers = [paper for paper in papers if paper.flag_author]
        not_authored_papers = [paper for paper in papers if not paper.flag_author]

        N_papers = endorsement_domain.papers_to_endorse

        if len(authored_papers) >= N_papers:
            # This also makes very little sense.
            titles = [paper.title for paper in authored_papers[:N_papers]]
            return self.accept(f"Endorser is author of: {', '.join(titles)}.")

        if len(papers) >= N_papers:
            # This also makes very little sense.
            titles = [paper.title for paper in not_authored_papers]
            return self.reject(f"Not Author of: {', '.join(titles)}.", public_reason=True, request_acceptable=True)

        category = pretty_category(self.canon_archive, self.canon_subject_class)
        reason = f"User must be the registered author of {N_papers} registered papers to endorse for {category}"
        reason = reason + f" but has only {len(authored_papers)} in the 3mo-5yr window"
        if len(papers) > len(authored_papers):
            reason += f" (user is non-author of {len(papers) - len(authored_papers)})"
        reason = reason + "."
        return self.reject(reason, request_acceptable=True)


    def submit_endorsement(self) -> EndorsementModel | None:
        result = self.accessor.arxiv_endorse(self)
        return result

