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

    @property
    def user_id(self) -> int:
        return 303688

    @property
    def doc_id(self) -> int:
        return 2231318

    @property
    def session_id(self) -> int:
        return 8788860


    def test_authorize_endpoint_success(self, arxiv_db, test_env, api_client):
        """Test successful paper ownership authorization via password"""

        with DatabaseSession() as db_session:
            paper_pw: PaperPw | None = db_session.query(PaperPw).filter(PaperPw.document_id == self.doc_id).one_or_none()
            assert paper_pw is not None

            doc = db_session.query(Document).filter(Document.document_id == self.doc_id).one_or_none()
            assert doc is not None

        headers = generate_request_headers(
            test_env,
            tapir_session_id=self.session_id,
            user_id=self.user_id,
        )

        # Prepare the authorization request
        auth_request = PaperAuthRequest(
            paper_id=str(doc.paper_id),
            password=str(paper_pw.password_enc),
            user_id=str(self.user_id),  # Assuming this matches the authenticated user
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
            ownerships = db_session.query(PaperOwner).filter(PaperOwner.user_id == self.user_id).all()
            assert len(ownerships) == 1

            ownership = db_session.query(PaperOwner).filter(
                PaperOwner.user_id == self.user_id,
                PaperOwner.document_id == self.doc_id
            ).one_or_none()

            assert ownership is not None
            assert ownership.valid
            assert ownership.flag_author
            assert not ownership.flag_auto


    def test_authorize_endpoint_wrong_password(self, arxiv_db, test_env, api_client):
        """Test authorization failure with wrong password"""

        with DatabaseSession() as db_session:
            paper_pw: PaperPw | None = db_session.query(PaperPw).filter(PaperPw.document_id == self.doc_id).one_or_none()
            assert paper_pw is not None

            doc = db_session.query(Document).filter(Document.document_id == self.doc_id).one_or_none()
            assert doc is not None

        headers = generate_request_headers(
            test_env,
            tapir_session_id=self.session_id,
            user_id=self.user_id,
        )

        # Prepare the authorization request
        auth_request = PaperAuthRequest(
            paper_id=str(doc.paper_id),
            password="*****",
            user_id=str(self.user_id),  # Assuming this matches the authenticated user
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
        assert response.status_code == 400

        with DatabaseSession() as db_session:
            ownership = db_session.query(PaperOwner).filter(
                PaperOwner.user_id == self.user_id,
                PaperOwner.document_id == self.doc_id
            ).one_or_none()

            assert ownership is None


    def test_authorize_endpoint_invalid_paper_id(self, arxiv_db, test_env, api_client):
        """Test authorization failure with invalid paper ID"""

        headers = generate_request_headers(
            test_env,
            tapir_session_id=self.session_id,
            user_id=self.user_id,
        )

        # Prepare the authorization request with non-existent paper
        auth_request = PaperAuthRequest(
            paper_id="9999.99999",
            password="any_password",
            user_id=str(self.user_id),
            verify_id=True,
            is_author=True
        )

        # Make the API request
        response = api_client.post(
            "/v1/paper_owners/authorize",
            headers=headers,
            json=auth_request.model_dump()
        )

        # Assert failure response
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]


    def test_authorize_endpoint_malformed_paper_id(self, arxiv_db, db_session: Session, test_env, api_client):
        """Test authorization failure with malformed paper ID"""

        headers = generate_request_headers(
            test_env,
            tapir_session_id=self.session_id,
            user_id=self.user_id,
        )

        # Prepare the authorization request with non-existent paper
        auth_request = PaperAuthRequest(
            paper_id="foo###12210021",
            password="any_password",
            user_id=str(self.user_id),
            verify_id=True,
            is_author=True
        )

        # Make the API request
        response = api_client.post(
            "/v1/paper_owners/authorize",
            headers=headers,
            json=auth_request.model_dump()
        )

        # Assert failure response
        assert response.status_code == 400
        assert "does not exist" in response.json()["detail"]


    def test_authorize_endpoint_verify_id_false(self, arxiv_db, db_session: Session, test_env, api_client):
        """Test authorization failure when verify_id is False"""

        with DatabaseSession() as db_session:
            paper_pw: PaperPw | None = db_session.query(PaperPw).filter(PaperPw.document_id == self.doc_id).one_or_none()
            assert paper_pw is not None

            doc = db_session.query(Document).filter(Document.document_id == self.doc_id).one_or_none()
            assert doc is not None

        headers = generate_request_headers(
            test_env,
            tapir_session_id=self.session_id,
            user_id=self.user_id,
        )

        # Prepare the authorization request
        auth_request = PaperAuthRequest(
            paper_id=str(doc.paper_id),
            password=str(paper_pw.password_enc),
            user_id=str(self.user_id),  # Assuming this matches the authenticated user
            verify_id=False,  # <------
            is_author=True
        )

        # Make the API request
        response = api_client.post(
            "/v1/paper_owners/authorize",
            headers=headers,
            json=auth_request.model_dump()
        )

        # Assert successful response
        assert response.status_code == 400

        with DatabaseSession() as db_session:
            ownership = db_session.query(PaperOwner).filter(
                PaperOwner.user_id == self.user_id,
                PaperOwner.document_id == self.doc_id
            ).one_or_none()
            assert ownership is not None



    def test_authorize_endpoint_existing_ownership(self, arxiv_db, db_session: Session, test_env, api_client):
        """Test authorization failure when ownership already exists"""

        with DatabaseSession() as db_session:
            paper_pw: PaperPw | None = db_session.query(PaperPw).filter(PaperPw.document_id == self.doc_id).one_or_none()
            assert paper_pw is not None

            doc = db_session.query(Document).filter(Document.document_id == self.doc_id).one_or_none()
            assert doc is not None

            # Create existing ownership
            existing_ownership = PaperOwner(
                user_id=self.user_id,
                document_id=self.doc_id,
                date=1673481600,
                added_by=1,
                remote_addr="127.0.0.1",
                remote_host="localhost",
                tracking_cookie="test_cookie",
                valid=True,
                flag_author=True,
                flag_auto=False
            )
            db_session.add(existing_ownership)
            db_session.commit()


        headers = generate_request_headers(
            test_env,
            tapir_session_id=self.session_id,
            user_id=self.user_id,
        )

        # Prepare the authorization request
        auth_request = PaperAuthRequest(
            paper_id=doc.paper_id,
            password=paper_pw.password_enc,
            user_id="123456",
            verify_id=True,
            is_author=True
        )

        # Make the API request
        response = api_client.post(
            "/v1/paper_owners/authorize",
            headers=api_headers,
            json=auth_request.model_dump()
        )

        # Assert conflict response
        assert response.status_code == 409
        assert "have the ownership" in response.json()["detail"]
