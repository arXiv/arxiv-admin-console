import pytest
from fastapi.testclient import TestClient

TEST_USER_ID = 591211
TEST_USER_SESSION_ID = 23276929

def test_get_user_by_id_with_no_auth(admin_api_sqlite_client: TestClient) -> None:
    response = admin_api_sqlite_client.get("/v1/users/1")
    assert response.status_code == 401


def test_get_user_by_id(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/users/1", headers=admin_api_admin_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["first_name"] == "Jacques"
    assert data["last_name"] == "Watt"

def test_get_user_not_found(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/users/9999999", headers=admin_api_admin_user_headers)
    assert response.status_code == 404

def test_get_user_with_query_user_id(admin_api_sqlite_client: TestClient,
                                     test_env_sqlite: dict,
                                     admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/users/?id=1", headers=admin_api_admin_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    person = data[0]
    assert person["email"] == "jjw1133@cornell.edu"


def test_get_user_with_query_email(admin_api_sqlite_client: TestClient,
                                   admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/users/?email=jjw1133@cornell.edu", headers=admin_api_admin_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    person = data[0]
    assert person["id"] == 1
    assert person["email"] == "jjw1133@cornell.edu"

def test_get_user_with_query_username(admin_api_sqlite_client: TestClient,
                                      admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/users/?username=cookie_monster", headers=admin_api_admin_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    person = data[0]
    assert person["id"] == 1129053


def test_get_user_with_no_query(admin_api_sqlite_client: TestClient,
                                admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/users/", headers=admin_api_admin_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 100


def test_get_user_with_too_many_queries(admin_api_sqlite_client: TestClient,
                                        admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/users/?id=1&email=sasha.the.dog@example.com", headers=admin_api_admin_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
