import unittest
from datetime import datetime, UTC
from typing import Optional, List

from arxiv.db.models import Category, EndorsementDomain, QuestionableCategory, Endorsement

from admin_api_routes.biz.endorsement_biz import EndorsementAccessor, EndorsementBusiness, EndorsementWithEndorser, \
    PaperProps
from admin_api_routes.endorsement_requsets import EndorsementRequestModel
from admin_api_routes.endorsements import EndorsementCodeModel
from admin_api_routes.user import UserModel

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
        "veto_status": "ok"
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
        "veto_status": "ok"
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
        "veto_status": "ok"
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
        "veto_status": "veto"
    },

    {
        "id": "500",
        "flag_is_mod": True,
        "email": "moderater@example.com",
        "first_name": "Michelle",
        "last_name": "Oderater",
        "suffix_name": "",
        "username": "moderator",
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
        "archive": "econ",
        "subject_class": "EM",
        "original_subject_classes": "econ.EM",
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
        "veto_status": "ok"
    },

]



class TestEndorsementAccessor(EndorsementAccessor):

    def is_moderator(self, user_id: int, archive: str, subject_class: Optional[str] = None) -> bool:
        key = f"{user_id}-{archive}.{str(subject_class)}"
        return {
            "100-cs.AI": True,
            "500-econ.None": True,
        }.get(key, False)

    def get_category(self, archive: str, subject_class: str) -> Category | None:
        return {
            "cs": {
                "AI": Category(
                    archive="cs",
                    subject_class="AI",
                    definitive=1,
                    active=1,
                    category_name="Artificial Intelligence",
                    endorse_all="n",
                    endorse_email="n",
                    papers_to_endorse=5,
                    endorsement_domain="cs"),
                "": Category(
                    archive="cs",
                    subject_class="",
                    definitive=0,
                    active=1,
                    category_name="Cambridge and Somerville",
                    endorse_all="n",
                    endorse_email="n",
                    papers_to_endorse=5,
                    endorsement_domain="cs")
            },
            "econ": {
                "EM": Category(
                    archive="econ",
                    subject_class="EM",
                    definitive=1,
                    active=1,
                    category_name="Meat Eater",
                    endorse_all="n",
                    endorse_email="n",
                    papers_to_endorse=5,
                    endorsement_domain="econ"),
            }
        }.get(archive, {}).get(subject_class)


    def get_domain_info(self, category: Category) -> EndorsementDomain | None:
        """Gets Endorsement domain from category"""

        return {
            "cs": EndorsementDomain(
                endorsement_domain="cs",
                endorse_all="n",
                mods_endorse_all="y",
                endorse_email="y",
                papers_to_endorse=3
                ),
            "econ": EndorsementDomain(
                endorsement_domain="econ",
                endorse_all="n",
                mods_endorse_all="y",
                endorse_email="y",
                papers_to_endorse=3
            )
        }.get(category.endorsement_domain)


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


# Example dictionary data
endorsement_request_good_data = {
    "id": "101",
    "endorsee_id": "200",
    "archive": "cs",
    "subject_class": "AI",
    "secret": "GOOD01",
    "flag_valid": True,
    "flag_open": True,
    "issued_when": "2023-06-15T12:30:00",
    "point_value": "10",
    "flag_suspect": False
}

endorsement_request_bad_data = {
    "id": "102",
    "endorsee_id": "200",
    "archive": "econ",
    "subject_class": "",
    "secret": "BAD101",
    "flag_valid": True,
    "flag_open": True,
    "issued_when": "2023-06-15T12:30:00",
    "point_value": "10",
    "flag_suspect": False
}

endorsement_request_non_definitive_data = {
    "id": "103",
    "endorsee_id": "200",
    "archive": "cs",
    "subject_class": "",
    "secret": "BAD102",
    "flag_valid": True,
    "flag_open": True,
    "issued_when": "2023-06-15T12:30:00",
    "point_value": "10",
    "flag_suspect": False
}

endorsement_request_good_econ_data = {
    "id": "104",
    "endorsee_id": "200",
    "archive": "econ",
    "subject_class": "EM",
    "secret": "GOOD02",
    "flag_valid": True,
    "flag_open": True,
    "issued_when": "2023-06-15T12:30:00",
    "point_value": "10",
    "flag_suspect": False
}


