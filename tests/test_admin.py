import pytest
from fastapi import status

from backend.config import ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_SECRET_WORD


@pytest.fixture
def admin_headers(client):
    client.post(
        "/users/",
        json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "secret_word": ADMIN_SECRET_WORD
        }
    )

    response = client.post(
        "/token",
        data={
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_get_all_users(client, admin_headers):
    response = client.get("/users", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)


def test_get_user_by_id(client, admin_headers):
    user_response = client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "secret_word": "secret"
        }
    )
    user_id = user_response.json()["id"]

    response = client.get(f"/users/{user_id}", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "test@example.com"


def test_update_user_role(client, admin_headers):
    user_response = client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "secret_word": "secret"
        }
    )
    user_id = user_response.json()["id"]

    response = client.put(
        f"/admin/users/{user_id}/role",
        headers=admin_headers,
        json={"role": "admin"}
    )
    assert response.status_code == status.HTTP_200_OK


def test_get_nonexistent_user(client, admin_headers):
    response = client.get("/users/999999", headers=admin_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_nonexistent_user_role(client, admin_headers):
    response = client.put(
        "/users/999999/role",
        headers=admin_headers,
        json={"role": "admin"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_admin_role(client, admin_headers):
    me_response = client.get("/admin/users/me", headers=admin_headers)
    assert me_response.status_code == status.HTTP_200_OK
    admin_data = me_response.json()

    response = client.put(
        f"/admin/users/{admin_data['id']}/role",
        headers=admin_headers,
        json={"role": "user"}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_unauthorized_role_update(client):
    user_response = client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "secret_word": "secret"
        }
    )
    user_id = user_response.json()["id"]

    response = client.put(
        f"/admin/users/{user_id}/role",
        headers={},
        json={"role": "admin"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
