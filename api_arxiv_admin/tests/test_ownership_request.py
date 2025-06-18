import pytest
from arxiv.db.models import OwnershipRequest, OwnershipRequestsAudit, t_arXiv_ownership_requests_papers

from arxiv_admin_api.ownership_requests import CreateOwnershipRequestModel, OwnershipRequestModel, \
    OwnershipRequestSubmit
from sqlalchemy.orm import Session


@pytest.mark.usefixtures("arxiv_db", "test_env", "api_client", "api_headers")
class TestCreateOwnershipRequest:

    def test_create_ownership_request(self, arxiv_db, db_session: Session, test_env, api_client, api_headers):
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
        # b'{"id":1,"user_id":1,"endorsement_request_id":null,"workflow_status":"pending","date":"2025-06-17T04:00:00Z","document_ids":[2650641,2651312,2654267,2656141,2657367,2657459,2663552,2663650,2664481,2664960,2665625,2668328,2669721,2669912,2670211,2671590,2673580,2674579,2675896],"paper_ids":["2412.19977","2412.20648","2501.02397","2501.04271","2501.05497","2501.05589","2501.11682","2501.11780","2501.12611","2501.13090","2501.13755","2501.16458","2501.17851","2501.18042","2501.18341","2502.00313","2502.02303","2502.03302","2502.04619"]}'
        ownership_request = OwnershipRequestModel.model_validate(response1.json())
        doc_ids = set([2650641,2651312,2654267,2656141,2657367,2657459,2663552,2663650,2664481,2664960,2665625,2668328,2669721,2669912,2670211,2671590,2673580,2674579,2675896])
        assert doc_ids == set(ownership_request.document_ids)
        ownership_request_id = ownership_request.id
        row: OwnershipRequest = db_session.query(OwnershipRequest).filter(OwnershipRequest.request_id == ownership_request_id).one_or_none()
        assert row is not None

        or_audit: OwnershipRequestsAudit | None = db_session.query(OwnershipRequestsAudit).filter(OwnershipRequestsAudit.request_id == ownership_request_id).one_or_none()
        assert or_audit is not None
        assert or_audit.session_id == 23276916

        requested_papers = db_session.query(
            t_arXiv_ownership_requests_papers.c.document_id
        ).filter(
            t_arXiv_ownership_requests_papers.c.request_id == ownership_request_id
        ).all()

        assert doc_ids == set([row[0] for row in requested_papers])


    def test_accept_ownership_request(self, arxiv_db, db_session: Session, test_env, api_client, api_headers):
        response1 = api_client.get("/v1/ownership_requests/1", headers=api_headers)
        assert response1.status_code == 200

        or1 = OwnershipRequestModel.model_validate(response1.json())

        document_ids = [
            2650641, 2651312, 2654267, 2656141, 2657367,
            2657459, 2663552, 2663650, 2664481, 2664960,
            2665625, 2668328, 2669721, 2669912, 2670211,
            2671590, 2673580, 2674579, 2675896
        ]

        # Select half of the documents (rounded down if odd number)
        selected_documents = document_ids[:len(document_ids) // 2]

        or_submit = OwnershipRequestSubmit(
            user_id = 1,
            workflow_status = "accepted",
            document_ids = document_ids,
            selected_documents = selected_documents
        )

        response2 = api_client.put("/v1/ownership_requests/1", headers=api_headers, json=or_submit.model_dump())
        assert response2.status_code == 200

        or2 = OwnershipRequestModel.model_validate(response2.json())
