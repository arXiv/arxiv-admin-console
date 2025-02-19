from typing import Optional

from sqlalchemy import Engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from arxiv.db.models import (
    Endorsement, EndorsementsAudit, Demographic, EndorsementRequest,
    TapirAdminAudit
)
from datetime import datetime


def tapir_audit_admin(session: Session,
                      affected_user: int,
                      action: str,
                      data: str = "",
                      comment: str = "",
                      user_id: Optional[int] = None,
                      session_id: Optional[int] = None):
    """
    Logs administrative actions in the tapir_admin_audit table.
    """
    session_id = session_id or None  # Assuming session_id handling elsewhere
    user_id = user_id or None  # Assuming user_id handling elsewhere

    audit_entry = TapirAdminAudit(
        log_date=datetime.utcnow(),
        session_id=session_id,
        ip_addr="REMOTE_ADDR",  # Replace with actual request data
        admin_user=user_id if user_id != -1 else None,
        affected_user=affected_user,
        tracking_cookie="TRACKING_COOKIE_NAME",
        action=action,
        data=data,
        comment=comment,
        remote_host="REMOTE_HOST"  # Replace with actual request data
    )

    session.add(audit_entry)


def arxiv_endorse(session: Session,
            endorser_id: int,
            endorsee_id: int,
            archive: str,
            subject_class: str,
            point_value: int,
            type_: str,
            comment: str, knows_personally: bool,
            seen_paper, request_id=None):
    """
    Endorse a user in the arXiv system.
    """

    # Ensure category consistency
    canonical_category = f"{archive}.{subject_class}" if subject_class else archive

    try:
        # Prevent multiple auto-endorsements
        if endorser_id is None:
            previous_endorsements = session.query(Endorsement).filter(
                Endorsement.endorser_id.is_(None),
                Endorsement.endorsee_id == endorsee_id,
                Endorsement.archive == archive,
                Endorsement.subject_class == subject_class
            ).with_for_update().count()

            if previous_endorsements:
                session.rollback()
                return False
        else:
            endorser_is_suspect = session.query(Demographic.flag_suspect).filter(
                Demographic.user_id == endorser_id
            ).scalar()

        # Insert endorsement record
        new_endorsement = Endorsement(
            endorser_id=endorser_id,
            endorsee_id=endorsee_id,
            archive=archive,
            subject_class=subject_class,
            flag_valid=True,
            type=type_,
            point_value=point_value,
            issued_when=datetime.utcnow(),
            request_id=request_id
        )
        session.add(new_endorsement)
        session.flush()  # Ensure LAST_INSERT_ID is available

        # Insert audit record
        audit_entry = EndorsementsAudit(
            endorsement_id=new_endorsement.id,
            session_id=None,  # Assuming session_id handling elsewhere
            remote_addr="REMOTE_ADDR",  # Replace with actual request data
            remote_host="REMOTE_HOST",
            tracking_cookie="TRACKING_COOKIE_NAME",
            flag_knows_personally=knows_personally,
            flag_seen_paper=seen_paper,
            comment=comment
        )
        session.add(audit_entry)

        # Handle suspect endorsements
        if point_value and endorser_is_suspect:
            session.query(Demographic).filter(
                Demographic.user_id == endorsee_id
            ).update({Demographic.flag_suspect: True})
            tapir_audit_admin(endorsee_id, "endorsed-by-suspect",
                              f"{endorser_id} {canonical_category} {new_endorsement.id}",
                              "", -1)

        if not point_value:
            session.query(Demographic).filter(
                Demographic.user_id == endorsee_id
            ).update({Demographic.flag_suspect: True})
            tapir_audit_admin(endorsee_id, "got-negative-endorsement",
                              f"{endorser_id} {canonical_category} {new_endorsement.id}", "", -1)

        # Update request if applicable
        if request_id:
            session.query(EndorsementRequest).filter(
                EndorsementRequest.request_id == request_id
            ).update({
                EndorsementRequest.point_value: EndorsementRequest.point_value + point_value
            })

        session.commit()
        return True

    except IntegrityError:
        session.rollback()
        return False

    except Exception as e:
        session.rollback()
        raise e
