import pytest
from datetime import datetime


from arxiv_bizlogic.database import DatabaseSession
from arxiv.db.models import EndorsementRequest, TapirUser
from arxiv_admin_api.biz.endorsement_io import EndorsementDBAccessor
from arxiv_admin_api.biz.endorsement_biz import EndorsementBusiness
from arxiv_admin_api.endorsements import EndorsementCodeModel
from arxiv_admin_api.endorsement_requests import EndorsementRequestModel

from tests.scaffolding import setup_db_fixture, teardown_db_fixture


@pytest.fixture(scope="class", autouse=True)
def setup_db():
    """Fixture to set up and tear down the database."""
    setup_db_fixture()  # Setup before tests
    yield
    teardown_db_fixture()  # Teardown after tests


@pytest.fixture(scope="function")
def db_session():
    """Fixture to provide a database session."""
    with DatabaseSession() as session:
        yield session


@pytest.fixture
def test_audit_timestamp():
    return datetime.fromisoformat("2025-01-01T00:00:00Z")


@pytest.fixture
def test_tapir_session_id():
    return 100


@pytest.mark.usefixtures("setup_db")
class TestReadOnlys:

    def test_see_papers(self, db_session):
        accessor = EndorsementDBAccessor(db_session)
        user_ids = db_session.query(TapirUser.user_id).all()
        window = [None, None]
        count = 0
        for domain in ["cs"]:
            for user_id in user_ids:
                papers = accessor.get_papers_by_user(user_id[0], domain, window, require_author=False)
                if len(papers) >= 3:
                    print(f"Found {user_id[0]}")
                count += len(papers)
        assert count > 0

    def test_academic_email(self, db_session):
        accessor = EndorsementDBAccessor(db_session)

        # Test various email conditions
        for email, expected, reasoning in [
            ("", False, "Empty email is not academic"),
            ("%A%", False, "Invalid characters"),
            ("me@my.biz", False, "Non-academic domain"),
            ("a@amuz.gda.pl", True, "Valid academic domain"),
            ("foobar@cornell.edu", True, "Cornell is academic"),
            ("foobar@arxiv.org", False, "arxiv.org may fail intentionally"),
        ]:
            answer, reason = accessor.is_academic_email(email)
            assert answer == expected, f"Email: {email}, Reason: {reason}"

    def test_is_moderator(self, db_session):
        accessor = EndorsementDBAccessor(db_session)
        user_ids = db_session.query(TapirUser.user_id).all()
        count = 0
        for archive in ["astro-ph"]:
            for user_id in user_ids:
                if accessor.is_moderator(user_id[0], archive=archive):
                    count += 1
        assert count == 2

    def test_get_category(self, db_session):
        accessor = EndorsementDBAccessor(db_session)
        for archive, subject_class, expect in [("cs", "AI", True), ("cs", "XX", False), ("econ", None, True)]:
            cat = accessor.get_category(archive, subject_class)
            assert (cat is not None) == expect

    def test_get_domain_info(self, db_session):
        accessor = EndorsementDBAccessor(db_session)
        for archive, subject_class in [("cs", "AI"), ("cs", ""), ("econ", "")]:
            cat = accessor.get_category(archive, subject_class)
            assert cat is not None
            domain = accessor.get_domain_info(cat)
            assert domain is not None
            assert archive == domain.endorsement_domain

    def test_get_endorsements(self, db_session):
        accessor = EndorsementDBAccessor(db_session)
        user_ids = db_session.query(TapirUser.user_id).all()
        count = 0
        for user_id in user_ids:
            for archive, subject_class in [("cs", "AI"), ("cs", "CL")]:
                result = accessor.get_endorsements(user_id[0], archive, subject_class)
                if result is not None:
                    count += len(result)
        assert count == 2

    def test_get_questionable_categories(self, db_session):
        accessor = EndorsementDBAccessor(db_session)
        count = 0
        for archive, subject_class in [("cs", "AI"), ("cs", "CL"), ("math", "GM"), ("physics", "gen-ph")]:
            result = accessor.get_questionable_categories(archive, subject_class)
            if result is not None:
                count += len(result)
        assert count == 2

    def test_get_papers_by_user(self, db_session):
        accessor = EndorsementDBAccessor(db_session)
        user_ids = db_session.query(TapirUser.user_id).all()
        count = 0
        window = [None, None]
        for user_id in user_ids:
            result = accessor.get_papers_by_user(user_id[0], "cs", window, require_author=True)
            if result is not None:
                count += len(result)
        assert count == 143


@pytest.mark.usefixtures("setup_db")
class TestCreateEndorsement:

    def test_create_endorsement(self, db_session, test_audit_timestamp, test_tapir_session_id):
        client_host = "127.0.0.1"
        client_host_name = "no-place-like@home.biz"
        tracking_cookie = "I-ate-them-all"

        endorsement_code = "R8T3GZ"
        er0 = EndorsementRequestModel.base_select(db_session).filter(
            EndorsementRequest.secret == endorsement_code
        ).one_or_none()
        assert er0 is not None
        erm0 = EndorsementRequestModel.model_validate(er0)
        assert erm0.point_value == 0  # Ensure proper data reset

        accessor = EndorsementDBAccessor(db_session)
        endorser = accessor.get_user("591211")
        endorsee = accessor.get_user("1019756")

        code = EndorsementCodeModel(
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
            code,
            endorser,
            endorsee,
            erm0,
            str(test_tapir_session_id),
            client_host,
            client_host_name,
            test_audit_timestamp,
            tracking_cookie,
        )
        assert business.can_submit()
        endorsement = business.submit_endorsement()
        assert endorsement is not None

        er1 = EndorsementRequestModel.base_select(db_session).filter(
            EndorsementRequest.secret == endorsement_code
        ).one_or_none()
        erm1 = EndorsementRequestModel.model_validate(er1)
        assert erm1.point_value == 10
