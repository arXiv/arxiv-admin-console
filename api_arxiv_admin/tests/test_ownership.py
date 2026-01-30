from arxiv.db.models import Document, PaperOwner, PaperPw
# OwnershipRequest, OwnershipRequestsAudit, t_arXiv_ownership_requests_papers,
from arxiv_admin_api.paper_owners import PaperAuthRequest
from sqlalchemy.orm import Session
from conftest import generate_request_headers


class _TestParams:
    USER_ID: int = 303688
    DOC_ID: int = 2231318
    SESSION_ID: int = 8788860



def test_authorize_endpoint_wrong_password(database_session, reset_test_database, test_env, admin_api_db_only_client):
    """Test authorization failure with wrong password"""

    with database_session() as db_session:
        paper_pw: PaperPw | None = db_session.query(PaperPw).filter(PaperPw.document_id == _TestParams.DOC_ID).one_or_none()
        assert paper_pw is not None

        doc = db_session.query(Document).filter(Document.document_id == _TestParams.DOC_ID).one_or_none()
        assert doc is not None


    # Prepare the authorization request
    auth_request = PaperAuthRequest(
        paper_id=str(doc.paper_id),
        password="*****",
        user_id=str(_TestParams.USER_ID),  # Assuming this matches the authenticated user
        verify_id=True,
        is_author=True
    )

    headers = generate_request_headers(
        test_env,
        tapir_session_id=_TestParams.SESSION_ID,
        user_id=_TestParams.USER_ID,
    )

    # Make the API request
    response = admin_api_db_only_client.post(
        "/v1/paper_owners/authorize",
        headers=headers,
        json=auth_request.model_dump()
    )

    # Assert successful response
    assert response.status_code == 400

    with database_session() as db_session:
        ownership = db_session.query(PaperOwner).filter(
            PaperOwner.user_id == _TestParams.USER_ID,
            PaperOwner.document_id == _TestParams.DOC_ID
        ).one_or_none()

        assert ownership is None


def test_authorize_endpoint_invalid_paper_id(reset_test_database, test_env, admin_api_db_only_client):
    """Test authorization failure with invalid paper ID"""

    headers = generate_request_headers(
        test_env,
        tapir_session_id=_TestParams.SESSION_ID,
        user_id=_TestParams.USER_ID,
    )

    # Prepare the authorization request with non-existent paper
    auth_request = PaperAuthRequest(
        paper_id="9999.99999",
        password="any_password",
        user_id=str(_TestParams.USER_ID),
        verify_id=True,
        is_author=True
    )

    # Make the API request
    response = admin_api_db_only_client.post(
        "/v1/paper_owners/authorize",
        headers=headers,
        json=auth_request.model_dump()
    )

    # Assert failure response
    assert response.status_code == 400
    assert "does not exist" in response.json()["detail"]


def test_authorize_endpoint_malformed_paper_id(reset_test_database, database_session, test_env, admin_api_db_only_client):
    """Test authorization failure with malformed paper ID"""

    headers = generate_request_headers(
        test_env,
        tapir_session_id=_TestParams.SESSION_ID,
        user_id=_TestParams.USER_ID,
    )

    # Prepare the authorization request with non-existent paper
    auth_request = PaperAuthRequest(
        paper_id="foo###12210021",
        password="any_password",
        user_id=str(_TestParams.USER_ID),
        verify_id=True,
        is_author=True
    )

    # Make the API request
    response = admin_api_db_only_client.post(
        "/v1/paper_owners/authorize",
        headers=headers,
        json=auth_request.model_dump()
    )

    # Assert failure response
    assert response.status_code == 400
    assert "Paper ID 'foo###12210021' is ill-formed." in response.json()["detail"]


def test_authorize_endpoint_verify_id_false(reset_test_database, database_session, test_env, admin_api_db_only_client):
    """Test authorization failure when verify_id is False"""

    with database_session() as db_session:
        paper_pw: PaperPw | None = db_session.query(PaperPw).filter(PaperPw.document_id == _TestParams.DOC_ID).one_or_none()
        assert paper_pw is not None

        doc = db_session.query(Document).filter(Document.document_id == _TestParams.DOC_ID).one_or_none()
        assert doc is not None

    headers = generate_request_headers(
        test_env,
        tapir_session_id=_TestParams.SESSION_ID,
        user_id=_TestParams.USER_ID,
    )

    # Prepare the authorization request
    auth_request = PaperAuthRequest(
        paper_id=str(doc.paper_id),
        password=str(paper_pw.password_enc),
        user_id=str(_TestParams.USER_ID),  # Assuming this matches the authenticated user
        verify_id=False,
        is_author=True
    )

    # Make the API request
    response = admin_api_db_only_client.post(
        "/v1/paper_owners/authorize",
        headers=headers,
        json=auth_request.model_dump()
    )

    # Assert successful response
    assert response.status_code == 400

    with database_session() as db_session:
        ownership = db_session.query(PaperOwner).filter(
            PaperOwner.user_id == _TestParams.USER_ID,
            PaperOwner.document_id == _TestParams.DOC_ID
        ).one_or_none()
        assert ownership is None



def test_authorize_endpoint_success(reset_test_database, database_session, test_env, admin_api_db_only_client):
    """Test successful paper ownership authorization via password"""

    with database_session() as db_session:
        paper_pw: PaperPw | None = db_session.query(PaperPw).filter(PaperPw.document_id == _TestParams.DOC_ID).one_or_none()
        assert paper_pw is not None

        doc = db_session.query(Document).filter(Document.document_id == _TestParams.DOC_ID).one_or_none()
        assert doc is not None

    headers = generate_request_headers(
        test_env,
        tapir_session_id=_TestParams.SESSION_ID,
        user_id=_TestParams.USER_ID,
    )

    # Prepare the authorization request
    auth_request = PaperAuthRequest(
        paper_id=str(doc.paper_id),
        password=str(paper_pw.password_enc),
        user_id=str(_TestParams.USER_ID),  # Assuming this matches the authenticated user
        verify_id=True,
        is_author=True
    )

    # Make the API request
    response = admin_api_db_only_client.post(
        "/v1/paper_owners/authorize",
        headers=headers,
        json=auth_request.model_dump()
    )

    # Assert successful response
    assert response.status_code == 201

    with database_session() as db_session:
        # Verify that ownership record was created
        ownerships = db_session.query(PaperOwner).filter(PaperOwner.user_id == _TestParams.USER_ID).all()
        assert len(ownerships) == 2

        ownership = db_session.query(PaperOwner).filter(
            PaperOwner.user_id == _TestParams.USER_ID,
            PaperOwner.document_id == _TestParams.DOC_ID
        ).one_or_none()

        assert ownership is not None
        assert ownership.valid
        assert ownership.flag_author
        assert not ownership.flag_auto


    # Make the API request 2nd time
    response = admin_api_db_only_client.post(
        "/v1/paper_owners/authorize",
        headers=headers,
        json=auth_request.model_dump()
    )

    # Assert conflict response
    assert response.status_code == 409
    assert "have the ownership" in response.json()["detail"]
