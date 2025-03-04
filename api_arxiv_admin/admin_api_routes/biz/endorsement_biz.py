import abc
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session, aliased
from arxiv.db.models import (Endorsement, Category, EndorsementDomain, TapirNickname, QuestionableCategory,)
from datetime import datetime, timedelta
from pydantic import BaseModel
from ..endorsement_requsets import EndorsementRequestModel
from ..endorsements import EndorsementType, EndorsementCodeModel
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
    dated: Optional[datetime]


class EndorsementAccessor:
    @abc.abstractmethod
    def is_moderator(self, user_id: int, archive: str, subject_class: Optional[str] = None) -> bool:
        return False

    @abc.abstractmethod
    def get_category(self, archive: str, subject_class: str) -> Category | None:
        return None

    @abc.abstractmethod
    def get_domain_info(self, category: Category) -> EndorsementDomain | None:
        """Gets Endorsement domain from category"""
        return None

    @abc.abstractmethod
    def get_endorsements(self, user_id: str, canon_archive: str, canon_subject_class: str) -> List[EndorsementWithEndorser]:
        """SELECT endorser_id, point_value, type FROM arXiv_endorsements
                           WHERE endorsee_id = :user_id AND archive = :archive AND subject_class = :subject_class AND flag_valid = 1"""
        return []

    @abc.abstractmethod
    def get_questionable_categories(self, archive: str, subject_class: str) -> List[QuestionableCategory]:
        return []

    @abc.abstractmethod
    def get_papers_by_user(self, user_id: str, domain: str, window: [datetime | None],require_author: bool = True) -> List[PaperProps]:
        return []

    @abc.abstractmethod
    def is_academic_email(self, email: str) -> bool:
        return False

    @abc.abstractmethod
    def get_user(self, id: str) -> UserModel | None:
        pass

    @abc.abstractmethod
    def tapir_audit_admin(self,
                          endorsement: "EndorsementBusiness",
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
        pass

    @abc.abstractmethod
    def arxiv_endorse(self, endorsement: "EndorsementBusiness") -> Endorsement | None:
        """
        Registers an endorsement for an arXiv user.

        :param self:
        :param endorsement: An instance of ArxivEndorsementParams containing endorsement details.
        :type endorsement: ArxivEndorsementParams
        :return: True if the endorsement was successfully recorded, False otherwise.
        :rtype: bool
        """
        pass


# Some magic value somewhere
arXiv_endorsement_window: [timedelta] = [timedelta(days=180), timedelta(days=0)]

class EndorsementBusiness:
    accessor: EndorsementAccessor
    endorsement_code: EndorsementCodeModel
    ensorseR: UserModel
    ensorseE: UserModel
    endorsement_request: EndorsementRequestModel
    canon_archive: str        # Normalized archive
    canon_subject_class: str  # Normalized subject class
    session_id: str           # Tapir session ID
    outcome: dict
    endorsement_domain: Optional[EndorsementDomain]
    remote_host_ip: str
    remote_host_name: str
    audit_timestamp: datetime
    # admin_user_id: Optional[str]
    tracking_cookie: str # $_tracking_cookie =$_COOKIE["M4_TRACKING_COOKIE_NAME"];
    endorsement_type: EndorsementType

    def __init__(self, accessor: EndorsementAccessor,
                 endorsement_code: EndorsementCodeModel,
                 endorseR: UserModel,
                 endorseE: UserModel,
                 endorsement_request: EndorsementRequestModel,
                 session_id: str,
                 remote_host_ip: str,
                 remote_host_name: str,
                 audit_timestamp: datetime,
                 tracking_cookie: str,
                 ):
        self.accessor = accessor
        # Original endorsement code input
        self.endorsement_code = endorsement_code
        # Participants
        self.endorseR = endorseR
        self.endorseE = endorseE

        self.endorsement_request = endorsement_request

        self.canon_archive, self.canon_subject_class = canonicalize_category(endorsement_request.archive, endorsement_request.subject_class)

        self.outcome = {
            "accepted": False,
            "public_reason": False,
            "reason": "",
            "total_points": 0,
        }

        self.session_id = session_id
        self.remote_host_ip = remote_host_ip
        self.remote_host_name = remote_host_name
        self.audit_timestamp = audit_timestamp
        # self.admin_user_id = admin_user_id
        self.tracking_cookie = tracking_cookie
        pass

    @property
    def accepted(self) -> bool:
        return self.outcome["accepted"]

    @accepted.setter
    def accepted(self, accepted: bool) -> None:
        self.outcome["accepted"] = accepted

    @property
    def public_reason(self) -> bool:
        return self.outcome["public_reason"]

    @public_reason.setter
    def public_reason(self, public_reason: bool) -> None:
        self.outcome["public_reason"] = public_reason

    @property
    def reason(self) -> str:
        return self.outcome["reason"]

    @reason.setter
    def reason(self, reason):
        self.outcome["reason"] = reason

    @property
    def total_points(self) -> int:
        return self.outcome["total_points"]

    @total_points.setter
    def total_points(self, total_points: int) -> None:
        self.outcome["total_points"] = total_points

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
    def endorser_veto_state(self) -> bool:
        """Check if the endorseR has a veto status"""
        veto_status = self.endorseR.veto_status
        if veto_status != "ok":
            self.accepted = True
            self.reason = "This endorsing user's ability to endorse has been suspended by administrative action."
            return False
        return True

    @property
    def window(self):
        return [self.audit_timestamp - t for t in arXiv_endorsement_window]


    def reject(self, public_reason: bool, reason: str) -> bool:
        self.accepted = False
        self.public_reason = public_reason
        self.reason = reason
        return self.accepted

    def accept(self, public_reason: bool, reason: str) -> bool:
        self.accepted = True
        self.public_reason = public_reason
        self.reason = reason
        return self.accepted

    def is_owner_in_domain(self, user_id: str, domain: str, require_author: bool) -> List[PaperProps]:
        papers = self.accessor.get_papers_by_user(user_id, domain, self.window, require_author=require_author)
        return papers


    def can_endorse(self) -> bool:
        # endorsement_category = canonicalize_category(self.endorsement_archive, self.endorsement_subject_class)

        # Check if the endorseR has a veto status
        if not self.endorser_veto_state:
            return self.reject(False, "This endorsing user's ability to endorse has been suspended by administrative action.")

        if self.endorser_is_proxy_submitter:
            return self.reject(True, "Proxy submitters are not allowed to endorse.")

        category = self.accessor.get_category(self.canon_archive, self.canon_subject_class)
        if not category:
            return self.reject(True,"We don't issue endorsements for non-definitive categories - no such category.")

        elif category.definitive == 0:
            return self.reject(True, "We don't issue endorsements for non-definitive categories")

        endorsement_domain = self.accessor.get_domain_info(category)
        if not endorsement_domain:
            return self.reject(True, "We don't issue endorsements for non-definitive categories - no such domain.")

        self.endorsement_domain = endorsement_domain

        #
        if endorsement_domain.endorse_all == "y":
            category = pretty_category(self.endorsement_request.archive, self.endorsement_request.subject_class)
            return self.accept(True, f"Everyone gets an autoendorsement for category {category}.")

        # ARXIVDEV-3461 - if this endorsement domain has the mod_endorse_all field
        # enabled, then any moderator within that domain should be able to endorse
        # within that domain (not just their moderated category)
        if endorsement_domain.mods_endorse_all == "y" and self.accessor.is_moderator(self.endorseR.id, self.endorsement_request.archive, None):
            return self.accept(True, f"User is a moderator in {self.endorsement_request.archive}")

        if self.accessor.is_moderator(self.endorseR.id, self.endorsement_request.archive, self.endorsement_request.subject_class):
            category = pretty_category(self.endorsement_request.archive, self.endorsement_request.subject_class)
            return self.accept(True, f"User is a moderator in {category}")

        # The code below works to limit endorsement privs to only those authors
        # that are allowed to submit to a category (doesn't seem to make any
        # sense to be able to endorse when you can't submit). However, it doesn't
        # make sense to put this online until the code in who-can-endorse.php
        # is also updated so that the arXiv_can_endorse table is correct and
        # /auth/show-endorsers shows correct information [Simeon/2009-12-10]

        # can submit?
        if self.endorseE.veto_status == "no-upload":
            return self.reject(False, "Requesting user's ability to upload has been suspended.")

        # Go through existing endorsements
        # not sure canon_FOOs are correct.
        endorsements = self.accessor.get_endorsements(self.endorseE.user_id, self.canon_archive, self.canon_subject_class)
        valid_endorsements = [endorsement for endorsement in endorsements if endorsement.point_value and endorsement.flag_valid]

        has_endorsements = False
        reason = ""
        endorsers = []
        #
        # One of next two need to set has_endorsements to True
        # otherwise, this is rejected

        # check 1
        if len(valid_endorsements) > 0:
            total_points = sum(endorsement.point_value for endorsement in valid_endorsements)
            if total_points < self.endorsement_threshold:
                return self.reject(False, f"User has only negative endorsements for this category ({total_points}/{self.endorsement_threshold})")

            endorsers = [endorser.endorser_username for endorser in valid_endorsements]

            for endorsement in valid_endorsements:
                match endorsement.type:
                    case "user":
                        reason = reason + f"User has been endorsed by {', '.join(endorsers)}\n"
                    case "auto":
                        reason = reason + "User has been autoendorsed\n"
                    case "admin":
                        reason = reason + f"Admin endorsement from {', '.join(endorsers)}\n"
                    case _:
                        reason = reason + "Unknown endorsement type\n"
            self.total_points = total_points
            has_endorsements = True

        # check 2
        questionable_category = self.accessor.get_questionable_categories(self.canon_archive, self.canon_subject_class)

        if questionable_category:
            invalids = [
                endorsement for endorsement in endorsements if (not endorsement.flag_valid) and endorsement.type == "auto" and endorsement.archive == self.canon_archive and endorsement.subject_class == self.canon_subject_class
            ]
            if invalids:
                return self.reject(False, "User's autoendorsement has been invalidated (strong case).")
            has_endorsements = True
        else:
            invalidated = [endorsement for endorsement in endorsements if not endorsement.flag_valid and endorsement.type == 'auto']
            if not invalidated:
                has_endorsements = True
            else:
                 season = "User's autoendorsement has been invalidated."

            if not self.endorseE.is_suspect:
                has_endorsements = True
            else:
                reason = "User is flagged, does not get autoendorsed."

        # Now we have done tests to see if there are reasons not to autoendorse this
        # user, do tests to find out whether we should...
        papers = self.accessor.get_papers_by_user(str(self.endorseE.id), endorsement_domain.endorsement_domain,
                                                  self.window, require_author=False)

        if len(papers) > endorsement_domain.papers_to_endorse:  # Required papers for autoendorsement. If users paper count is greater than or equal to the archive limit....
            has_endorsements = True                #  auto endorse for this archive.category

        # If the endorsement domain accepts all academic email, good.
        if endorsement_domain.endorse_email == "y":
            if self.accessor.is_academic_email(self.endorseE.email):
                has_endorsements = True

        if not has_endorsements:
            category = pretty_category(self.endorsement_request.archive, self.endorsement_request.subject_class)
            return self.reject(False, f"User is not allowed to submit to {category}.")

        # ==============================================================================================================
        # Look at the endorsers
        papers = self.accessor.get_papers_by_user(str(self.endorseR.id),
                                                  endorsement_domain.endorsement_domain,
                                                  [None, None], require_author=False)

        if not papers:
            category = pretty_category(self.endorsement_request.archive, self.endorsement_request.subject_class)
            return self.reject(False, f"User has no registered papers in {category} in the 3mo-5yr window.")

        authored_papers = [paper for paper in papers if paper.flag_author]
        not_authored_papers = [paper for paper in papers if not paper.flag_author]

        N_papers = endorsement_domain.papers_to_endorse

        if len(authored_papers) >= N_papers:
            return self.accept(False, f"Author of: {', '.join(map(str, authored_papers[:N_papers]))}")

        if len(papers) >= N_papers:
            return self.reject(True, f"Not Author of: {', '.join(map(str, not_authored_papers))}")

        category = pretty_category(self.canon_archive, self.canon_subject_class)
        reason = f"User must be the registered author of {N_papers} registered papers to endorse for {category} "
        reason = reason + f"but has only {len(authored_papers)} in the 3mo-5yr window"
        if len(papers) > len(authored_papers):
            reason += f" (user is non-author of {len(papers) - len(authored_papers)})"
        return self.reject(False, reason)


    def endorse(self) -> Endorsement | None:
        return self.accessor.arxiv_endorse(self)
