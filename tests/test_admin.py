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
        f"/users/{user_id}/role",
        headers=admin_headers,
        json={"role": "admin"}
    )
    assert response.status_code == status.HTTP_200_OK
