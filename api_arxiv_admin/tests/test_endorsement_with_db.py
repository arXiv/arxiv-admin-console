from typing import Optional
import pytest
from arxiv_admin_api.endorsement_requests import EndorsementRequestModel

from arxiv.db.models import EndorsementRequest, TapirUser
# Category, EndorsementDomain, QuestionableCategory, Endorsement,

from arxiv_admin_api.biz.endorsement_biz import EndorsementBusiness
from arxiv_admin_api.biz.endorsement_io import EndorsementDBAccessor
from arxiv_admin_api.endorsements import EndorsementCodeModel
from datetime import datetime

from arxiv_admin_api.public_users import PublicUserModel


def test_see_papers(reset_test_database, database_session) -> None:
    with database_session() as session:
        accessor = EndorsementDBAccessor(session)
        user_ids = session.query(TapirUser.user_id).all()
        window: Optional[list[datetime]] = None
        count = 0
        for domain in ["cs"]:
            for user_id in user_ids:
                papers = accessor.get_papers_by_user(user_id[0], domain, window, require_author=False)
                if len(papers) >= 3:
                    print("Found {}".format(user_id[0]))
                count = count + len(papers)
        assert count > 0

def test_academic_email(reset_test_database, database_session) -> None:
    with database_session() as session:
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

def test_is_moderator(reset_test_database, database_session) -> None:
    with database_session() as session:
        accessor = EndorsementDBAccessor(session)
        user_ids = session.query(TapirUser.user_id).all()
        count = 0
        for archive in ["astro-ph"]:
            for user_id in user_ids:
                if accessor.is_moderator(user_id[0], archive=archive):
                    count += 1
        assert count == 2

def test_get_category(reset_test_database, database_session) -> None:
    with database_session() as session:
        accessor = EndorsementDBAccessor(session)
        for archive, subject_class, expect in [("cs", "AI", True), ("cs", "XX", False), ("econ", None, True)]:
            cat = accessor.get_category(archive, subject_class)
            assert (cat if expect else None) == cat

def test_get_domain_info(reset_test_database, database_session) -> None:
    with database_session() as session:
        accessor = EndorsementDBAccessor(session)
        for archive, subject_class, expect in [("cs", "AI", True), ("cs", '', False), ("econ", '', True)]:
            cat = accessor.get_category(archive, subject_class)
            assert cat is not None
            domain = accessor.get_domain_info(cat)
            assert domain is not None
            assert archive == domain.endorsement_domain

def test_get_endorsements(reset_test_database, database_session) -> None:
    with database_session() as session:
        accessor = EndorsementDBAccessor(session)
        user_ids = session.query(TapirUser.user_id).all()
        count = 0
        for user_id in user_ids:
            for archive, subject_class in [("cs", "AI"), ("cs", "CL")]:
                result = accessor.get_endorsements(user_id[0], archive, subject_class)
                if result is not None:
                    count = count + len(result)
        assert count == 2


def test_get_questionable_categories(reset_test_database, database_session) -> None:
    with database_session() as session:
        accessor = EndorsementDBAccessor(session)
        count = 0
        for archive, subject_class in [("cs", "AI"), ("cs", "CL"), ("math", "GM"), ("physics", "gen-ph")]:
            result = accessor.get_questionable_categories(archive, subject_class)
            if result is not None:
                count = count + len(result)
        assert count == 2


def test_get_papers_by_user(reset_test_database, database_session) -> None:
    with database_session() as session:
        accessor = EndorsementDBAccessor(session)
        user_ids = session.query(TapirUser.user_id).all()
        count = 0
        window = None
        for user_id in user_ids:
            result = accessor.get_papers_by_user(user_id[0], "cs", window, require_author = True)
            if result is not None:
                count = count + len(result)
        assert count == 554
        pass


def test_create_endorsement(reset_test_database, database_session) -> None:
    client_host = "127.0.0.1"
    client_host_name = "no-place-like@home.biz"
    tracking_cookie = "I-ate-them-all"
    audit_timestamp = datetime.fromisoformat("2025-01-01T00:00:00Z")  # Using now makes it
    tapir_session_id = 100

    # Unfortunatnely, this seems to load the default

    endorsement_code = "R8T3GZ"
    with database_session() as session:
        er0 = EndorsementRequestModel.base_select(session).filter(EndorsementRequest.secret == endorsement_code).one_or_none()
        assert er0 is not None
        erm0 = EndorsementRequestModel.model_validate(er0)

        assert erm0.point_value == 0 # if this fails, you need to reset/reload the database

        accessor = EndorsementDBAccessor(session)
        endorser = accessor.get_user("591211")
        endorsee_0 = accessor.get_user("1019756")
        # this would be a test bug
        assert endorser is not None
        assert endorsee_0 is not None
        endorsee = PublicUserModel.model_validate(endorsee_0.model_dump())

        code: EndorsementCodeModel = EndorsementCodeModel(
            preflight=False,
            endorser_id=str(endorser.id),
            endorsement_code=endorsement_code,
            comment="This is good",
            knows_personally=True,
            seen_paper=True,
            positive=True,
        )

        assert erm0.archive is not None
        assert erm0.subject_class is not None

        business = EndorsementBusiness(
            accessor,
            endorser,
            endorsee,
            audit_timestamp,
            archive=erm0.archive,
            subject_class=erm0.subject_class,
            endorsement_request=erm0,
            endorsement_code=code,
            session_id=str(tapir_session_id),
            remote_host_ip=client_host,
            remote_host_name=client_host_name,
            tracking_cookie=tracking_cookie,
        )
        assert business.can_submit()
        endorsement = business.submit_endorsement()
        assert endorsement is not None

    with database_session() as session:
        er1 = EndorsementRequestModel.base_select(session).filter(EndorsementRequest.secret == endorsement_code).one_or_none()
        erm1 = EndorsementRequestModel.model_validate(er1)
        assert erm1.point_value == 10

