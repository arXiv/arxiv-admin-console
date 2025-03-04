import unittest
from datetime import datetime, UTC
from typing import Optional, List

from arxiv.db.models import Category, EndorsementDomain, QuestionableCategory, Endorsement

from admin_api_routes.biz.endorsement_biz import EndorsementAccessor, EndorsementBusiness, EndorsementWithEndorser, \
    PaperProps
from admin_api_routes.endorsement_requsets import EndorsementRequestModel
from admin_api_routes.endorsements import EndorsementCodeModel
from admin_api_routes.user import UserModel


class TestEndorsementAccessor(EndorsementAccessor):

    def is_moderator(self, user_id: int, archive: str, subject_class: Optional[str] = None) -> bool:
        return False

    def get_category(self, archive: str, subject_class: str) -> Category | None:
        return None

    def get_domain_info(self, category: Category) -> EndorsementDomain | None:
        """Gets Endorsement domain from category"""
        return None

    def get_endorsements(self, user_id: str, canon_archive: str, canon_subject_class: str) -> List[EndorsementWithEndorser]:
        """SELECT endorser_id, point_value, type FROM arXiv_endorsements
                           WHERE endorsee_id = :user_id AND archive = :archive AND subject_class = :subject_class AND flag_valid = 1"""
        return []

    def get_questionable_categories(self, archive: str, subject_class: str) -> List[QuestionableCategory]:
        return []

    def get_papers_by_user(self, user_id: str, domain: str, window: [datetime | None],require_author: bool = True) -> List[PaperProps]:
        return []

    def is_academic_email(self, email: str) -> bool:
        return False

    def get_user(self, id: str) -> UserModel | None:
        pass

    def tapir_audit_admin(self,
                          endorsement: "EndorsementBusiness",
                          affected_user: int,
                          action: str,
                          data: str = "",
                          comment: str = "",
                          user_id: Optional[int] = None,
                          session_id: Optional[int] = None) -> None:
        pass

    def arxiv_endorse(self, endorsement: "EndorsementBusiness") -> Endorsement | None:
        pass

