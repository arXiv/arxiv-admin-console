import pytest
from arxiv.db.models import TapirAdminAudit, Category
from sqlalchemy.sql import and_
from fastapi.testclient import TestClient

from arxiv_admin_api.categories import CategoryModel


# --- No-auth tests (expect 401) ---

def test_list_categories_no_auth(admin_api_sqlite_client: TestClient) -> None:
    response = admin_api_sqlite_client.get("/v1/categories/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "X-Total-Count" in response.headers
    item = data[0]
    assert "id" in item
    assert "archive" in item
    assert "subject_class" in item


def test_get_category_by_id_no_auth(admin_api_sqlite_client: TestClient) -> None:
    response = admin_api_sqlite_client.get("/v1/categories/cs.AI")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "cs.AI"
    assert data["archive"] == "cs"
    assert data["subject_class"] == "AI"
    assert data["category_name"] == "Artificial Intelligence"


def test_get_subject_classes_no_auth(admin_api_sqlite_client: TestClient) -> None:
    response = admin_api_sqlite_client.get("/v1/categories/cs/subject-class")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "X-Total-Count" in response.headers
    for cat in data:
        assert cat["archive"] == "cs"


def test_get_category_with_subject_class_no_auth(admin_api_sqlite_client: TestClient) -> None:
    response = admin_api_sqlite_client.get("/v1/categories/cs/subject-class/AI")
    assert response.status_code == 200
    data = response.json()
    assert data["archive"] == "cs"
    assert data["subject_class"] == "AI"
    assert data["category_name"] == "Artificial Intelligence"


def test_create_category_no_auth(admin_api_sqlite_client: TestClient) -> None:
    response = admin_api_sqlite_client.post("/v1/categories/", json={
        "archive": "test-arch",
        "subject_class": "XX",
    })
    assert response.status_code == 401


def test_update_category_no_auth(admin_api_sqlite_client: TestClient) -> None:
    response = admin_api_sqlite_client.put("/v1/categories/cs.AI", json={
        "category_name": "New Name"
    })
    assert response.status_code == 401


def test_delete_category_no_auth(admin_api_sqlite_client: TestClient) -> None:
    response = admin_api_sqlite_client.delete("/v1/categories/cs.AI")
    assert response.status_code == 401


def test_list_archive_groups_no_auth(admin_api_sqlite_client: TestClient) -> None:
    response = admin_api_sqlite_client.get("/v1/archive_group/")
    assert response.status_code == 200


# --- List categories ---

def test_list_categories(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/categories/", headers=admin_api_admin_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    # Verify X-Total-Count header
    assert "X-Total-Count" in response.headers
    total = int(response.headers["X-Total-Count"])
    assert total > 0
    # Verify structure
    item = data[0]
    assert "id" in item
    assert "archive" in item
    assert "subject_class" in item
    assert "definitive" in item
    assert "active" in item
    assert "category_name" in item
    assert "endorse_all" in item
    assert "endorse_email" in item
    assert "papers_to_endorse" in item
    assert "endorsement_domain" in item


def test_list_categories_pagination(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/categories/?_start=0&_end=5", headers=admin_api_admin_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    total = int(response.headers["X-Total-Count"])
    assert total > 5  # total should be more than our page size


def test_list_categories_pagination_offset(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    """Verify that different pages return different results."""
    resp1 = admin_api_sqlite_client.get("/v1/categories/?_start=0&_end=3", headers=admin_api_admin_user_headers)
    resp2 = admin_api_sqlite_client.get("/v1/categories/?_start=3&_end=6", headers=admin_api_admin_user_headers)
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    ids1 = [c["id"] for c in resp1.json()]
    ids2 = [c["id"] for c in resp2.json()]
    assert set(ids1).isdisjoint(set(ids2))


def test_list_categories_invalid_range(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/categories/?_start=10&_end=5", headers=admin_api_admin_user_headers)
    assert response.status_code == 400


def test_list_categories_filter_archive(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/categories/?archive=cs", headers=admin_api_admin_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for cat in data:
        assert cat["archive"].startswith("cs")


def test_list_categories_filter_active(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/categories/?active=true", headers=admin_api_admin_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for cat in data:
        assert cat["active"] is True


def test_list_categories_filter_inactive(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/categories/?active=false", headers=admin_api_admin_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for cat in data:
        assert cat["active"] is False


def test_list_categories_order_desc(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    resp_asc = admin_api_sqlite_client.get("/v1/categories/?_start=0&_end=5&_order=ASC", headers=admin_api_admin_user_headers)
    resp_desc = admin_api_sqlite_client.get("/v1/categories/?_start=0&_end=5&_order=DESC", headers=admin_api_admin_user_headers)
    assert resp_asc.status_code == 200
    assert resp_desc.status_code == 200
    ids_asc = [c["id"] for c in resp_asc.json()]
    ids_desc = [c["id"] for c in resp_desc.json()]
    assert ids_asc != ids_desc


# --- Get category by id ---

def test_get_category_by_id(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/categories/cs.AI", headers=admin_api_admin_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "cs.AI"
    assert data["archive"] == "cs"
    assert data["subject_class"] == "AI"
    assert data["category_name"] == "Artificial Intelligence"
    assert data["active"] is True
    assert data["definitive"] is True


def test_get_category_by_id_not_found(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/categories/zz.ZZ", headers=admin_api_admin_user_headers)
    assert response.status_code == 404


# --- Subject class endpoints ---

def test_list_subject_classes(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/categories/cs/subject-class", headers=admin_api_admin_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "X-Total-Count" in response.headers
    # All should belong to cs archive
    for cat in data:
        assert cat["archive"] == "cs"


def test_list_subject_classes_pagination(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/categories/cs/subject-class?_start=0&_end=3", headers=admin_api_admin_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3


def test_list_subject_classes_invalid_range(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/categories/cs/subject-class?_start=5&_end=2", headers=admin_api_admin_user_headers)
    assert response.status_code == 400


def test_list_subject_classes_order_desc(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    resp_asc = admin_api_sqlite_client.get("/v1/categories/cs/subject-class?_start=0&_end=5&_order=ASC", headers=admin_api_admin_user_headers)
    resp_desc = admin_api_sqlite_client.get("/v1/categories/cs/subject-class?_start=0&_end=5&_order=DESC", headers=admin_api_admin_user_headers)
    assert resp_asc.status_code == 200
    assert resp_desc.status_code == 200
    sc_asc = [c["subject_class"] for c in resp_asc.json()]
    sc_desc = [c["subject_class"] for c in resp_desc.json()]
    assert sc_asc != sc_desc


def test_get_category_with_subject_class(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/categories/cs/subject-class/AI", headers=admin_api_admin_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["archive"] == "cs"
    assert data["subject_class"] == "AI"
    assert data["category_name"] == "Artificial Intelligence"


def test_get_category_with_star_subject_class(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    """The * subject_class is treated as empty string (archive-only category)."""
    response = admin_api_sqlite_client.get("/v1/categories/astro-ph/subject-class/*", headers=admin_api_admin_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["archive"] == "astro-ph"
    assert data["subject_class"] == ""


def test_get_category_with_subject_class_not_found(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/categories/cs/subject-class/ZZ", headers=admin_api_admin_user_headers)
    assert response.status_code == 404


# --- Write operations (require owner role) ---

def test_update_category_not_owner(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    """Admin user without owner role gets 403."""
    response = admin_api_sqlite_client.put("/v1/categories/cs.AI", headers=admin_api_admin_user_headers, json={
        "category_name": "New Name"
    })
    assert response.status_code == 403


def test_create_category_not_owner(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    """Admin user without owner role gets 403."""
    response = admin_api_sqlite_client.post("/v1/categories/", headers=admin_api_admin_user_headers, json={
        "archive": "test-arch",
        "subject_class": "XC",
        "definitive": True,
        "active": True,
        "category_name": "Extraterrestrial Computing",
        "endorse_all": "d",
        "endorse_email": "d",
        "papers_to_endorse": 0,
        "endorsement_domain": "test-arch",
    })
    assert response.status_code == 403


def test_create_category_owner(admin_api_sqlite_client: TestClient, admin_api_owner_headers: dict) -> None:
    """Owner role can create a new category."""
    response = admin_api_sqlite_client.post("/v1/categories/", headers=admin_api_owner_headers, json={
        "archive": "cs",
        "subject_class": "XC",
        "definitive": True,
        "active": True,
        "category_name": "Extraterrestrial Computing",
        "endorse_all": "y",
        "endorse_email": "y",
        "papers_to_endorse": 0,
        "endorsement_domain": "cs",
    })
    assert response.status_code == 201


def test_delete_category_not_owner(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    """Admin user without owner role gets 403."""
    response = admin_api_sqlite_client.delete("/v1/categories/cs.AI", headers=admin_api_admin_user_headers)
    assert response.status_code == 403


# --- Archive group endpoint ---

def test_list_archive_groups(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/archive_group/", headers=admin_api_admin_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "X-Total-Count" in response.headers
    # Verify structure
    item = data[0]
    assert "archive" in item
    assert "group" in item


def test_list_archive_groups_pagination(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/archive_group/?_start=0&_end=5", headers=admin_api_admin_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5


def test_list_archive_groups_filter_archive(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/archive_group/?archive=cs", headers=admin_api_admin_user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    for item in data:
        assert item["archive"] == "cs"


def test_list_archive_groups_order_desc(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    resp_asc = admin_api_sqlite_client.get("/v1/archive_group/?_start=0&_end=5&_order=ASC", headers=admin_api_admin_user_headers)
    resp_desc = admin_api_sqlite_client.get("/v1/archive_group/?_start=0&_end=5&_order=DESC", headers=admin_api_admin_user_headers)
    assert resp_asc.status_code == 200
    assert resp_desc.status_code == 200
    archives_asc = [g["archive"] for g in resp_asc.json()]
    archives_desc = [g["archive"] for g in resp_desc.json()]
    assert archives_asc != archives_desc


def test_list_archive_groups_invalid_range(admin_api_sqlite_client: TestClient, admin_api_admin_user_headers: dict) -> None:
    response = admin_api_sqlite_client.get("/v1/archive_group/?_start=10&_end=2", headers=admin_api_admin_user_headers)
    assert response.status_code == 400

def test_update_delete_category_owner(admin_api_sqlite_client: TestClient,
                                      admin_api_owner_headers: dict,
                                      sqlite_session
                                      ) -> None:
    """Owner can create/update/delete a category.
    See the audit log created for each step
    """
    with sqlite_session() as session:
        audit_count_0 = session.query(TapirAdminAudit.entry_id).count()
        last_audit_entry = session.query(TapirAdminAudit.entry_id).order_by(TapirAdminAudit.entry_id.desc()).first()[0]
        cs_xc_p = session.query(Category).filter(and_(Category.archive == "cs", Category.subject_class == "XC")).count() == 1

    if not cs_xc_p:
        response = admin_api_sqlite_client.post("/v1/categories/", headers=admin_api_owner_headers, json={
            "archive": "cs",
            "subject_class": "XC",
            "definitive": True,
            "active": True,
            "category_name": "Extraterrestrial Computing",
            "endorse_all": "y",
            "endorse_email": "y",
            "papers_to_endorse": 0,
            "endorsement_domain": "cs",
        })
        assert response.status_code == 201

    with sqlite_session() as session:
        audit_count_1 = session.query(TapirAdminAudit.entry_id).count()
        assert audit_count_1 == audit_count_0 + 1

        audit = session.query(TapirAdminAudit).filter(TapirAdminAudit.entry_id == last_audit_entry + 1).one()
        assert audit.action == "arxiv-category"
        assert "create" in audit.data

    # Update papers_to_endorse to 3
    response = admin_api_sqlite_client.put("/v1/categories/cs.XC", headers=admin_api_owner_headers, json={
        "papers_to_endorse": 3,
    })
    assert response.status_code == 200
    data = response.json()
    assert data["papers_to_endorse"] == 3
    assert data["category_name"] == "Extraterrestrial Computing"

    with sqlite_session() as session:
        audit = session.query(TapirAdminAudit).filter(TapirAdminAudit.entry_id == last_audit_entry + 2).one()
        assert audit.action == "arxiv-category"
        assert "update" in audit.data

    # Delete the category
    response = admin_api_sqlite_client.delete("/v1/categories/cs.XC", headers=admin_api_owner_headers)
    assert response.status_code == 204

    with sqlite_session() as session:
        audit = session.query(TapirAdminAudit).filter(TapirAdminAudit.entry_id == last_audit_entry + 3).one()
        assert audit.action == "arxiv-category"
        assert "delete" in audit.data
