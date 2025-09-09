import pytest
from datetime import datetime

from arxiv_bizlogic.database import DatabaseSession
from arxiv_admin_api.endorsement_requests import EndorsementRequestModel

from arxiv.db.models import EndorsementRequest, \
    TapirUser  # Category, EndorsementDomain, QuestionableCategory, Endorsement,

from arxiv_admin_api.biz.endorsement_biz import EndorsementBusiness
from arxiv_admin_api.biz.endorsement_io import EndorsementDBAccessor
from arxiv_admin_api.endorsements import EndorsementCodeModel



class TestReadOnlys:
    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, arxiv_db):
        """Use the pytest fixture for database setup"""
        pass

    def test_see_papers(self) -> None:
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
            assert count > 0

    def test_academic_email(self) -> None:
        with DatabaseSession() as session:
            accessor = EndorsementDBAccessor(session)
            answer, reason = accessor.is_academic_email("")
            assert not answer
            answer, reason = accessor.is_academic_email("%A%")
            assert not answer
            answer, reason = accessor.is_academic_email("me@my.biz")
            assert not answer
            answer, reason = accessor.is_academic_email("a@amuz.gda.pl")
            assert answer
            answer, reason = accessor.is_academic_email("foobar@cornell.edu")
            assert answer
            answer, reason = accessor.is_academic_email("foobar@arxiv.org")
            # We may want to reconsider this...
            assert not answer

    def test_is_moderator(self) -> None:
        with DatabaseSession() as session:
            accessor = EndorsementDBAccessor(session)
            user_ids = session.query(TapirUser.user_id).all()
            count = 0
            for archive in ["astro-ph"]:
                for user_id in user_ids:
                    if accessor.is_moderator(user_id[0], archive=archive):
                        count += 1
            assert count == 2

    def test_get_category(self) -> None:
        with DatabaseSession() as session:
            accessor = EndorsementDBAccessor(session)
            for archive, subject_class, expect in [("cs", "AI", True), ("cs", "XX", False), ("econ", None, True)]:
                cat = accessor.get_category(archive, subject_class)
                assert (cat if expect else None) == cat

    def test_get_domain_info(self) -> None:
        with DatabaseSession() as session:
            accessor = EndorsementDBAccessor(session)
            for archive, subject_class, expect in [("cs", "AI", True), ("cs", '', False), ("econ", '', True)]:
                cat = accessor.get_category(archive, subject_class)
                assert cat is not None
                domain = accessor.get_domain_info(cat)
                assert domain is not None
                assert archive == domain.endorsement_domain

    def test_get_endorsements(self) -> None:
        with DatabaseSession() as session:
            accessor = EndorsementDBAccessor(session)
            user_ids = session.query(TapirUser.user_id).all()
            count = 0
            for user_id in user_ids:
                for archive, subject_class in [("cs", "AI"), ("cs", "CL")]:
                    result = accessor.get_endorsements(user_id[0], archive, subject_class)
                    if result is not None:
                        count = count + len(result)
            assert count == 2


    def test_get_questionable_categories(self) -> None:
        with DatabaseSession() as session:
            accessor = EndorsementDBAccessor(session)
            count = 0
            for archive, subject_class in [("cs", "AI"), ("cs", "CL"), ("math", "GM"), ("physics", "gen-ph")]:
                result = accessor.get_questionable_categories(archive, subject_class)
                if result is not None:
                    count = count + len(result)
            assert count == 2


    def test_get_papers_by_user(self) -> None:
        with DatabaseSession() as session:
            accessor = EndorsementDBAccessor(session)
            user_ids = session.query(TapirUser.user_id).all()
            count = 0
            window = [None, None]
            for user_id in user_ids:
                result = accessor.get_papers_by_user(user_id[0], "cs", window, require_author = True)
                if result is not None:
                    count = count + len(result)
            assert count == 143
            pass


class TestCreateEndorsement:
    @pytest.fixture(autouse=True)
    def setup_method(self, arxiv_db):
        """Use the pytest fixture for database setup"""
        self.audit_timestamp = datetime.fromisoformat("2025-01-01T00:00:00Z")  # Using now makes it
        self.tapir_session_id = 100

    def test_create_endorsement(self) -> None:
        client_host = "127.0.0.1"
        client_host_name = "no-place-like@home.biz"
        tracking_cookie = "I-ate-them-all"
        # Unfortunatnely, this seems to load the default

        endorsement_code = "R8T3GZ"
        with DatabaseSession() as session:
            er0 = EndorsementRequestModel.base_select(session).filter(EndorsementRequest.secret == endorsement_code).one_or_none()
            assert er0 is not None
            erm0 = EndorsementRequestModel.model_validate(er0)

            assert erm0.point_value == 0 # if this fails, you need to reset/reload the database

            accessor = EndorsementDBAccessor(session)
            endorser = accessor.get_user("591211")
            endorsee = accessor.get_user("1019756")

            code: EndorsementCodeModel = EndorsementCodeModel(
                preflight=False,
                endorser_id=str(endorser.id),
                endorsement_code=endorsement_code,
                comment="This is good",
                knows_personally=True,
                seen_paper=True,
                positive=True,
            )

            business = EndorsementBusiness(
                accessor,
                endorser,
                endorsee,
                self.audit_timestamp,
                archive=erm0.archive,
                subject_class=erm0.subject_class,
                endorsement_request=erm0,
                endorsement_code=code,
                session_id=str(self.tapir_session_id),
                remote_host_ip=client_host,
                remote_host_name=client_host_name,
                tracking_cookie=tracking_cookie,
            )
            assert business.can_submit()
            endorsement = business.submit_endorsement()
            assert endorsement is not None

        with DatabaseSession() as session:
            er1 = EndorsementRequestModel.base_select(session).filter(EndorsementRequest.secret == endorsement_code).one_or_none()
            erm1 = EndorsementRequestModel.model_validate(er1)
            assert erm1.point_value == 10



if __name__ == '__main__':
    pytest.main([__file__])
