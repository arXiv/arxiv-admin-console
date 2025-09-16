import pytest
from arxiv.db.models import OwnershipRequest, OwnershipRequestsAudit, t_arXiv_ownership_requests_papers, Document, \
    PaperOwner, PaperPw
from arxiv_bizlogic.database import DatabaseSession
from sqlalchemy import and_

from arxiv_admin_api.ownership_requests import CreateOwnershipRequestModel, OwnershipRequestModel, \
    OwnershipRequestSubmit
from arxiv_admin_api.paper_owners import PaperAuthRequest
from sqlalchemy.orm import Session
import json
from conftest import generate_request_headers


@pytest.mark.usefixtures("arxiv_db", "test_env", "api_client")
class TestOwnershipByPaperPassword:
    def test_authorize_endpoint_success(self, arxiv_db, test_env, api_client):
        """Test successful paper ownership authorization via password"""
        user_id = 303688
        doc_id = 2231318
        session_id = 8788860

        with DatabaseSession() as db_session:
            paper_pw: PaperPw | None = db_session.query(PaperPw).filter(PaperPw.document_id == doc_id).one_or_none()
            assert paper_pw is not None

            doc = db_session.query(Document).filter(Document.document_id == doc_id).one_or_none()
            assert doc is not None

        headers = generate_request_headers(
            test_env,
            tapir_session_id=session_id,
            user_id=user_id,
        )

        # Prepare the authorization request
        auth_request = PaperAuthRequest(
            paper_id=str(doc.paper_id),
            password=str(paper_pw.password_enc),
            user_id=str(user_id),  # Assuming this matches the authenticated user
            verify_id=True,
            is_author=True
        )

        # Make the API request
        response = api_client.post(
            "/v1/paper_owners/authorize",
            headers=headers,
            json=auth_request.model_dump()
        )

        # Assert successful response
        assert response.status_code == 201

        with DatabaseSession() as db_session:
            # Verify that ownership record was created
            ownerships = db_session.query(PaperOwner).filter(PaperOwner.user_id == user_id).all()
            assert len(ownerships) == 1

            ownership = db_session.query(PaperOwner).filter(
                PaperOwner.user_id == user_id,
                PaperOwner.document_id == doc_id
            ).one_or_none()

            assert ownership is not None
            assert ownership.valid
            assert ownership.flag_author
            assert not ownership.flag_auto


    def test_authorize_endpoint_wrong_password(self, arxiv_db, db_session: Session, test_env, api_client, api_headers):
        """Test authorization failure with wrong password"""

        # Create a test document
        test_paper_id = "2301.00002"
        document = Document(
            document_id=12346,
            paper_id=test_paper_id,
            title="Test Paper Title 2",
            submitter_id=999,
            dated=1673481600
        )
        db_session.add(document)

        # Create a paper password for the document
        correct_password = "correct_password_123"
        paper_pw = PaperPw(
            document_id=12346,
            password_storage=0,
            password_enc=correct_password
        )
        db_session.add(paper_pw)
        db_session.commit()

        # Prepare the authorization request with wrong password
        auth_request = PaperAuthRequest(
            paper_id=test_paper_id,
            password="wrong_password",
            user_id="123456",
            verify_id=True,
            is_author=True
        )

        # Make the API request
        response = api_client.post(
            "/paper_owners/authorize",
            headers=api_headers,
            json=auth_request.model_dump()
        )

        # Assert failure response
        assert response.status_code == 400
        assert "Incorrect paper password" in response.json()["detail"]

        # Verify that no ownership record was created
        ownership = db_session.query(PaperOwner).filter(
            PaperOwner.user_id == 123456,
            PaperOwner.document_id == 12346
        ).first()

        assert ownership is None

    def test_authorize_endpoint_invalid_paper_id(self, arxiv_db, db_session: Session, test_env, api_client,
                                                 api_headers):
        """Test authorization failure with invalid paper ID"""

        # Prepare the authorization request with non-existent paper
        auth_request = PaperAuthRequest(
            paper_id="9999.99999",
            password="any_password",
            user_id="123456",
            verify_id=True,
            is_author=True
        )

        # Make the API request
        response = api_client.post(
            "/paper_owners/authorize",
            headers=api_headers,
            json=auth_request.model_dump()
        )

        # Assert failure response
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]

    def test_authorize_endpoint_malformed_paper_id(self, arxiv_db, db_session: Session, test_env, api_client,
                                                   api_headers):
        """Test authorization failure with malformed paper ID"""

        # Prepare the authorization request with malformed paper ID
        auth_request = PaperAuthRequest(
            paper_id="invalid-paper-id",
            password="any_password",
            user_id="123456",
            verify_id=True,
            is_author=True
        )

        # Make the API request
        response = api_client.post(
            "/paper_owners/authorize",
            headers=api_headers,
            json=auth_request.model_dump()
        )

        # Assert failure response
        assert response.status_code == 400
        assert "ill-formed" in response.json()["detail"]

    def test_authorize_endpoint_verify_id_false(self, arxiv_db, db_session: Session, test_env, api_client, api_headers):
        """Test authorization failure when verify_id is False"""

        # Prepare the authorization request with verify_id=False
        auth_request = PaperAuthRequest(
            paper_id="2301.00001",
            password="any_password",
            user_id="123456",
            verify_id=False,
            is_author=True
        )

        # Make the API request
        response = api_client.post(
            "/paper_owners/authorize",
            headers=api_headers,
            json=auth_request.model_dump()
        )

        # Assert failure response
        assert response.status_code == 400
        assert "verify your contact information" in response.json()["detail"]

    def test_authorize_endpoint_existing_ownership(self, arxiv_db, db_session: Session, test_env, api_client,
                                                   api_headers):
        """Test authorization failure when ownership already exists"""

        # Create a test document
        test_paper_id = "2301.00003"
        document = Document(
            document_id=12347,
            paper_id=test_paper_id,
            title="Test Paper Title 3",
            submitter_id=999,
            dated=1673481600
        )
        db_session.add(document)

        # Create a paper password
        test_password = "test_password_123"
        paper_pw = PaperPw(
            document_id=12347,
            password_storage=0,
            password_enc=test_password
        )
        db_session.add(paper_pw)

        # Create existing ownership
        existing_ownership = PaperOwner(
            user_id=123456,
            document_id=12347,
            date=1673481600,
            added_by=123456,
            remote_addr="127.0.0.1",
            remote_host="localhost",
            tracking_cookie="test_cookie",
            valid=True,
            flag_author=True,
            flag_auto=False
        )
        db_session.add(existing_ownership)
        db_session.commit()

        # Prepare the authorization request
        auth_request = PaperAuthRequest(
            paper_id=test_paper_id,
            password=test_password,
            user_id="123456",
            verify_id=True,
            is_author=True
        )

        # Make the API request
        response = api_client.post(
            "/paper_owners/authorize",
            headers=api_headers,
            json=auth_request.model_dump()
        )

        # Assert conflict response
        assert response.status_code == 409
        assert "have the ownership" in response.json()["detail"]

    def test_authorize_endpoint_auto_flag(self, arxiv_db, db_session: Session, test_env, api_client, api_headers):
        """Test that flag_auto is set correctly when user is the submitter"""

        # Create a test document where user is the submitter
        test_paper_id = "2301.00004"
        user_id = 123456
        document = Document(
            document_id=12348,
            paper_id=test_paper_id,
            title="Test Paper Title 4",
            submitter_id=user_id,  # Same as claiming user
            dated=1673481600
        )
        db_session.add(document)

        # Create a paper password
        test_password = "test_password_123"
        paper_pw = PaperPw(
            document_id=12348,
            password_storage=0,
            password_enc=test_password
        )
        db_session.add(paper_pw)
        db_session.commit()

        # Prepare the authorization request
        auth_request = PaperAuthRequest(
            paper_id=test_paper_id,
            password=test_password,
            user_id=str(user_id),
            verify_id=True,
            is_author=False  # Set as non-author to test flag handling
        )

        # Make the API request
        response = api_client.post(
            "/paper_owners/authorize",
            headers=api_headers,
            json=auth_request.model_dump()
        )

        # Assert successful response
        assert response.status_code == 201

        # Verify that ownership record was created with correct flags
        ownership = db_session.query(PaperOwner).filter(
            PaperOwner.user_id == user_id,
            PaperOwner.document_id == 12348
        ).first()

        assert ownership is not None
        assert ownership.valid is True
        assert ownership.flag_author is False  # Should respect the request
        assert ownership.flag_auto == 1  # Should be auto since user is submitter