USERS = [
    {
        "id": "100",
        "flag_is_mod": True,
        "email": "user100@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "suffix_name": "Jr.",
        "username": "user1",
        "email_bouncing": False,
        "policy_class": 1,
        "joined_date": "2020-01-01T00:00:00",
        "joined_remote_host": "192.168.1.1",
        "flag_internal": False,
        "flag_edit_users": False,
        "flag_edit_system": False,
        "flag_email_verified": True,
        "flag_approved": True,
        "flag_deleted": False,
        "flag_banned": False,
        "flag_wants_email": True,
        "flag_html_email": True,
        "flag_allow_tex_produced": False,
        "flag_can_lock": False,
        "country": "USA",
        "affiliation": "Test Institute",
        "url": "https://example.com",
        "type": "2",
        "archive": "cs",
        "subject_class": "AI",
        "original_subject_classes": "AI, ML",
        "flag_group_physics": False,
        "flag_group_math": False,
        "flag_group_cs": True,
        "flag_group_nlin": False,
        "flag_proxy": False,
        "flag_journal": False,
        "flag_xml": False,
        "dirty": False,
        "flag_group_test": False,
        "flag_suspect": False,
        "flag_group_q_bio": False,
        "flag_group_q_fin": False,
        "flag_group_stat": False,
        "flag_group_eess": False,
        "flag_group_econ": False,
        "veto_status": None
    },

    {
        "id": "200",
        "flag_is_mod": False,
        "email": "user200@example.com",
        "first_name": "Cookie",
        "last_name": "Monster",
        "suffix_name": "",
        "username": "cookie_monster",
        "email_bouncing": False,
        "policy_class": 1,
        "joined_date": "2020-01-01T00:00:00",
        "joined_remote_host": "192.168.1.1",
        "flag_internal": False,
        "flag_edit_users": False,
        "flag_edit_system": False,
        "flag_email_verified": True,
        "flag_approved": True,
        "flag_deleted": False,
        "flag_banned": False,
        "flag_wants_email": True,
        "flag_html_email": True,
        "flag_allow_tex_produced": False,
        "flag_can_lock": False,
        "country": "USA",
        "affiliation": "Test Institute",
        "url": "https://example.com",
        "type": "3",
        "archive": "cs",
        "subject_class": "AI",
        "original_subject_classes": "AI, ML",
        "flag_group_physics": False,
        "flag_group_math": False,
        "flag_group_cs": True,
        "flag_group_nlin": False,
        "flag_proxy": False,
        "flag_journal": False,
        "flag_xml": False,
        "dirty": False,
        "flag_group_test": False,
        "flag_suspect": False,
        "flag_group_q_bio": False,
        "flag_group_q_fin": False,
        "flag_group_stat": False,
        "flag_group_eess": False,
        "flag_group_econ": False,
        "veto_status": None
    },

    {
        "id": "300",
        "flag_is_mod": False,
        "email": "suspect@example.com",
        "first_name": "Usual",
        "last_name": "Suspect",
        "suffix_name": "",
        "username": "suspect",
        "email_bouncing": False,
        "policy_class": 1,
        "joined_date": "2020-01-01T00:00:00",
        "joined_remote_host": "192.168.1.1",
        "flag_internal": False,
        "flag_edit_users": False,
        "flag_edit_system": False,
        "flag_email_verified": True,
        "flag_approved": True,
        "flag_deleted": False,
        "flag_banned": False,
        "flag_wants_email": True,
        "flag_html_email": True,
        "flag_allow_tex_produced": False,
        "flag_can_lock": False,
        "country": "USA",
        "affiliation": "Test Institute",
        "url": "https://example.com",
        "type": "2",
        "archive": "cs",
        "subject_class": "AI",
        "original_subject_classes": "AI, ML",
        "flag_group_physics": False,
        "flag_group_math": False,
        "flag_group_cs": True,
        "flag_group_nlin": False,
        "flag_proxy": False,
        "flag_journal": False,
        "flag_xml": False,
        "dirty": False,
        "flag_group_test": False,
        "flag_suspect": True,
        "flag_group_q_bio": False,
        "flag_group_q_fin": False,
        "flag_group_stat": False,
        "flag_group_eess": False,
        "flag_group_econ": False,
        "veto_status": None
    },

    {
        "id": "400",
        "flag_is_mod": False,
        "email": "veto@example.com",
        "first_name": "Vince",
        "last_name": "Eto",
        "suffix_name": "",
        "username": "suspect",
        "email_bouncing": False,
        "policy_class": 1,
        "joined_date": "2020-01-01T00:00:00",
        "joined_remote_host": "192.168.1.1",
        "flag_internal": False,
        "flag_edit_users": False,
        "flag_edit_system": False,
        "flag_email_verified": True,
        "flag_approved": True,
        "flag_deleted": False,
        "flag_banned": False,
        "flag_wants_email": True,
        "flag_html_email": True,
        "flag_allow_tex_produced": False,
        "flag_can_lock": False,
        "country": "USA",
        "affiliation": "Test Institute",
        "url": "https://example.com",
        "type": "2",
        "archive": "cs",
        "subject_class": "AI",
        "original_subject_classes": "AI, ML",
        "flag_group_physics": False,
        "flag_group_math": False,
        "flag_group_cs": True,
        "flag_group_nlin": False,
        "flag_proxy": False,
        "flag_journal": False,
        "flag_xml": False,
        "dirty": False,
        "flag_group_test": False,
        "flag_suspect": True,
        "flag_group_q_bio": False,
        "flag_group_q_fin": False,
        "flag_group_stat": False,
        "flag_group_eess": False,
        "flag_group_econ": False,
        "veto_status": "I am veto"
    },

]

# Example dictionary data
endorsement_request_data = {
    "id": "101",
    "endorsee_id": "202",
    "archive": "cs",
    "subject_class": "AI",
    "secret": "s3cr3t",
    "flag_valid": True,
    "flag_open": False,
    "issued_when": "2023-06-15T12:30:00",
    "point_value": "10",
    "flag_suspect": False
}


class TestEndorsement(unittest.TestCase):
    def test_good_endorsement(self):
        endorser = UserModel.model_validate(USERS[0])
        endorsee = UserModel.model_validate(USERS[1])

        code: EndorsementCodeModel = EndorsementCodeModel(
            endorser_id = str(endorser.id),
            endorsement_code = "ABC123",
            comment = "This is good",
            knows_personally = True,
            seen_paper = True,
        )
        accessor = TestEndorsementAccessor()
        audit_timestamp = datetime.now(UTC)
        tracking_cookie = "I-ate-them-all"
        tapir_session_id = 100
        client_host = "127.0.0.1"
        client_host_name = "noplace-like@home.edu"
        data = endorsement_request_data.copy()
        data['endorsee_id'] = endorsee.id
        endorsement_request = EndorsementRequestModel.model_validate(endorsement_request_data)


        business = EndorsementBusiness(
            accessor,
            code,
            endorser,
            endorsee,
            endorsement_request,
            str(tapir_session_id),

            client_host,
            client_host_name,

            audit_timestamp,
            tracking_cookie,
        )
        self.assertTrue(business.can_endorse())


if __name__ == '__main__':
    unittest.main()
