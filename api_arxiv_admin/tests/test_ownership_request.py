import pytest
from arxiv.db.models import OwnershipRequest, OwnershipRequestsAudit, t_arXiv_ownership_requests_papers

from arxiv_admin_api.ownership_requests import CreateOwnershipRequestModel, OwnershipRequestModel, \
    OwnershipRequestSubmit, WorkflowStatus
from sqlalchemy.orm import Session

from tests.conftest import generate_request_headers


class _TestParams:
    USER_ID: int = 303688
    DOC_ID: int = 2231318
    SESSION_ID: int = 8788860


def test_create_ownership_request(reset_test_database, database_session: Session, test_env, admin_api_db_only_client):
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

    api_headers = generate_request_headers(
        test_env,
        user_id=_TestParams.USER_ID,
        tapir_session_id=_TestParams.SESSION_ID
    )

    response1 = admin_api_db_only_client.post("/v1/ownership_requests", json=ownership_request.model_dump(), headers=api_headers)
    assert response1.status_code == 200
    # b'{"id":1,"user_id":1,"endorsement_request_id":null,"workflow_status":"pending","date":"2025-06-17T04:00:00Z","document_ids":[2650641,2651312,2654267,2656141,2657367,2657459,2663552,2663650,2664481,2664960,2665625,2668328,2669721,2669912,2670211,2671590,2673580,2674579,2675896],"paper_ids":["2412.19977","2412.20648","2501.02397","2501.04271","2501.05497","2501.05589","2501.11682","2501.11780","2501.12611","2501.13090","2501.13755","2501.16458","2501.17851","2501.18042","2501.18341","2502.00313","2502.02303","2502.03302","2502.04619"]}'

    ownership_request_response = OwnershipRequestModel.model_validate(response1.json())

    doc_ids = set(
        [2650641, 2651312, 2654267, 2656141, 2657367, 2657459, 2663552, 2663650, 2664481, 2664960, 2665625, 2668328,
         2669721, 2669912, 2670211, 2671590, 2673580, 2674579, 2675896])
    assert doc_ids == set(ownership_request_response.document_ids or [])
    ownership_request_id = ownership_request_response.id
    row: OwnershipRequest | None = database_session.query(OwnershipRequest).filter(
        OwnershipRequest.request_id == ownership_request_id).one_or_none()
    assert row is not None

    or_audit: OwnershipRequestsAudit | None = database_session.query(OwnershipRequestsAudit).filter(
        OwnershipRequestsAudit.request_id == ownership_request_id).one_or_none()
    assert or_audit is not None
    assert or_audit.session_id == 23276916

    requested_papers = database_session.query(
        t_arXiv_ownership_requests_papers.c.document_id
    ).filter(
        t_arXiv_ownership_requests_papers.c.request_id == ownership_request_id
    ).all()

    assert doc_ids == set([row[0] for row in requested_papers])

    response11 = admin_api_db_only_client.get(f"/v1/paper_owners?user_id=1", headers=api_headers)
    result11 = response11.json()
    assert len(result11) == 0

    # Now update the request jest created
    response2 = admin_api_db_only_client.get("/v1/ownership_requests/1", headers=api_headers)
    assert response2.status_code == 200

    or1 = OwnershipRequestModel.model_validate(response2.json())
    assert or1 is not None

    document_ids = [
        2650641, 2651312, 2654267, 2656141, 2657367,
        2657459, 2663552, 2663650, 2664481, 2664960,
        2665625, 2668328, 2669721, 2669912, 2670211,
        2671590, 2673580, 2674579, 2675896
    ]

    # Select half of the documents (rounded down if odd number)
    selected_documents = document_ids[:len(document_ids) // 2]

    or_submit = OwnershipRequestSubmit(
        user_id=1,
        workflow_status=WorkflowStatus.ACCEPTED,
        document_ids=document_ids,
        authored_documents=selected_documents,
        paper_ids=None
    )

    response3 = admin_api_db_only_client.put("/v1/ownership_requests/1", headers=api_headers,
                               json=or_submit.model_dump(mode="json"))
    assert response3.status_code == 200

    or3 = OwnershipRequestModel.model_validate(response3.json())
    assert or3

    response31 = admin_api_db_only_client.get(f"/v1/paper_owners?user_id=1", headers=api_headers)
    result31 = response31.json()
    assert len(result31) == 19

    expected_result = [
        {'added_by': 1129053, 'date': '2025-09-08T18:29:37', 'document': None, 'document_id': 2664960,
         'flag_author': False, 'flag_auto': False, 'id': 'user_1-doc_2664960', 'remote_addr': 'testclient',
         'remote_host': 'localhost', 'tracking_cookie': '', 'user_id': 1, 'valid': True},
        {'added_by': 1129053, 'date': '2025-09-08T18:29:37', 'document': None, 'document_id': 2675896,
         'flag_author': False, 'flag_auto': False, 'id': 'user_1-doc_2675896', 'remote_addr': 'testclient',
         'remote_host': 'localhost', 'tracking_cookie': '', 'user_id': 1, 'valid': True},
        {'added_by': 1129053, 'date': '2025-09-08T18:29:37', 'document': None, 'document_id': 2674579,
         'flag_author': False, 'flag_auto': False, 'id': 'user_1-doc_2674579', 'remote_addr': 'testclient',
         'remote_host': 'localhost', 'tracking_cookie': '', 'user_id': 1, 'valid': True},
        {'added_by': 1129053, 'date': '2025-09-08T18:29:37', 'document': None, 'document_id': 2673580,
         'flag_author': False, 'flag_auto': False, 'id': 'user_1-doc_2673580', 'remote_addr': 'testclient',
         'remote_host': 'localhost', 'tracking_cookie': '', 'user_id': 1, 'valid': True},
        {'added_by': 1129053, 'date': '2025-09-08T18:29:37', 'document': None, 'document_id': 2671590,
         'flag_author': False, 'flag_auto': False, 'id': 'user_1-doc_2671590', 'remote_addr': 'testclient',
         'remote_host': 'localhost', 'tracking_cookie': '', 'user_id': 1, 'valid': True},
        {'added_by': 1129053, 'date': '2025-09-08T18:29:37', 'document': None, 'document_id': 2670211,
         'flag_author': False, 'flag_auto': False, 'id': 'user_1-doc_2670211', 'remote_addr': 'testclient',
         'remote_host': 'localhost', 'tracking_cookie': '', 'user_id': 1, 'valid': True},
        {'added_by': 1129053, 'date': '2025-09-08T18:29:37', 'document': None, 'document_id': 2669912,
         'flag_author': False, 'flag_auto': False, 'id': 'user_1-doc_2669912', 'remote_addr': 'testclient',
         'remote_host': 'localhost', 'tracking_cookie': '', 'user_id': 1, 'valid': True},
        {'added_by': 1129053, 'date': '2025-09-08T18:29:37', 'document': None, 'document_id': 2669721,
         'flag_author': False, 'flag_auto': False, 'id': 'user_1-doc_2669721', 'remote_addr': 'testclient',
         'remote_host': 'localhost', 'tracking_cookie': '', 'user_id': 1, 'valid': True},
        {'added_by': 1129053, 'date': '2025-09-08T18:29:37', 'document': None, 'document_id': 2668328,
         'flag_author': False, 'flag_auto': False, 'id': 'user_1-doc_2668328', 'remote_addr': 'testclient',
         'remote_host': 'localhost', 'tracking_cookie': '', 'user_id': 1, 'valid': True},
        {'added_by': 1129053, 'date': '2025-09-08T18:29:37', 'document': None, 'document_id': 2665625,
         'flag_author': False, 'flag_auto': False, 'id': 'user_1-doc_2665625', 'remote_addr': 'testclient',
         'remote_host': 'localhost', 'tracking_cookie': '', 'user_id': 1, 'valid': True},
        {'added_by': 1129053, 'date': '2025-09-08T18:29:37', 'document': None, 'document_id': 2650641,
         'flag_author': True, 'flag_auto': False, 'id': 'user_1-doc_2650641', 'remote_addr': 'testclient',
         'remote_host': 'localhost', 'tracking_cookie': '', 'user_id': 1, 'valid': True},
        {'added_by': 1129053, 'date': '2025-09-08T18:29:37', 'document': None, 'document_id': 2664481,
         'flag_author': True, 'flag_auto': False, 'id': 'user_1-doc_2664481', 'remote_addr': 'testclient',
         'remote_host': 'localhost', 'tracking_cookie': '', 'user_id': 1, 'valid': True},
        {'added_by': 1129053, 'date': '2025-09-08T18:29:37', 'document': None, 'document_id': 2663650,
         'flag_author': True, 'flag_auto': False, 'id': 'user_1-doc_2663650', 'remote_addr': 'testclient',
         'remote_host': 'localhost', 'tracking_cookie': '', 'user_id': 1, 'valid': True},
        {'added_by': 1129053, 'date': '2025-09-08T18:29:37', 'document': None, 'document_id': 2663552,
         'flag_author': True, 'flag_auto': False, 'id': 'user_1-doc_2663552', 'remote_addr': 'testclient',
         'remote_host': 'localhost', 'tracking_cookie': '', 'user_id': 1, 'valid': True},
        {'added_by': 1129053, 'date': '2025-09-08T18:29:37', 'document': None, 'document_id': 2657459,
         'flag_author': True, 'flag_auto': False, 'id': 'user_1-doc_2657459', 'remote_addr': 'testclient',
         'remote_host': 'localhost', 'tracking_cookie': '', 'user_id': 1, 'valid': True},
        {'added_by': 1129053, 'date': '2025-09-08T18:29:37', 'document': None, 'document_id': 2657367,
         'flag_author': True, 'flag_auto': False, 'id': 'user_1-doc_2657367', 'remote_addr': 'testclient',
         'remote_host': 'localhost', 'tracking_cookie': '', 'user_id': 1, 'valid': True},
        {'added_by': 1129053, 'date': '2025-09-08T18:29:37', 'document': None, 'document_id': 2656141,
         'flag_author': True, 'flag_auto': False, 'id': 'user_1-doc_2656141', 'remote_addr': 'testclient',
         'remote_host': 'localhost', 'tracking_cookie': '', 'user_id': 1, 'valid': True},
        {'added_by': 1129053, 'date': '2025-09-08T18:29:37', 'document': None, 'document_id': 2654267,
         'flag_author': True, 'flag_auto': False, 'id': 'user_1-doc_2654267', 'remote_addr': 'testclient',
         'remote_host': 'localhost', 'tracking_cookie': '', 'user_id': 1, 'valid': True},
        {'added_by': 1129053, 'date': '2025-09-08T18:29:37', 'document': None, 'document_id': 2651312,
         'flag_author': True, 'flag_auto': False, 'id': 'user_1-doc_2651312', 'remote_addr': 'testclient',
         'remote_host': 'localhost', 'tracking_cookie': '', 'user_id': 1, 'valid': True}]

    # Remove date field from both lists as it changes on each test run
    for item in result31:
        item.pop('date', None)
    for item in expected_result:
        item.pop('date', None)

    # Sort both lists by document_id for stable comparison
    result31_sorted = sorted(result31, key=lambda x: x['document_id'])  # type: ignore[arg-type, return-value]
    expected_result_sorted = sorted(expected_result, key=lambda x: x['document_id'])  # type: ignore[arg-type, return-value]

    assert result31_sorted == expected_result_sorted
