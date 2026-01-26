from arxiv_admin_api.endorsement_requests import EndorsementRequestModel

from arxiv.db.models import EndorsementRequest, \
    TapirUser  # Category, EndorsementDomain, QuestionableCategory, Endorsement,

from arxiv_admin_api.biz.endorsement_biz import EndorsementBusiness
from arxiv_admin_api.biz.endorsement_io import EndorsementDBAccessor
from arxiv_admin_api.endorsements import EndorsementCodeModel


def test_email_patterns(reset_test_database, database_session, admin_api_db_only_client, admin_api_headers) -> None:
    endpoint = "/v1/email_patterns"
    response = admin_api_db_only_client.get(endpoint, headers=admin_api_headers)
    assert response.status_code == 200

