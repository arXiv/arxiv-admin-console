from enum import Enum
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from arxiv.db.models import (
    Endorsement, EndorsementsAudit, Demographic, EndorsementRequest,
    TapirAdminAudit
)
from datetime import datetime
from pydantic import BaseModel
from .. import datetime_to_epoch


class ArxivEndorsementParams(BaseModel):
    issued_when: datetime
    endorser_id: Optional[int]  # Allow None for automatic endorsements
    endorsee_id: int
    archive: str
    subject_class: str
    point_value: int
    type_: Optional[Enum("user", "admin", "auto")] = None
    comment: str
    knows_personally: bool
    seen_paper: bool
    request_id: Optional[int] = None
    session_id: Optional[int] = None # audit - tapir session id
    admin_user_id: int    # audit - admin who did the op
    remote_addr: str      # audit
    remote_host: str      # audit
    tracking_cookie: str  # audit


def tapir_audit_admin(session: Session,
                      endorsement: ArxivEndorsementParams,
                      affected_user: int,
                      action: str,
                      data: str = "",
                      comment: str = "",
                      user_id: Optional[int] = None,
                      session_id: Optional[int] = None):
    """
    Logs administrative actions in the `tapir_admin_audit` table.

    This function records administrative actions taken on a user within
    the system, storing relevant metadata such as the acting admin,
    affected user, session details, and additional comments.

    :param session: The database session to use for logging the audit entry.
    :type session: Session
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
    session_id = session_id or None  # Assuming session_id handling elsewhere
    user_id = user_id or None  # Assuming user_id handling elsewhere

    audit_entry = TapirAdminAudit(
        log_date=datetime_to_epoch(endorsement.issued_when),
        session_id=session_id,
        ip_addr=endorsement.remote_addr,
        admin_user=endorsement.admin_user_id,
        affected_user=affected_user,
        tracking_cookie=endorsement.tracking_cookie,
        action=action,
        data=data,
        comment=comment,
        remote_host=endorsement.remote_host
    )

    session.add(audit_entry)


def arxiv_endorse(session: Session, endorsement: ArxivEndorsementParams) -> bool:
    """
    Registers an endorsement for an arXiv user.

    :param session: The database session to use for the transaction.
    :type session: Session
    :param endorsement: An instance of ArxivEndorsementParams containing endorsement details.
    :type endorsement: ArxivEndorsementParams
    :return: True if the endorsement was successfully recorded, False otherwise.
    :rtype: bool
    """

    # Ensure category consistency
    canonical_category = f"{endorsement.archive}.{endorsement.subject_class}" if endorsement.subject_class else endorsement.archive

    try:
        #
        endorser_is_suspect = False

        if endorsement.endorser_id is None:
            previous_endorsements = session.query(Endorsement).filter(
                Endorsement.endorser_id.is_(None),
                Endorsement.endorsee_id == endorsement.endorsee_id,
                Endorsement.archive == endorsement.archive,
                Endorsement.subject_class == endorsement.subject_class
            ).with_for_update().count()

            if previous_endorsements:
                session.rollback()
                return False
        else:
            endorser_is_suspect = session.query(Demographic.flag_suspect).filter(
                Demographic.user_id == endorsement.endorser_id
            ).scalar()

        # Insert endorsement record
        new_endorsement = Endorsement(
            endorser_id=endorsement.endorser_id,
            endorsee_id=endorsement.endorsee_id,
            archive=endorsement.archive,
            subject_class=endorsement.subject_class,
            flag_valid=True,
            type=endorsement.type_,
            point_value=endorsement.point_value,
            issued_when=datetime_to_epoch(endorsement.issued_when),
            request_id=endorsement.request_id
        )
        session.add(new_endorsement)
        session.flush()  # Ensure LAST_INSERT_ID is available

        # Insert audit record
        audit_entry = EndorsementsAudit(
            endorsement_id=new_endorsement.id,
            session_id=endorsement.session_id,
            remote_addr=endorsement.remote_addr,
            remote_host=endorsement.remote_host,
            tracking_cookie=endorsement.tracking_cookie,
            flag_knows_personally=endorsement.knows_personally,
            flag_seen_paper=endorsement.seen_paper,
            comment=endorsement.comment
        )
        session.add(audit_entry)

        # Handle suspect endorsements
        if endorsement.point_value and endorser_is_suspect:
            session.query(Demographic).filter(
                Demographic.user_id == endorsement.endorsee_id
            ).update({Demographic.flag_suspect: True})

            tapir_audit_admin(
                session,
                endorsement,
                affected_user=endorsement.endorsee_id,
                action="endorsed-by-suspect",
                data=f"{endorsement.endorser_id} {canonical_category} {new_endorsement.id}",
                comment="",
                user_id=endorsement.admin_user_id
            )

        if not endorsement.point_value:
            session.query(Demographic).filter(
                Demographic.user_id == endorsement.endorsee_id
            ).update({Demographic.flag_suspect: True})

            tapir_audit_admin(
                session,
                endorsement,
                affected_user=endorsement.endorsee_id,
                action="got-negative-endorsement",
                data=f"{endorsement.endorser_id} {canonical_category} {new_endorsement.id}",
                comment="",
                user_id=-1
            )

        # Update request if applicable
        if endorsement.request_id:
            session.query(EndorsementRequest).filter(
                EndorsementRequest.request_id == endorsement.request_id
            ).update({
                EndorsementRequest.point_value: EndorsementRequest.point_value + endorsement.point_value
            })

        session.commit()
        return True

    except IntegrityError:
        session.rollback()
        return False

    except Exception as e:
        session.rollback()
        raise e
