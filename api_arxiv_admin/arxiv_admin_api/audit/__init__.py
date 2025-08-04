
from sqlalchemy.orm import Session
from typing import Any, Optional
from arxiv_bizlogic.audit_event import (admin_audit, AdminAuditEvent, AdminAudit_SetBanned, AdminAudit_SetEditUsers,
                                        AdminAudit_SetEditSystem, AdminAudit_SetSuspect, AdminAudit_SetEmailVerified,
                                        AdminAudit_AddPaperOwner, AdminAudit_AddPaperOwner2, AdminAudit_ChangePassword,
                                        AdminAudit_AdminChangePaperPassword, AdminAudit_AdminMakeAuthor,
                                        AdminAudit_AdminMakeNonauthor, AdminAudit_AdminRevokePaperOwner,
                                        AdminAudit_AdminUnrevokePaperOwner, AdminAudit_BecomeUser,
                                        AdminAudit_ChangeEmail, AdminAudit_SuspendUser, AdminAudit_UnuspendUser,
                                        AdminAudit_SetGroupTest, AdminAudit_SetProxy, AdminAudit_SetXml,
                                        AdminAudit_SetEndorsementValid, AdminAudit_SetPointValue,
                                        AdminAudit_SetEndorsementRequestsValid, AdminAudit_SetEmailBouncing)
from typing import Type

def audit_event_maker_positional(cls: Type[AdminAuditEvent],
                                 admin_id: str, session_id: str,
                                 _prop_name: str, user_id: str, _old_value: Any, new_value: Any,
                                 comment: Optional[str] = None,
                                 remote_ip: Optional[str] = None,
                                 remote_hostname: Optional[str] = None,
                                 tracking_cookie: Optional[str] = None,
                                 ) -> AdminAuditEvent:

    return cls(
        admin_id,
        session_id,
        user_id,
        new_value,
        comment=comment,
        remote_ip=remote_ip,
        remote_hostname=remote_hostname,
        tracking_cookie=tracking_cookie
    )



def audit_event_maker_kwarg(cls: Type[AdminAuditEvent],
                            admin_id: str, session_id: str,
                            _prop_name: str, user_id: str, _old_value: Any, new_value: Any,
                            comment: Optional[str] = None,
                            remote_ip: Optional[str] = None,
                            remote_hostname: Optional[str] = None,
                            tracking_cookie: Optional[str] = None,
                            arg_name: str = None,
                            ) -> AdminAuditEvent:
    kwargs = {
        "comment": comment,
        "remote_ip": remote_ip,
        "remote_hostname": remote_hostname,
        "tracking_cookie": tracking_cookie,
    }

    if arg_name is not None:
        kwargs[arg_name] = new_value

    return cls(
        admin_id,
        session_id,
        user_id,
        **kwargs
    )


user_prop_audit_registry = {
    "add_paper_owner": (AdminAudit_AddPaperOwner, audit_event_maker_positional),
    "add_paper_owner_2": (AdminAudit_AddPaperOwner2, audit_event_maker_positional),
    "admin_change_paper_password": (AdminAudit_AdminChangePaperPassword, audit_event_maker_positional),

    "admin_make_author": (AdminAudit_AdminMakeAuthor, audit_event_maker_positional),
    "admin_make_nonauthor": (AdminAudit_AdminMakeNonauthor, audit_event_maker_positional),
    "admin_revoke_paper": (AdminAudit_AdminRevokePaperOwner, audit_event_maker_positional),
    "admin_unrevoke_paper": (AdminAudit_AdminUnrevokePaperOwner, audit_event_maker_positional),

    # AdminAudit_AdminNotArxivRevokePaperOwner - There are two versions of "revoke" and I am not sure.

    "become_user": (AdminAudit_BecomeUser, audit_event_maker_kwarg),
    "suspend_user": (AdminAudit_SuspendUser, audit_event_maker_kwarg),
    "unsuspend_user": (AdminAudit_UnuspendUser, audit_event_maker_kwarg),

    "change_email": (AdminAudit_ChangeEmail, audit_event_maker_kwarg, "email"),
    "change_password": (AdminAudit_ChangePassword, audit_event_maker_kwarg),

    # "flag_banned": (AdminAudit_SetBanned, audit_event_maker_positional),

    "flag_suspect": (AdminAudit_SetSuspect, audit_event_maker_positional),
    "group_test": (AdminAudit_SetGroupTest, audit_event_maker_positional),
    "proxy": (AdminAudit_SetProxy, audit_event_maker_positional),
    "xml": (AdminAudit_SetXml, audit_event_maker_positional),
    "endorsement_valid": (AdminAudit_SetEndorsementValid, audit_event_maker_positional),
    "point_value": (AdminAudit_SetPointValue, audit_event_maker_positional),
    "endorsement_request_valid": (AdminAudit_SetEndorsementRequestsValid, audit_event_maker_positional),
    "email_bouncing": (AdminAudit_SetEmailBouncing, audit_event_maker_positional),
    "flag_edit_system": (AdminAudit_SetEditSystem, audit_event_maker_positional),
    "flag_edit_users": (AdminAudit_SetEditUsers, audit_event_maker_positional),
    "email_verified": (AdminAudit_SetEmailVerified, audit_event_maker_positional),
}


def record_user_prop_admin_action(session: Session, admin_id: str, session_id: str,
                                  prop_name: str, user_id: str, old_value: Any, new_value: Any,
                                  comment: Optional[str] = None,
                                  remote_ip: Optional[str] = None,
                                  remote_hostname: Optional[str] = None,
                                  tracking_cookie: Optional[str] = None,
                                  ) -> None:
    """
    Records an administrative action performed by an admin on a user's property.
    This does not cover all of admin actions.

    Args:
        session (Session): The active database session to log the audit event.
        admin_id (str): Identifier of the admin performing the action.
        session_id (str): Identifier of the admin's session during the action.
        prop_name (str): Name of the property being modified.
        user_id (str): Identifier of the user whose property is being changed.
        old_value (Any): The previous value of the property before the change.
        new_value (Any): The updated value of the property after the change.
        comment (Optional[str]): An optional comment providing context for the change.
        remote_ip (Optional[str]): The remote IP address from which the change originated.
        remote_hostname (Optional[str]): The remote hostname from which the change originated.
        tracking_cookie (Optional[str]): An optional tracking identifier, usually for tracing user sessions.

    Returns:
        None

    Raises:
        None
    """
    auditor = user_prop_audit_registry.get(prop_name)
    assert auditor is not None, f"Unknown admin action: {prop_name}"

    if len(auditor) == 2:
        audit_class, maker = auditor
        audit_event = maker(
            audit_class,
            admin_id, session_id,
            prop_name, user_id, old_value, new_value,
            comment=comment, remote_ip=remote_ip, remote_hostname=remote_hostname,
            tracking_cookie=tracking_cookie
        )
    else:
        audit_class, maker, arg_name = auditor
        audit_event = maker(
            audit_class,
            admin_id, session_id,
            prop_name, user_id, old_value, new_value,
            comment=comment, remote_ip=remote_ip, remote_hostname=remote_hostname,
            tracking_cookie=tracking_cookie,
            arg_name=arg_name,
        )

    admin_audit(session, audit_event)
