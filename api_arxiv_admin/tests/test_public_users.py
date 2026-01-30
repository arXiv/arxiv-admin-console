import pytest
from fastapi.testclient import TestClient

from tests.conftest import generate_request_headers

TEST_USER_ID = 591211
TEST_USER_SESSION_ID = 23276929

@pytest.fixture
def api_headers(test_env) -> dict:
    return generate_request_headers(
        test_env,
        user_id=TEST_USER_ID,
        tapir_session_id=TEST_USER_SESSION_ID
    )


def test_get_public_user_by_id(admin_api_db_only_client: TestClient):
    response = admin_api_db_only_client.get("/v1/public-users/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["first_name"] == "Jacques"
    assert data["last_name"] == "Houle"

def test_get_public_user_not_found(admin_api_db_only_client: TestClient):
    response = admin_api_db_only_client.get("/v1/public-users/9999999")
    assert response.status_code == 404

def test_get_public_user_with_query_user_id(admin_api_db_only_client: TestClient, test_env, api_headers):
    response = admin_api_db_only_client.get("/v1/public-users/?user_id=1", headers=api_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1

def test_get_public_user_with_query_email(admin_api_db_only_client: TestClient, api_headers):
    response = admin_api_db_only_client.get("/v1/public-users/?email=jhoule@example.com", headers=api_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["email"] == "jhoule@example.com"

def test_get_public_user_with_query_username(admin_api_db_only_client: TestClient, api_headers: dict):
    response = admin_api_db_only_client.get("/v1/public-users/?username=cookie_monster", headers=api_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1129053

def test_get_public_user_with_no_query(admin_api_db_only_client: TestClient, api_headers: dict):
    response = admin_api_db_only_client.get("/v1/public-users/", headers=api_headers)
    assert response.status_code == 400

def test_get_public_user_with_too_many_queries(admin_api_db_only_client: TestClient, api_headers: dict):
    response = admin_api_db_only_client.get("/v1/public-users/?user_id=1&email=sasha.the.dog@example.com", headers=api_headers)
    assert response.status_code == 400