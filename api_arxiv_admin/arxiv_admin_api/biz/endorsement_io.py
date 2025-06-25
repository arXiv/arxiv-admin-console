import logging
from datetime import datetime, UTC
from typing import Optional, List, Tuple

from fastapi import HTTPException, status
from sqlalchemy import and_, or_, between, text, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from arxiv.db.models import (
    Endorsement, EndorsementsAudit, Demographic, EndorsementRequest,
    TapirAdminAudit, t_arXiv_moderators, Category, EndorsementDomain, TapirUser,
    QuestionableCategory, Document, t_arXiv_in_category, PaperOwner,
    t_arXiv_black_email, t_arXiv_white_email
)

from .. import datetime_to_epoch, VERY_OLDE
from ..dao.endorsement_model import EndorsementType, EndorsementModel
from ..user import UserModel

from .endorsement_biz import (EndorsementAccessor, EndorsementWithEndorser, PaperProps,
                              pretty_category, EndorsementBusiness)

logger = logging.getLogger(__name__)

class EndorsementDBAccessor(EndorsementAccessor):
    session: Session

    def __init__(self, sesseon: Session):
        self.session = sesseon

    def is_moderator(self, user_id: int, archive: str, subject_class: Optional[str] = None) -> bool:
        query = self.session.query(t_arXiv_moderators).filter(and_(
            t_arXiv_moderators.c.user_id == user_id,
            t_arXiv_moderators.c.archive == archive
        ))

        if subject_class and subject_class != "*":
            query = query.filter(or_(
                t_arXiv_moderators.c.subject_class == subject_class,
                t_arXiv_moderators.c.subject_class == "",
                t_arXiv_moderators.c.subject_class is None))
            pass
        return bool(query.scalar())

    def get_category(self, archive: str, subject_class: str | None) -> Category | None:
        subject_class = subject_class if subject_class else ""
        return self.session.query(Category).filter(
            and_(
                Category.archive == archive,
                Category.subject_class == subject_class,
            )).one_or_none()


    def get_domain_info(self, category: Category) -> EndorsementDomain | None:
        """Gets Endorsement domain from category"""
        return self.session.query(EndorsementDomain).filter(EndorsementDomain.endorsement_domain == category.endorsement_domain).one_or_none()

    def get_endorsements(self, user_id: str, canon_archive: str, canon_subject_class: str) -> List[EndorsementWithEndorser]| None:
        """SELECT endorser_id, point_value, type FROM arXiv_endorsements
                           WHERE endorsee_id = :user_id AND archive = :archive AND subject_class = :subject_class"""
        es = EndorsementWithEndorser.base_select(self.session).filter(and_(
            Endorsement.endorsee_id == user_id,
            Endorsement.archive == canon_archive,
            Endorsement.subject_class == canon_subject_class)).all()
        return [ EndorsementWithEndorser.model_validate(endorsement) for endorsement in es]

    def get_questionable_categories(self, archive: str, subject_class: str) -> List[QuestionableCategory]:
        return self.session.query(QuestionableCategory).filter(
            and_(
                QuestionableCategory.archive == archive,
                QuestionableCategory.subject_class == subject_class,
            )
        ).all()

    def get_papers_by_user(self, user_id: str, domain: str, window: [datetime | None], require_author: bool = True) -> List[PaperProps]:
        query = (
            self.session.query(
                PaperOwner.document_id,
                PaperOwner.flag_author,
                Document.title
            )
            .join(t_arXiv_in_category, PaperOwner.document_id == t_arXiv_in_category.c.document_id)
            .join(
                Category,
                and_(
                    Category.archive == t_arXiv_in_category.c.archive,
                    Category.subject_class == t_arXiv_in_category.c.subject_class
                )
            )
            .join(Document, PaperOwner.document_id == Document.document_id)
            .filter(
                PaperOwner.user_id == int(user_id),
                PaperOwner.valid == 1,
                Category.endorsement_domain == domain
            )
        )

        # Apply additional filters
        if require_author:
            query = query.filter(PaperOwner.flag_author.is_(True))

        if window[0] or window[1]:
            query = query.filter(between(Document.dated,
                                         datetime_to_epoch(window[0], VERY_OLDE),
                                         datetime_to_epoch(window[1], datetime.now(UTC))))

        query = query.group_by(PaperOwner.document_id)

        # Convert query results into Pydantic models using model_validate
        results = [PaperProps.model_validate(row) for row in query.all()]
        return results

    def is_academic_email(self, email: str) -> Tuple[bool, str]:
        """Checks if an email is academic based on blacklist and whitelist patterns."""

        # Check blacklist first
        blacklist_query = select(t_arXiv_black_email.c.pattern).where(
            text(f"'{email}' LIKE pattern")  # Match the email against stored patterns
        )
        blacklisted_pattern = self.session.execute(blacklist_query).scalar()

        if blacklisted_pattern:
            return (False, f"{email} looks like a non-academic e-mail address. (Matches '{blacklisted_pattern}')")

        # Check whitelist
        whitelist_query = select(t_arXiv_white_email.c.pattern).where(
            text(f"'{email}' LIKE pattern")  # Match the email against stored patterns
        )
        whitelisted_pattern = self.session.execute(whitelist_query).scalar()

        if whitelisted_pattern:
            return (True, f"{email} looks like an academic e-mail address. (Matches '{whitelisted_pattern}')")

        return (False, f"{email} looks like a non-academic e-mail address. (Matches no patterns)")

    def get_user(self, id: str) -> UserModel | None:
        # @ignore-types
        user = UserModel.base_select(self.session).filter(TapirUser.user_id == int(id)).one_or_none()
        if user:
            return UserModel.to_model(user)
        return None

    def tapir_audit_admin(self,
                          endorsement: EndorsementBusiness,
                          affected_user: int = 0,
                          action: str = "",
                          data: str = "",
                          comment: str = "",
                          user_id: Optional[int] = None,
                          session_id: Optional[int] = None):
        """
        Logs administrative actions in the `tapir_admin_audit` table.

        This function records administrative actions taken on a user within
        the system, storing relevant metadata such as the acting admin,
        affected user, session details, and additional comments.

        :param self:
        :param endorsement:
        :type endorsement: EndorsementBusiness, the source of decision making
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
        :param session_id: The ID of the session in which the action occurred. Tapir session ID
        :type session_id: Optional[int], optional

        :return: None

# by default we get $session_id and $user_id out of $auth,  but that won't work under some circumstances,
# such as when a user becomes another user,  then we need to pass them over

function tapir_audit_admin($affected_user,$action,$data="",$comment="",$user_id="",$session_id="") {
	global $auth;

	$session_id=($session_id==="") ? $auth->session_id : $session_id;
	$user_id=($user_id==="") ? $auth->user_id : $user_id;

	$_session_id=addslashes($session_id);
   if (!$session_id) {
      $_session_id="null";
   };

	$_ip_addr=addslashes($_SERVER["REMOTE_ADDR"]);
    $_remote_host=addslashes($_SERVER["REMOTE_HOST"]);
	$_admin_user=($user_id==-1) ? "null" : "'".addslashes($user_id)."'";
	$_affected_user=addslashes($affected_user);
	$_tracking_cookie=$_COOKIE["M4_TRACKING_COOKIE_NAME"];
	$_action=addslashes($action);
	$_data=addslashes($data);
	$_comment=addslashes($comment);

	$auth->conn->query("INSERT INTO tapir_admin_audit (log_date,session_id,ip_addr,admin_user,affected_user,tracking_cookie,action,data,comment,remote_host) VALUES ($auth->timestamp,$_session_id,'$_ip_addr',$_admin_user,'$_affected_user','$_tracking_cookie','$_action','$_data','$_comment','$_remote_host')");
};
        """

        audit_entry = TapirAdminAudit(
            log_date = datetime_to_epoch(endorsement.audit_timestamp, datetime.now(UTC)),
            session_id=session_id,
            ip_addr=endorsement.remote_host_ip,
            admin_user=endorsement.endorseR.id if endorsement.endorseR.is_admin else None,
            affected_user=affected_user,
            tracking_cookie=endorsement.tracking_cookie,
            action=action,
            data=data,
            comment=comment,
            remote_host=endorsement.remote_host_name
        )
        self.session.add(audit_entry)


    def arxiv_endorse(self, endorsement: EndorsementBusiness) -> EndorsementModel | None:
        """
        Registers an endorsement for an arXiv user.

        :param self:
        :param endorsement: An instance of ArxivEndorsementParams containing endorsement details.
        :type endorsement: ArxivEndorsementParams
        :return: True if the endorsement was successfully recorded, False otherwise.
        :rtype: bool
        """
        session = self.session # sugar
        # Ensure category consistency
        canon_archive, canon_subject_class = endorsement.canon_archive, endorsement.canon_subject_class
        canonical_category = pretty_category(canon_archive, canon_subject_class)
        endorser_is_suspect = False
        endorser_id = endorsement.endorseR.id if endorsement.endorseR.id else None
        endorsement_type: EndorsementType

        try:
            # In what circumstance there is no endorser known? Is this because "auto endorse"?
            if endorser_id is None:
                endorsement_type = EndorsementType.auto
                # My guess is that, if there is an auto endorse already, no need for another auto endorse.
                previous_endorsements = session.query(Endorsement).filter(
                    Endorsement.endorser_id.is_(None),
                    Endorsement.endorsee_id == endorsement.endorseE.id,
                    Endorsement.archive == endorsement.canon_archive,
                    Endorsement.subject_class == endorsement.canon_subject_class
                ).with_for_update().count()

                if previous_endorsements:
                    session.rollback()
                    return None
            else:
                endorser_is_suspect = endorsement.endorseR.flag_suspect
                endorsement_type = EndorsementType.admin if endorsement.endorseR.is_admin else EndorsementType.user

            # Insert endorsement record
            new_endorsement = Endorsement(
                endorser_id=endorser_id,
                endorsee_id=endorsement.endorseE.id,
                archive=endorsement.canon_archive,
                subject_class=endorsement.canon_subject_class,
                flag_valid=True,
                type=endorsement_type.value,
                point_value=endorsement.point_value if endorsement.endorsement_code.positive else 0,
                issued_when=datetime_to_epoch(endorsement.audit_timestamp, datetime.now(UTC)),
                request_id=endorsement.endorsement_request_id
            )
            session.add(new_endorsement)
            session.flush()
            session.refresh(new_endorsement)

            # Now increase the total by this endorsement
            if endorsement.endorsement_code.positive:
                endorsement.total_points = endorsement.total_points + endorsement.point_value

            # Insert audit record
            session_id = int(endorsement.session_id) if endorsement.session_id else 0
            audit_entry = EndorsementsAudit(
                endorsement_id=new_endorsement.endorsement_id,
                session_id=session_id,
                remote_addr=endorsement.remote_host_ip,
                remote_host=endorsement.remote_host_name,
                tracking_cookie=endorsement.tracking_cookie,
                flag_knows_personally=endorsement.endorsement_code.knows_personally,
                flag_seen_paper=endorsement.endorsement_code.seen_paper,
                comment=endorsement.endorsement_code.comment
            )
            session.add(audit_entry)
            session.flush()

            # Handle suspect endorsements
            demographic: Demographic | None = session.query(Demographic).filter(Demographic.user_id == endorsement.endorseE.id).one_or_none()

            if endorsement.endorsement_code.positive and endorser_is_suspect:
                if demographic and demographic.flag_suspect != 1:
                    demographic.flag_suspect = 1
                    session.add(demographic)
                    session.flush()
                    session.refresh(demographic)

                self.tapir_audit_admin(
                    endorsement,
                    affected_user=endorsement.endorseE.id,
                    action="endorsed-by-suspect",
                    data=f"{endorsement.endorseE.id} {canonical_category} {new_endorsement.endorsement_id}",
                    comment="",
                    user_id=endorsement.endorseR.id,
                    session_id=session_id,
                )

            if not endorsement.endorsement_code.positive:
                if demographic and demographic.flag_suspect != 1:
                    demographic.flag_suspect = 1
                    session.add(demographic)
                    session.flush()
                    session.refresh(demographic)

                self.tapir_audit_admin(
                    endorsement,
                    affected_user=endorsement.endorseE.id,
                    action="got-negative-endorsement",
                    data=f"{endorsement.endorseR.id} {canonical_category} {new_endorsement.endorsement_id}",
                    comment="",
                    user_id=-1,
                    session_id=session_id,
                )

            # Update request if applicable
            if endorsement.endorsement_request and endorsement.endorsement_request.id and endorsement.point_value:
                e_req: EndorsementRequest | None = session.query(EndorsementRequest).filter(EndorsementRequest.request_id == endorsement.endorsement_request.id).one_or_none()
                if e_req and e_req.point_value != endorsement.total_points:
                    e_req.point_value = endorsement.total_points
                    session.add(e_req)
                    session.flush()

            session.commit()
            session.refresh(new_endorsement)
            endorsement = EndorsementModel.base_select(session).filter(Endorsement.endorsement_id == new_endorsement.endorsement_id).one_or_none()
            return EndorsementModel.model_validate(endorsement)

        except IntegrityError as exc:
            logger.error("%s; endorse %s", __name__, str(exc))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

        except Exception as exc:
            logger.error("%s; endorse %s", __name__, str(exc))
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


    def get_existing_endorsement(self, biz: EndorsementBusiness) -> EndorsementModel | None:
        """
        Registers an endorsement for an arXiv user.

        :param self:
        :param biz: An instance of ArxivEndorsementParams containing endorsement details.
        :type biz: ArxivEndorsementParams
        :return: True if the endorsement was successfully recorded, False otherwise.
        :rtype: bool
        """
        endorser_id = biz.endorseR.id if biz.endorseR else None
        if endorser_id is None:
            return None
        session = self.session  # sugar

        try:
            endorsement = EndorsementModel.base_select(session).filter(
                Endorsement.endorser_id == endorser_id,
                Endorsement.endorsee_id == biz.endorseE.id,
                Endorsement.archive == biz.canon_archive,
                Endorsement.subject_class == biz.canon_subject_class
            ).one_or_none()
            if endorsement is None:
                return None
            return EndorsementModel.model_validate(endorsement)

        except Exception as exc:
            logger.error("%s; endorse %s", __name__, str(exc))
            raise
