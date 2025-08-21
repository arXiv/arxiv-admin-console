import unittest
from datetime import datetime
from typing import Optional, List, Tuple

from arxiv.db.models import Category, EndorsementDomain, QuestionableCategory, Endorsement
from arxiv_admin_api.biz.endorsement_biz import EndorsementAccessor, EndorsementBusiness, EndorsementWithEndorser, \
    PaperProps, can_user_endorse_for, can_user_submit_to
from arxiv_admin_api.dao.endorsement_model import EndorsementModel
from arxiv_admin_api.endorsement_requests import EndorsementRequestModel
from arxiv_admin_api.endorsements import EndorsementCodeModel
from arxiv_admin_api.public_users import PublicUserModel
from arxiv_admin_api.user import UserModel

USER_PROTO = {
    "id": "",
    "flag_is_mod": False,
    "email": "",
    "first_name": "",
    "last_name": "",
    "suffix_name": "",
    "username": "",
    "email_bouncing": False,
    "policy_class": 1,
    "joined_date": 1577836800, # "2020-01-01T00:00:00",
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
    "flag_group_cs": False,
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
}

USER_DATA = {
    "cs-mod":
        {
            "id": "100",
            "flag_is_mod": True,
            "email": "user100@example.edu",
            "first_name": "Jane",
            "last_name": "Mod",
            "username": "user-cs-mod",
            "type": "2",
            "archive": "cs",
            "subject_class": "AI",
            "original_subject_classes": "AI, ML",
            "flag_group_cs": True,
        },

    "cookie":
        {
            "id": "200",
            "email": "cmonster@example.edu",
            "first_name": "Cookie",
            "last_name": "Monster",
            "username": "cookie_monster",
            "type": "3",
            "archive": "cs",
            "subject_class": "AI",
            "flag_group_cs": True,
        },

    "evil-cookie":
        {
            "id": "201",
            "email": "cmonster@example.edu",
            "first_name": "Cookie",
            "last_name": "Monster",
            "username": "cookie_monster",
            "type": "3",
            "archive": "cs",
            "subject_class": "AI",
            "flag_group_cs": True,
            "veto_status": "no-upload",
    },

    "suspect":
        {
            "id": "300",
            "email": "suspect@example.edu",
            "first_name": "Usual",
            "last_name": "Suspect",
            "username": "suspect",
            "type": "2",
            "archive": "cs",
            "subject_class": "AI",
            "flag_group_cs": True,
            "flag_suspect": True,
        },

    "veto":
        {
            "id": "400",
            "email": "vetoed@example.edu",
            "first_name": "Vince",
            "last_name": "Etoed",
            "username": "vetoed",
            "email_bouncing": False,
            "type": "2",
            "archive": "cs",
            "subject_class": "AI",
            "original_subject_classes": "AI, ML",
            "flag_group_cs": True,
            "veto_status": "no-endorse"
        },

    "econ-mod":
        {
            "id": "500",
            "flag_is_mod": True,
            "email": "moderater@example.edu",
            "first_name": "Michelle",
            "last_name": "Oderater",
            "username": "moderator",
            "archive": "econ",
            "subject_class": "EM",
            "original_subject_classes": "econ.EM",
            "flag_group_econ": True,
        },

    "user600":
        {
            "id": "600",
            "email": "user600@example.edu",
            "first_name": "Roppyaku",
            "last_name": "Youzer",
            "username": "user600",
            "archive": "econ",
            "subject_class": "EM",
            "original_subject_classes": "econ.EM",
            "flag_group_econ": False,
        },

    "user700":
        {
            "id": "700",
            "email": "user700@example.edu",
            "first_name": "Nanahyaku",
            "last_name": "Youzer",
            "suffix_name": "",
            "username": "user700",
            "archive": "econ",
            "subject_class": "EM",
            "original_subject_classes": "econ.EM",
            "flag_group_econ": True,
            "veto_status": "ok"
        },

    "user800":
        {
            "id": "800",
            "email": "user800@example.edu",
            "first_name": "Happyaku",
            "last_name": "Youzer",
            "suffix_name": "",
            "username": "user800",
            "archive": "econ",
            "subject_class": "EM",
            "original_subject_classes": "econ.EM",
            "flag_group_econ": True,
            "veto_status": "ok"
        },

    "user900":
        {
            "id": "900",
            "email": "user900@example.edu",
            "first_name": "Kyuhyaku",
            "last_name": "Youzer",
            "suffix_name": "",
            "username": "user900",
            "archive": "econ",
            "subject_class": "EM",
            "original_subject_classes": "econ.EM",
            "flag_group_econ": True,
            "veto_status": "ok"
        },

}

