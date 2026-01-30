import pytest
from fastapi.testclient import TestClient
from arxiv_bizlogic.fastapi_helpers import COOKIE_ENV_NAMES

def test_ping(admin_api_db_only_client: TestClient):
    response = admin_api_db_only_client.get("/system/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_database_status(admin_api_db_only_client: TestClient):
    response = admin_api_db_only_client.get("/system/database_status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_cookie_names(admin_api_db_only_client: TestClient, test_env: dict):
    response = admin_api_db_only_client.get("/system/cookie_names")
    assert response.status_code == 200
    expected_cookies = {
        "session": test_env.get("AUTH_SESSION_COOKIE_NAME", "ARXIVNG_SESSION_ID"),
        "classic": test_env.get("CLASSIC_COOKIE_NAME", "tapir_session"),
        "keycloak_access": "keycloak_access_token",
        "keycloak_refresh": "keycloak_refresh_token",
        "ng": "ARXIVNG_SESSION_ID"
    }
    assert response.json() == expected_cookies