class TestEndorsement(unittest.TestCase):
    def setUp(self):
        self.accessor = TestEndorsementAccessor()
        self.audit_timestamp = datetime.now(UTC)
        self.client_host = "127.0.0.1"
        self.client_host_name = "noplace-like@home.edu"
        self.tracking_cookie = "I-ate-them-all"
        self.tapir_session_id = 100


    def test_good_endorsement_by_moderator(self):
        endorser = UserModel.model_validate(USERS[0])
        endorsee = UserModel.model_validate(USERS[1])

        code: EndorsementCodeModel = EndorsementCodeModel(
            endorser_id = str(endorser.id),
            endorsement_code = "GOOD01",
            comment = "This is good",
            knows_personally = True,
            seen_paper = True,
        )

        data = endorsement_request_good_data.copy()
        data['endorsee_id'] = str(endorsee.id)
        endorsement_request = EndorsementRequestModel.model_validate(data)

        business = EndorsementBusiness(
            self.accessor,
            code,
            endorser,
            endorsee,
            endorsement_request,
            str(self.tapir_session_id),

            self.client_host,
            self.client_host_name,

            self.audit_timestamp,
            self.tracking_cookie,
        )
        self.assertTrue(business.can_endorse())
        self.assertEqual("Endorser user1 is a moderator in cs.AI.", business.reason)

    def test_bad_endorsement(self):
        endorser = UserModel.model_validate(USERS[0])
        endorsee = UserModel.model_validate(USERS[1])

        code: EndorsementCodeModel = EndorsementCodeModel(
            endorser_id = str(endorser.id),
            endorsement_code = "GOOD01",
            comment = "This is bad",
            knows_personally = True,
            seen_paper = True,
        )
        data = endorsement_request_good_data.copy()
        data['endorsee_id'] = str(endorsee.id)
        endorsement_request = EndorsementRequestModel.model_validate(data)

        business = EndorsementBusiness(
            self.accessor,
            code,
            endorser,
            endorsee,
            endorsement_request,
            str(self.tapir_session_id),

            self.client_host,
            self.client_host_name,

            self.audit_timestamp,
            self.tracking_cookie,
        )
        self.assertFalse(business.can_endorse())

    def test_vetoed_user(self):
        endorser = UserModel.model_validate(USERS[3])
        endorsee = UserModel.model_validate(USERS[1])

        code: EndorsementCodeModel = EndorsementCodeModel(
            endorser_id = str(endorser.id),
            endorsement_code = "VETO01",
            comment = "This is bad",
            knows_personally = True,
            seen_paper = True,
        )
        data = endorsement_request_good_data.copy()
        data['endorsee_id'] = str(endorsee.id)
        endorsement_request = EndorsementRequestModel.model_validate(data)

        business = EndorsementBusiness(
            self.accessor,
            code,
            endorser,
            endorsee,
            endorsement_request,
            str(self.tapir_session_id),

            self.client_host,
            self.client_host_name,

            self.audit_timestamp,
            self.tracking_cookie,
        )
        self.assertFalse(business.can_endorse())
        self.assertEqual("This endorsing user's ability to endorse has been suspended by administrative action.", business.reason)

    def test_proxy_submitter(self):
        proxy_user = USERS[0].copy()
        proxy_user["flag_proxy"] = True
        endorser = UserModel.model_validate(proxy_user)
        endorsee = UserModel.model_validate(USERS[1])

        code: EndorsementCodeModel = EndorsementCodeModel(
            endorser_id = str(endorser.id),
            endorsement_code = "GOOD01",
            comment = "This is good",
            knows_personally = True,
            seen_paper = True,
        )

        data = endorsement_request_good_data.copy()
        data['endorsee_id'] = str(endorsee.id)
        endorsement_request = EndorsementRequestModel.model_validate(data)

        business = EndorsementBusiness(
            self.accessor,
            code,
            endorser,
            endorsee,
            endorsement_request,
            str(self.tapir_session_id),

            self.client_host,
            self.client_host_name,

            self.audit_timestamp,
            self.tracking_cookie,
        )
        self.assertFalse(business.can_endorse())
        self.assertEqual("Proxy submitters are not allowed to endorse.", business.reason)


    def test_non_definitive_category(self):
        endorser = UserModel.model_validate(USERS[0])
        endorsee = UserModel.model_validate(USERS[1])

        code: EndorsementCodeModel = EndorsementCodeModel(
            endorser_id = str(endorser.id),
            endorsement_code = "GOOD01",
            comment = "This maybe good",
            knows_personally = True,
            seen_paper = True,
        )

        data = endorsement_request_good_data.copy()
        data['endorsee_id'] = str(endorsee.id)
        endorsement_request = EndorsementRequestModel.model_validate(data)

        business = EndorsementBusiness(
            self.accessor,
            code,
            endorser,
            endorsee,
            endorsement_request,
            str(self.tapir_session_id),

            self.client_host,
            self.client_host_name,

            self.audit_timestamp,
            self.tracking_cookie,
        )
        self.assertFalse(business.can_endorse())
        self.assertEqual("We don't issue endorsements for non-definitive categories.", business.reason)

    def test_good_by_mod_ARXIVDEV_3461(self):
        endorser = UserModel.model_validate(USERS[4])
        endorsee = UserModel.model_validate(USERS[1])

        code: EndorsementCodeModel = EndorsementCodeModel(
            endorser_id = str(endorser.id),
            endorsement_code = "GOOD01",
            comment = "This is good",
            knows_personally = True,
            seen_paper = True,
        )

        data = endorsement_request_good_econ_data.copy()
        data['endorsee_id'] = str(endorsee.id)
        endorsement_request = EndorsementRequestModel.model_validate(data)

        business = EndorsementBusiness(
            self.accessor,
            code,
            endorser,
            endorsee,
            endorsement_request,
            str(self.tapir_session_id),

            self.client_host,
            self.client_host_name,

            self.audit_timestamp,
            self.tracking_cookie,
        )
        self.assertTrue(business.can_endorse())
        self.assertEqual("Endorser moderator is a moderator in econ.", business.reason)

    # Good by moderator is the first test.

    def test_bad_endorsement_endorsee_no_upload(self):
        endorser = UserModel.model_validate(USERS[2])
        no_upload = USERS[1].copy()
        no_upload["veto_status"] = "no-upload"
        endorsee = UserModel.model_validate(no_upload)

        code: EndorsementCodeModel = EndorsementCodeModel(
            endorser_id = str(endorser.id),
            endorsement_code = "GOOD01",
            comment = "This is good",
            knows_personally = True,
            seen_paper = True,
        )

        data = endorsement_request_good_data.copy()
        data['endorsee_id'] = str(endorsee.id)
        endorsement_request = EndorsementRequestModel.model_validate(data)

        business = EndorsementBusiness(
            self.accessor,
            code,
            endorser,
            endorsee,
            endorsement_request,
            str(self.tapir_session_id),

            self.client_host,
            self.client_host_name,

            self.audit_timestamp,
            self.tracking_cookie,
        )
        self.assertFalse(business.can_endorse())
        self.assertEqual("Requesting user's ability to upload has been suspended.", business.reason)

    def test_bad_endorsement_endorsee_no_upload(self):
        endorser = UserModel.model_validate(USERS[2])
        endorsee = UserModel.model_validate(USERS[1])

        code: EndorsementCodeModel = EndorsementCodeModel(
            endorser_id = str(endorser.id),
            endorsement_code = "GOOD01",
            comment = "This is good",
            knows_personally = True,
            seen_paper = True,
        )

        data = endorsement_request_good_data.copy()
        data['endorsee_id'] = str(endorsee.id)
        endorsement_request = EndorsementRequestModel.model_validate(data)

        business = EndorsementBusiness(
            self.accessor,
            code,
            endorser,
            endorsee,
            endorsement_request,
            str(self.tapir_session_id),

            self.client_host,
            self.client_host_name,

            self.audit_timestamp,
            self.tracking_cookie,
        )
        self.assertTrue(business.can_endorse())
        self.assertEqual("", business.reason)


if __name__ == '__main__':
    unittest.main()
