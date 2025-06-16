import pytest

from arxiv_admin_api.ownership_requests import CreateOwnershipRequestModel


@pytest.mark.usefixtures("arxiv_db", "test_env", "api_client", "api_headers")
class TestCreateOwnershipRequest:

    def test_create_ownership_request(self, arxiv_db, test_env, api_client, api_headers):
        ownership_request = CreateOwnershipRequestModel(
            user_id="1",
            arxiv_ids=["2412.19977",
                       "2412.20648",
                       "2501.02397",
                       "2501.04271",
                       "2501.05497",
                       "2501.05589",
                       "2501.11682",
                       "2501.11780",
                       "2501.12611",
                       "2501.13090",
                       "2501.13755",
                       "2501.16458",
                       "2501.17851",
                       "2501.18042",
                       "2501.18341",
                       "2502.00313",
                       "2502.02303",
                       "2502.03302",
                       "2502.04619"
                       ],
            remote_addr="127.0.0.1"
        )
        response1 = api_client.post("/v1/ownership_requests", json=ownership_request.model_dump(), headers=api_headers)
        assert response1.status_code == 200