def get_user_data(moniker: str) -> dict:
    data = USER_PROTO.copy()
    data.update(USER_DATA[moniker])
    return data

USER_DATA_BY_ID = { user["id"]: user for user in USER_DATA.values() }

class MockEndorsementAccessor(EndorsementAccessor):

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

    def get_endorsements(self, user_id: str, archive: str, subject_class: str) -> List[EndorsementWithEndorser]:
        """SELECT endorser_id, point_value, type FROM arXiv_endorsements
                           WHERE endorsee_id = :user_id AND archive = :archive AND subject_class = :subject_class AND flag_valid = 1"""
        return {
            "600": [
                EndorsementWithEndorser(
                    endorsement_id=1,
                    endorser_id=1000,
                    endorsee_id=600,
                    archive="econ",
                    subject_class="EM",
                    flag_valid=1,
                    type="user",
                    point_value=5,
                    issued_when=datetime.now(),
                    request_id=104,
                    endorser_username="user001"),

                EndorsementWithEndorser(
                    endorsement_id=2,
                    endorser_id=1001,
                    endorsee_id=600,
                    archive="econ",
                    subject_class="EM",
                    flag_valid=1,
                    type="user",
                    point_value=5,
                    issued_when=datetime.now(),
                    request_id=104,
                    endorser_username="user002"),

                EndorsementWithEndorser(
                    endorsement_id=3,
                    endorser_id=1002,
                    endorsee_id=600,
                    archive="econ",
                    subject_class="EM",
                    flag_valid=1,
                    type="user",
                    point_value=5,
                    issued_when=datetime.now(),
                    request_id=104,
                    endorser_username="user003")
            ],
            "700": [
                EndorsementWithEndorser(
                    endorsement_id=2,
                    endorser_id=1001,
                    endorsee_id=600,
                    archive="econ",
                    subject_class="EM",
                    flag_valid=1,
                    type="user",
                    point_value=5,
                    issued_when=datetime.now(),
                    request_id=104,
                    endorser_username="user002"),
            ]

        }.get(user_id, [])

    def get_questionable_categories(self, archive: str, subject_class: str) -> List[QuestionableCategory]:
        return [
            QuestionableCategory(archive="math", subject_class="GM"),
            QuestionableCategory(archive="ptysics", subject_class="gen-ph"),
        ]

    def get_papers_by_user(self, user_id: str, domain: str, window: List[datetime] | None, require_author: bool = True) -> List[PaperProps]:
        return {
            "800": [
                PaperProps(document_id=8001, flag_author=True, title="Paper 8001",
                           dated=datetime.fromisoformat("2000-01-01T00:00:00Z")),
                PaperProps(document_id=8002, flag_author=True, title="Paper 8002",
                           dated=datetime.fromisoformat("2000-01-02T00:00:00Z")),
                PaperProps(document_id=8003, flag_author=True, title="Paper 8003",
                           dated=datetime.fromisoformat("2000-01-03T00:00:00Z")),
                PaperProps(document_id=8004, flag_author=True, title="Paper 8004",
                           dated=datetime.fromisoformat("2000-01-04T00:00:00Z")),
                PaperProps(document_id=8005, flag_author=True, title="Paper 8005",
                           dated=datetime.fromisoformat("2000-01-05T00:00:00Z")),
            ],
            "900": [
                PaperProps(document_id=9001, flag_author=True, title="Paper 9001",
                           dated=datetime.fromisoformat("2000-01-01T00:00:00Z")),
                PaperProps(document_id=9002, flag_author=True, title="Paper 9002",
                           dated=datetime.fromisoformat("2000-01-02T00:00:00Z")),
            ]

        }.get(user_id, [])


    def is_academic_email(self, email: str) -> Tuple[bool, str]:
        is_edu = email.endswith(".edu")
        return is_edu, email


    def get_user(self, id: str) -> UserModel | None:
        user = USER_DATA_BY_ID.get(id)
        if user is None:
            return None
        data = USER_PROTO.copy()
        data.update(user)
        return UserModel.to_model(data)


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
        return None


    def get_existing_endorsement(self, biz: "EndorsementBusiness") -> EndorsementModel | None:
        return None

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



