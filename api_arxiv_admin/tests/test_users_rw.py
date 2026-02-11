import pytest
from arxiv.db.models import TapirAdminAudit, Demographic
from fastapi.testclient import TestClient


from arxiv_admin_api.user import UserCommentRequest, UserPropertyUpdateRequest, UserModel, UserVetoStatusRequest
from arxiv_bizlogic.user_status import UserVetoStatus

TEST_USER_ID = 591211
TEST_USER_SESSION_ID = 23276929


def test_get_user_by_id_with_no_auth(admin_api_sqlite_client: TestClient) -> None:
    body = UserCommentRequest(
        comment="fav!"
    )
    response = admin_api_sqlite_client.post("/v1/users/1/comment", json=body.model_dump())
    assert response.status_code == 401

def test_get_user_by_id(admin_api_sqlite_client: TestClient,
                        admin_api_admin_user_headers,
                        sqlite_session) -> None:
    with sqlite_session() as session:
        count_0 = session.query(TapirAdminAudit).count()

    body = UserCommentRequest(
        comment="fav!"
    )
    response = admin_api_sqlite_client.post("/v1/users/1/comment",
                                            json=body.model_dump(),
                                            headers=admin_api_admin_user_headers)
    assert response.status_code == 201
    with sqlite_session() as session:
        count_1 = session.query(TapirAdminAudit).count()
    assert count_0 + 1 == count_1

# user demographic update

def test_update_user_demographic_no_auth(admin_api_sqlite_client: TestClient) -> None:
    """Test that updating demographic without auth returns 401"""
    body = UserPropertyUpdateRequest(
        property_name="country",
        property_value="us"
    )
    response = admin_api_sqlite_client.put(f"/v1/users/{TEST_USER_ID}/demographic", json=body.model_dump())
    assert response.status_code == 401


def test_update_user_demographic(admin_api_sqlite_client: TestClient,
                                  admin_api_admin_user_headers,
                                  sqlite_session) -> None:
    """Test updating a user's demographic field"""
    with sqlite_session() as session:
        audit_count_before = session.query(TapirAdminAudit).count()

    body = UserPropertyUpdateRequest(
        property_name="country",
        property_value="jp",
        comment="Changed country for testing"
    )
    response = admin_api_sqlite_client.put(f"/v1/users/{TEST_USER_ID}/demographic",
                                            json=body.model_dump(),
                                            headers=admin_api_admin_user_headers)
    assert response.status_code == 200

    # Verify the update was NOT recorded in audit log
    with sqlite_session() as session:
        audit_count_after = session.query(TapirAdminAudit).count()
    assert audit_count_after == audit_count_before

    # Verify the update was NOT recorded in audit log
    response = admin_api_sqlite_client.get(f"/v1/users/{TEST_USER_ID}",
                                                headers=admin_api_admin_user_headers)
    user = UserModel.model_validate(response.json())
    assert user.country == "jp"

# veto

def test_update_veto_status_no_auth(admin_api_sqlite_client: TestClient) -> None:
    """Test that updating veto status without auth returns 401"""
    body = UserVetoStatusRequest(
        status_before=UserVetoStatus.OK,
        status_after=UserVetoStatus.NO_UPLOAD,
        comment="Testing veto status update"
    )
    response = admin_api_sqlite_client.put(f"/v1/users/{TEST_USER_ID}/veto-status", json=body.model_dump())
    assert response.status_code == 401


def test_update_veto_status(admin_api_sqlite_client: TestClient,
                            admin_api_admin_user_headers,
                            sqlite_session) -> None:
    """Test updating a user's veto status"""
    user_id = TEST_USER_ID

    with sqlite_session() as session:
        audit_count_before = session.query(TapirAdminAudit).count()
        demographic: Demographic | None = session.query(Demographic).filter(Demographic.user_id == user_id).one_or_none()
        if demographic is None:
            raise Exception("User not found")
        demographic.veto_status = "ok"
        session.commit()

    body = UserVetoStatusRequest(
        status_before=UserVetoStatus.OK,
        status_after=UserVetoStatus.NO_UPLOAD,
        comment="Testing veto status change"
    )
    response = admin_api_sqlite_client.put(f"/v1/users/{user_id}/veto-status",
                                           json=body.model_dump(),
                                           headers=admin_api_admin_user_headers)
    assert response.status_code == 200

    # Verify the update was recorded in audit log
    with sqlite_session() as session:
        audit_count_after = session.query(TapirAdminAudit).count()
    assert audit_count_after == audit_count_before + 1

    # Verify the veto status was updated
    response = admin_api_sqlite_client.get(f"/v1/users/{user_id}",
                                           headers=admin_api_admin_user_headers)
    user = UserModel.model_validate(response.json())
    assert user.veto_status == UserVetoStatus.NO_UPLOAD.value


def test_update_veto_status_no_change(admin_api_sqlite_client: TestClient,
                                      admin_api_admin_user_headers) -> None:
    """Test that updating veto status to the same value returns 208"""
    # First get the current status
    response = admin_api_sqlite_client.get(f"/v1/users/{TEST_USER_ID}",
                                           headers=admin_api_admin_user_headers)
    user = UserModel.model_validate(response.json())
    current_status = UserVetoStatus(user.veto_status)

    # Try to update to the same status
    body = UserVetoStatusRequest(
        status_before=current_status,
        status_after=current_status,
        comment="No change test"
    )
    response = admin_api_sqlite_client.put(f"/v1/users/{TEST_USER_ID}/veto-status",
                                           json=body.model_dump(),
                                           headers=admin_api_admin_user_headers)
    assert response.status_code == 208

