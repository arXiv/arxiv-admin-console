from arxiv_admin_api.endorsement_requests import EndorsementRequestModel

from arxiv.db.models import EndorsementRequest, \
    TapirUser  # Category, EndorsementDomain, QuestionableCategory, Endorsement,

from arxiv_admin_api.biz.endorsement_biz import EndorsementBusiness
from arxiv_admin_api.biz.endorsement_io import EndorsementDBAccessor
from arxiv_admin_api.endorsements import EndorsementCodeModel


def test_email_patterns(reset_test_database, database_session, admin_api_db_only_client, admin_api_admin_user_headers) -> None:
    all_black_url = "/v1/email_patterns?purpose=black&_start=0&_end=99999"
    response_0 = admin_api_db_only_client.get(all_black_url, headers=admin_api_admin_user_headers)
    assert response_0.status_code == 200
    all_blacks = response_0.json()
    all_blacks_count_0 = len(all_blacks)
    assert all_blacks_count_0 > 0

    new_black = {
        "id": "%.example.com",
        "purpose": "black",
    }
    response_1 = admin_api_db_only_client.post("/v1/email_patterns", json=new_black, headers=admin_api_admin_user_headers)
    assert response_1.status_code == 201

    response_2 = admin_api_db_only_client.get(all_black_url, headers=admin_api_admin_user_headers)
    assert response_2.status_code == 200
    all_blacks = response_2.json()
    all_blacks_count_2 = len(all_blacks)
    assert all_blacks_count_2 == all_blacks_count_0 + 1

    # delete the 2nd element in all_blacks, and see the count reduces by 1
    response_3 = admin_api_db_only_client.delete(
        "/v1/email_patterns/black",
        params={"ids": [all_blacks[1]["id"]]},
        headers=admin_api_admin_user_headers
    )
    assert response_3.status_code == 204

    response_4 = admin_api_db_only_client.get(all_black_url, headers=admin_api_admin_user_headers)
    assert response_4.status_code == 200
    all_blacks_count_4 = len(response_4.json())
    assert all_blacks_count_4 == all_blacks_count_2 - 1

    # slice to first 25 elements, use /import with replace, verify count is 25
    all_blacks = response_4.json()
    first_25 = all_blacks[:25]
    patterns_text = "\n".join([p["id"] for p in first_25])

    from io import BytesIO
    file_content = BytesIO(patterns_text.encode("utf-8"))
    # Remove Content-Type header for multipart form data
    plain_headers = {k: v for k, v in admin_api_admin_user_headers.items() if k != "Content-Type"}
    response_5 = admin_api_db_only_client.post(
        "/v1/email_patterns/import",
        files={"file": ("patterns.txt", file_content, "text/plain")},
        data={"purpose": "black", "operation": "replace"},
        headers=plain_headers
    )
    assert response_5.status_code == 200
    result = response_5.json()
    assert result["processed_count"] == 25

    response_6 = admin_api_db_only_client.get(all_black_url, headers=admin_api_admin_user_headers)
    assert response_6.status_code == 200
    all_blacks_count_6 = len(response_6.json())
    assert all_blacks_count_6 == 25

    # test export/black - should return 25 patterns as text
    response_7 = admin_api_db_only_client.get(
        "/v1/email_patterns/export/black",
        headers=admin_api_admin_user_headers
    )
    assert response_7.status_code == 200
    exported_lines = [line for line in response_7.text.strip().split("\n") if line]
    assert len(exported_lines) == 25