class TestEndorsementJudgement(unittest.TestCase):
    def setUp(self):
        self.accessor = MockEndorsementAccessor()
        self.audit_timestamp = datetime.fromisoformat("2025-01-01T00:00:00Z")  # Using now makes it phase of moon bug
        self.client_host = "127.0.0.1"
        self.client_host_name = "noplace-like@home.edu"
        self.tracking_cookie = "I-ate-them-all"
        self.tapir_session_id = 100

    def test_good_endorsement_by_moderator(self):
        """Tests success endorsement by a moderator"""
        endorser = UserModel.to_model(get_user_data("cs-mod"))
        endorsee = PublicUserModel.model_validate(get_user_data("cookie"))

        code: EndorsementCodeModel = EndorsementCodeModel(
            preflight=True,
            endorser_id=str(endorser.id),
            endorsement_code="GOOD01",
            comment="This is good",
            knows_personally=True,
            seen_paper=True,
            positive=True,
        )

        data = endorsement_request_good_data.copy()
        data['endorsee_id'] = str(endorsee.id)
        endorsement_request = EndorsementRequestModel.model_validate(data)
        assert endorsement_request.archive != None
        assert endorsement_request.subject_class != None

        business = EndorsementBusiness(
            self.accessor,
            endorser,
            endorsee,
            self.audit_timestamp,
            archive=endorsement_request.archive,
            subject_class=endorsement_request.subject_class,
            endorsement_code=code,
            endorsement_request=endorsement_request,
            session_id=str(self.tapir_session_id),
            remote_host_ip=self.client_host,
            remote_host_name=self.client_host_name,
            tracking_cookie=self.tracking_cookie,
        )
        self.assertTrue(business.can_submit())
        self.assertEqual("Endorser user-cs-mod is a moderator in cs.AI.", business.reason)

    def test_bad_endorsement(self):
        """Tests a reject because of unrelated category"""
        endorser = UserModel.to_model(get_user_data("econ-mod"))
        endorsee = PublicUserModel.model_validate(get_user_data("cookie"))

        code: EndorsementCodeModel = EndorsementCodeModel(
            preflight=True,
            endorser_id=str(endorser.id),
            endorsement_code="GOOD01",
            comment="This is bad",
            knows_personally=True,
            seen_paper=True,
            positive=True,
        )
        data = endorsement_request_bad_data.copy()
        data['endorsee_id'] = str(endorsee.id)
        endorsement_request = EndorsementRequestModel.model_validate(data)

        business = EndorsementBusiness(
            self.accessor,
            endorser,
            endorsee,
            self.audit_timestamp,
            archive=endorsement_request.archive,
            subject_class=endorsement_request.subject_class,
            endorsement_request=endorsement_request,
            endorsement_code=code,
            session_id=str(self.tapir_session_id),
            remote_host_ip=self.client_host,
            remote_host_name=self.client_host_name,
            tracking_cookie=self.tracking_cookie,
        )
        self.assertFalse(business.can_submit())

    def test_vetoed_user(self):
        """Endorsee is vetoed"""
        endorser = UserModel.to_model(get_user_data("veto"))
        endorsee = PublicUserModel.model_validate(get_user_data("cookie"))

        code: EndorsementCodeModel = EndorsementCodeModel(
            preflight=True,
            endorser_id=str(endorser.id),
            endorsement_code="VETO01",
            comment="This is bad",
            knows_personally=True,
            seen_paper=True,
            positive=True,
        )
        data = endorsement_request_good_data.copy()
        data['endorsee_id'] = str(endorsee.id)
        endorsement_request = EndorsementRequestModel.model_validate(data)

        business = EndorsementBusiness(
            self.accessor,
            endorser,
            endorsee,
            self.audit_timestamp,
            archive=endorsement_request.archive,
            subject_class=endorsement_request.subject_class,
            endorsement_request=endorsement_request,
            endorsement_code=code,
            session_id=str(self.tapir_session_id),
            remote_host_ip=self.client_host,
            remote_host_name=self.client_host_name,
            tracking_cookie=self.tracking_cookie,
        )

        self.assertFalse(business.can_submit())
        self.assertEqual("This endorsing user's ability to endorse has been suspended by administrative action.",
                         business.reason)

    def test_proxy_submitter(self):
        """Endorsee is a proxy submitter."""
        proxy_user = get_user_data("cs-mod")
        proxy_user["flag_proxy"] = True
        endorser = UserModel.to_model(proxy_user)
        endorsee = PublicUserModel.model_validate(get_user_data("cookie"))

        code: EndorsementCodeModel = EndorsementCodeModel(
            preflight=True,
            endorser_id=str(endorser.id),
            endorsement_code="GOOD01",
            comment="This is good",
            knows_personally=True,
            seen_paper=True,
            positive=True,
        )

        data = endorsement_request_good_data.copy()
        data['endorsee_id'] = str(endorsee.id)
        endorsement_request = EndorsementRequestModel.model_validate(data)

        business = EndorsementBusiness(
            self.accessor,
            endorser,
            endorsee,
            self.audit_timestamp,
            archive=endorsement_request.archive,
            subject_class=endorsement_request.subject_class,
            endorsement_request=endorsement_request,
            endorsement_code=code,
            session_id=str(self.tapir_session_id),
            remote_host_ip=self.client_host,
            remote_host_name=self.client_host_name,
            tracking_cookie=self.tracking_cookie,
        )
        self.assertFalse(business.can_submit())
        self.assertEqual("Proxy submitters are not allowed to endorse.", business.reason)

    def test_non_definitive_category(self):
        """Reject by non-definitive category.  here cs.*"""
        endorser = UserModel.to_model(get_user_data("cs-mod"))
        endorsee = PublicUserModel.model_validate(get_user_data("cookie"))

        code: EndorsementCodeModel = EndorsementCodeModel(
            preflight=True,
            endorser_id=str(endorser.id),
            endorsement_code="GOOD01",
            comment="This maybe good",
            knows_personally=True,
            seen_paper=True,
            positive=True,
        )

        data = endorsement_request_non_definitive_data.copy()
        data['endorsee_id'] = str(endorsee.id)
        endorsement_request = EndorsementRequestModel.model_validate(data)

        business = EndorsementBusiness(
            self.accessor,
            endorser,
            endorsee,
            self.audit_timestamp,
            archive=endorsement_request.archive,
            subject_class=endorsement_request.subject_class,
            endorsement_request=endorsement_request,
            endorsement_code=code,
            session_id=str(self.tapir_session_id),
            remote_host_ip=self.client_host,
            remote_host_name=self.client_host_name,
            tracking_cookie=self.tracking_cookie,
        )
        self.assertFalse(business.can_submit())
        self.assertEqual("We don't issue endorsements for non-definitive categories.", business.reason)

    def test_good_by_mod_ARXIVDEV_3461(self):
        """Accept because a mod said okay"""
        endorser = UserModel.to_model(get_user_data("econ-mod"))
        endorsee = PublicUserModel.model_validate(get_user_data("cookie"))

        code: EndorsementCodeModel = EndorsementCodeModel(
            preflight=True,
            endorser_id=str(endorser.id),
            endorsement_code="GOOD01",
            comment="This is good",
            knows_personally=True,
            seen_paper=True,
            positive=True,
        )

        data = endorsement_request_good_econ_data.copy()
        data['endorsee_id'] = str(endorsee.id)
        endorsement_request = EndorsementRequestModel.model_validate(data)

        business = EndorsementBusiness(
            self.accessor,
            endorser,
            endorsee,
            self.audit_timestamp,
            archive=endorsement_request.archive,
            subject_class=endorsement_request.subject_class,
            endorsement_request=endorsement_request,
            endorsement_code=code,
            session_id=str(self.tapir_session_id),
            remote_host_ip=self.client_host,
            remote_host_name=self.client_host_name,
            tracking_cookie=self.tracking_cookie,
        )
        self.assertTrue(business.can_submit())
        self.assertEqual("Endorser moderator is a moderator in econ.", business.reason)

    # Good by moderator is the first test.

    def test_bad_endorsement_endorsee_no_upload(self):
        """Tests the endorsee who has no-upload"""

        endorser = UserModel.to_model(get_user_data("user600"))
        endorsee = PublicUserModel.model_validate(get_user_data("evil-cookie"))

        code: EndorsementCodeModel = EndorsementCodeModel(
            preflight=True,
            endorser_id=str(endorser.id),
            endorsement_code="GOOD01",
            comment="This is good",
            knows_personally=True,
            seen_paper=True,
            positive=True,
        )

        data = endorsement_request_good_data.copy()
        data['endorsee_id'] = str(endorsee.id)
        endorsement_request = EndorsementRequestModel.model_validate(data)

        business = EndorsementBusiness(
            self.accessor,
            endorser,
            endorsee,
            self.audit_timestamp,
            archive=endorsement_request.archive,
            subject_class=endorsement_request.subject_class,
            endorsement_request=endorsement_request,
            endorsement_code=code,
            session_id=str(self.tapir_session_id),
            remote_host_ip=self.client_host,
            remote_host_name=self.client_host_name,
            tracking_cookie=self.tracking_cookie,
        )
        self.assertFalse(business.can_submit())
        self.assertEqual("Requesting user's ability to upload has been suspended.", business.reason)

    def test_accept_enough_endorsements(self):
        """Accept because enough endorsements"""
        endorser = UserModel.to_model(get_user_data("user800"))  # Ordinary monster
        endorsee = PublicUserModel.model_validate(get_user_data("user600"))  # Ordinary user

        code: EndorsementCodeModel = EndorsementCodeModel(
            preflight=True,
            endorser_id=str(endorser.id),
            endorsement_code="GOOD01",
            comment="This is good",
            knows_personally=True,
            seen_paper=True,
            positive=True,
        )

        data = endorsement_request_good_econ_data.copy()
        data['endorsee_id'] = str(endorsee.id)
        endorsement_request = EndorsementRequestModel.model_validate(data)

        business = EndorsementBusiness(
            self.accessor,
            endorser,
            endorsee,
            self.audit_timestamp,
            archive=endorsement_request.archive,
            subject_class=endorsement_request.subject_class,
            endorsement_request=endorsement_request,
            endorsement_code=code,
            session_id=str(self.tapir_session_id),
            remote_host_ip=self.client_host,
            remote_host_name=self.client_host_name,
            tracking_cookie=self.tracking_cookie,
        )
        self.assertTrue(business.can_submit())
        self.assertEqual("Endorser is author of: Paper 8001, Paper 8002, Paper 8003.", business.reason)

    def test_reject_not_enough_endorsements(self):
        """Reject because not enough endorsements"""
        endorser = UserModel.to_model(get_user_data("cookie"))  # Ordinary monster
        endorsee = PublicUserModel.model_validate(get_user_data("user700"))  # Ordinary user

        code: EndorsementCodeModel = EndorsementCodeModel(
            preflight=True,
            endorser_id=str(endorser.id),
            endorsement_code="GOOD01",
            comment="This is good",
            knows_personally=True,
            seen_paper=True,
            positive=True,
        )

        data = endorsement_request_good_econ_data.copy()
        data['endorsee_id'] = str(endorsee.id)
        endorsement_request = EndorsementRequestModel.model_validate(data)

        business = EndorsementBusiness(
            self.accessor,
            endorser,
            endorsee,
            self.audit_timestamp,
            archive=endorsement_request.archive,
            subject_class=endorsement_request.subject_class,
            endorsement_request=endorsement_request,
            endorsement_code=code,
            session_id=str(self.tapir_session_id),
            remote_host_ip=self.client_host,
            remote_host_name=self.client_host_name,
            tracking_cookie=self.tracking_cookie,
        )
        self.assertFalse(business.can_submit())
        self.assertEqual(
            "Endorser does not have enough registered papers in econ.EM in the 3mo-5yr window.",
            business.reason)

    def test_accept_endorser_with_enough_papers(self):
        """Accept because the endorser has enough paper quota"""
        endorser = UserModel.to_model(get_user_data("user800"))  # Ordinary user
        endorsee = PublicUserModel.model_validate(get_user_data("user700"))  # Ordinary user

        code: EndorsementCodeModel = EndorsementCodeModel(
            preflight=True,
            endorser_id=str(endorser.id),
            endorsement_code="GOOD01",
            comment="This is good",
            knows_personally=True,
            seen_paper=True,
            positive=True,
        )

        data = endorsement_request_good_econ_data.copy()
        data['endorsee_id'] = str(endorsee.id)
        endorsement_request = EndorsementRequestModel.model_validate(data)

        business = EndorsementBusiness(
            self.accessor,
            endorser,
            endorsee,
            self.audit_timestamp,
            archive=endorsement_request.archive,
            subject_class=endorsement_request.subject_class,
            endorsement_request=endorsement_request,
            endorsement_code=code,
            session_id=str(self.tapir_session_id),
            remote_host_ip=self.client_host,
            remote_host_name=self.client_host_name,
            tracking_cookie=self.tracking_cookie,
        )
        self.assertTrue(business.can_submit())
        self.assertEqual("Endorser is author of: Paper 8001, Paper 8002, Paper 8003.", business.reason)

    def test_reject_endorser_without_enough_papers(self):
        """Accept because the endorser has enough paper quota"""
        endorser = UserModel.to_model(get_user_data("user900"))  # Ordinary user
        endorsee = PublicUserModel.model_validate(get_user_data("user700"))  # Ordinary user

        code: EndorsementCodeModel = EndorsementCodeModel(
            preflight=True,
            endorser_id=str(endorser.id),
            endorsement_code="GOOD01",
            comment="This is good",
            knows_personally=True,
            seen_paper=True,
            positive=True,
        )

        data = endorsement_request_good_econ_data.copy()
        data['endorsee_id'] = str(endorsee.id)
        endorsement_request = EndorsementRequestModel.model_validate(data)

        business = EndorsementBusiness(
            self.accessor,
            endorser,
            endorsee,
            self.audit_timestamp,
            archive=endorsement_request.archive,
            subject_class=endorsement_request.subject_class,
            endorsement_request=endorsement_request,
            endorsement_code=code,
            session_id=str(self.tapir_session_id),
            remote_host_ip=self.client_host,
            remote_host_name=self.client_host_name,
            tracking_cookie=self.tracking_cookie,
        )
        self.assertFalse(business.can_submit())
        self.assertEqual("User must be the registered author of 3 registered papers to endorse for econ.EM but has only 2 in the 3mo-5yr window.", business.reason)

    def test_can_user_endorse_for(self):
        # This user is a cs.AI moderator
        user_id = "100"
        user = self.accessor.get_user(user_id)
        result, biz = can_user_endorse_for(self.accessor, user,"cs", "AI")
        self.assertTrue(result)
        self.assertEqual('Endorser user-cs-mod is a moderator in cs.AI.', biz.reason)

        # This user is not a econ.EM moderator
        result, biz = can_user_endorse_for(self.accessor, user,"econ", "EM")
        self.assertFalse(result)
        self.assertEqual('Endorser does not have enough registered papers in econ.EM in the 3mo-5yr window.', biz.reason)


    def test_can_user_submit_to(self):
        # This user is a cs.AI moderator
        user_id = "100"
        user = self.accessor.get_user(user_id)
        result, biz = can_user_submit_to(self.accessor, user,"econ", "EM")
        self.assertTrue(result)



if __name__ == '__main__':
    unittest.main()
