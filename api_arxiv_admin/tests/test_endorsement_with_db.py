import subprocess
import time
import unittest
from datetime import datetime
from typing import List

from admin_api_routes.database import DatabaseSession
from admin_api_routes.endorsement_requsets import EndorsementRequestModel

from arxiv.db.models import EndorsementRequest, \
    TapirUser  # Category, EndorsementDomain, QuestionableCategory, Endorsement,

from admin_api_routes.biz.endorsement_biz import EndorsementBusiness, EndorsementWithEndorser
from admin_api_routes.biz.endorsement_io import EndorsementDBAccessor
from admin_api_routes.endorsements import EndorsementCodeModel

HOST = "127.0.0.1"
DB_PORT = 21601
DB_USER = "arxiv"
DB_PASSWORD = "arxiv_password"
MAX_RETRIES = 10
RETRY_DELAY = 2
DOCKER_COMPOSE_ARGS = ["docker", "compose", "-f", "../tests/docker-compose-for-test.yaml",
                       "--env-file=../tests/test-env"]

class TestReadOnlys(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # docker compose -f ./docker-compose-for-test.yaml --env-file=./test-env  up
        subprocess.run(DOCKER_COMPOSE_ARGS + ["up", "-d"])

        from tests.restore_mysql import wait_for_mysql
        wait_for_mysql(HOST, DB_PORT, DB_USER, DB_PASSWORD, "arXiv", MAX_RETRIES, RETRY_DELAY)
        db_uri = "mysql+mysqldb://{}:{}@{}:{}/{}?ssl=false&ssl_mode=DISABLED".format(DB_USER, DB_PASSWORD, HOST, DB_PORT, "arXiv")
        from arxiv.config import Settings
        settings = Settings(
            CLASSIC_DB_URI = db_uri,
            LATEXML_DB_URI = None
        )
        from admin_api_routes.database import Database
        database = Database(settings)
        database.set_to_global()
        from app_logging import setup_logger
        setup_logger()
        for _ in range(10):
            try:
                with DatabaseSession() as session:
                    users = session.query(TapirUser).all()
                    if len(users) > 0:
                        break
            except Exception:
                time.sleep(5)
                continue

    @classmethod
    def tearDownClass(cls):
        """This method runs once after all test methods in the class."""
        subprocess.run(DOCKER_COMPOSE_ARGS + ["down"])

    def test_see_papers(self):
        with DatabaseSession() as session:
            accessor = EndorsementDBAccessor(session)
            user_ids = session.query(TapirUser.user_id).all()
            window = [None, None]
            count = 0
            for domain in ["cs"]:
                for user_id in user_ids:
                    papers = accessor.get_papers_by_user(user_id[0], domain, window, require_author=False)
                    if len(papers) >= 3:
                        print("Found {}".format(user_id[0]))
                    count = count + len(papers)
            self.assertTrue(count)

    def test_academic_email(self):
        with DatabaseSession() as session:
            accessor = EndorsementDBAccessor(session)
            answer, reason = accessor.is_academic_email("")
            self.assertFalse(answer)
            answer, reason = accessor.is_academic_email("%A%")
            self.assertFalse(answer)
            answer, reason = accessor.is_academic_email("me@my.biz")
            self.assertFalse(answer)
            answer, reason = accessor.is_academic_email("a@amuz.gda.pl")
            self.assertTrue(answer)
            answer, reason = accessor.is_academic_email("foobar@cornell.edu")
            self.assertTrue(answer)
            answer, reason = accessor.is_academic_email("foobar@arxiv.org")
            # We may want to reconsider this...
            self.assertFalse(answer)

    def test_is_moderator(self):
        with DatabaseSession() as session:
            accessor = EndorsementDBAccessor(session)
            user_ids = session.query(TapirUser.user_id).all()
            count = 0
            for archive in ["cs"]:
                for user_id in user_ids:
                    if accessor.is_moderator(user_id[0], archive=archive):
                        count += 1
            self.assertEqual(2, count)

    def test_get_category(self):
        with DatabaseSession() as session:
            accessor = EndorsementDBAccessor(session)
            for archive, subject_class, expect in [("cs", "AI", True), ("cs", "XX", False), ("econ", None, True)]:
                cat = accessor.get_category(archive, subject_class)
                self.assertEqual(cat if expect else None, cat)

    def test_get_domain_info(self):
        with DatabaseSession() as session:
            accessor = EndorsementDBAccessor(session)
            for archive, subject_class, expect in [("cs", "AI", True), ("cs", None, False), ("econ", None, True)]:
                cat = accessor.get_category(archive, subject_class)
                self.assertNotEqual(None, cat)
                domain = accessor.get_domain_info(cat)
                self.assertEqual(expect, domain)

    def test_get_endorsements(self, user_id: str, canon_archive: str, canon_subject_class: str) -> List[EndorsementWithEndorser]| None:
        with DatabaseSession() as session:
            accessor = EndorsementDBAccessor(session)



class TestCreateEndorsement(unittest.TestCase):

    def setUp(self):
        self.audit_timestamp = datetime.fromisoformat("2025-01-01T00:00:00Z")  # Using now makes it

        # docker compose -f ./docker-compose-for-test.yaml --env-file=./test-env  up
        self.tapir_session_id = 100
        subprocess.run(DOCKER_COMPOSE_ARGS + ["up", "-d"])

        from tests.restore_mysql import wait_for_mysql
        wait_for_mysql(HOST, DB_PORT, DB_USER, DB_PASSWORD, "arXiv", MAX_RETRIES, RETRY_DELAY)
        db_uri = "mysql+mysqldb://{}:{}@{}:{}/{}?ssl=false&ssl_mode=DISABLED".format(DB_USER, DB_PASSWORD, HOST, DB_PORT, "arXiv")
        from arxiv.config import Settings
        settings = Settings(
            CLASSIC_DB_URI = db_uri,
            LATEXML_DB_URI = None
        )
        from admin_api_routes.database import Database
        database = Database(settings)
        database.set_to_global()
        from app_logging import setup_logger
        setup_logger()
        for _ in range(10):
            try:
                with DatabaseSession() as session:
                    users = session.query(TapirUser).all()
                    if len(users) > 0:
                        break
            except Exception:
                time.sleep(5)
                continue


    def tearDown(self):
        subprocess.run(DOCKER_COMPOSE_ARGS + ["down"])

    def test_create_endorsement(self):
        client_host = "127.0.0.1"
        client_host_name = "no-place-like@home.biz"
        tracking_cookie = "I-ate-them-all"
        # Unfortunatnely, this seems to load the default

        endorsement_code = "R8T3GZ"
        with DatabaseSession() as session:
            er = EndorsementRequestModel.base_select(session).filter(EndorsementRequest.secret == endorsement_code).one_or_none()
            self.assertNotEqual(None, er)
            erm = EndorsementRequestModel.model_validate(er)

            accessor = EndorsementDBAccessor(session)
            endorser = accessor.get_user("591211")
            endorsee = accessor.get_user("1019756")

            code: EndorsementCodeModel = EndorsementCodeModel(
                endorser_id=str(endorser.id),
                endorsement_code=endorsement_code,
                comment="This is good",
                knows_personally=True,
                seen_paper=True,
                positive=True,
            )

            business = EndorsementBusiness(
                accessor,
                code,
                endorser,
                endorsee,
                erm,
                str(self.tapir_session_id),

                client_host,
                client_host_name,

                self.audit_timestamp,
                tracking_cookie,
            )
            self.assertTrue(business.can_endorse())
            endorsement = business.endorse()
            self.assertNotEqual(None, endorsement)



if __name__ == '__main__':
    unittest.main()
