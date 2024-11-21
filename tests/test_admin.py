import pytest
from fastapi import status

from backend.config import ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_SECRET_WORD
from backend.rate_limiter import rate_limiter


@pytest.fixture
def admin_headers(client):
    rate_limiter.attempts = {}
    rate_limiter.blocked_until = {}
    response = client.post(
        "/users/",
        json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "secret_word": ADMIN_SECRET_WORD,
            "is_admin": True
        }
    )
    assert response.status_code == 200, f"Admin creation failed: {response.json()}"

    login_response = client.post(
        "/token",
        data={
            "username": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
    )
    assert login_response.status_code == 200, f"Admin login failed: {login_response.json()}"

    token = login_response.json()["access_token"]
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
    client.post(
        "/users/",
        json={
            "email": "admin@test.com",
            "password": "adminpass123",
            "secret_word": "secret",
            "is_admin": True,
            "role": "admin"
        }
    )
    admin_token = client.post(
        "/token",
        data={
            "username": "admin@test.com",
            "password": "adminpass123"
        }
    ).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

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
    admin_response = client.post(
        "/users/",
        json={
            "email": "admin2@test.com",
            "password": "adminpass123",
            "secret_word": "secret",
            "is_admin": True
        }
    )
    admin_id = admin_response.json()["id"]

    response = client.put(
        f"/users/{admin_id}/role",
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


def test_admin_user_management(client, admin_headers):
    user_response = client.post(
        "/users/",
        json={
            "email": "managed@example.com",
            "password": "pass123",
            "secret_word": "secret"
        }
    )
    user_id = user_response.json()["id"]

    roles = ["user", "pm", "admin"]
    for role in roles:
        response = client.put(
            f"/users/{user_id}/role",
            headers=admin_headers,
            json={"role": role}
        )
        assert response.status_code == status.HTTP_200_OK

        user_info = client.get(f"/users/{user_id}", headers=admin_headers)
        assert user_info.json()["role"] == role


def test_pm_role_task_management(client, admin_headers):
    pm_response = client.post(
        "/users/",
        json={
            "email": "pm@example.com",
            "password": "pmpass123",
            "secret_word": "secret"
        }
    )
    pm_id = pm_response.json()["id"]

    client.put(
        f"/users/{pm_id}/role",
        headers=admin_headers,
        json={"role": "pm"}
    )

    pm_token = client.post(
        "/token",
        data={
            "username": "pm@example.com",
            "password": "pmpass123"
        }
    ).json()["access_token"]
    pm_headers = {"Authorization": f"Bearer {pm_token}"}

    response = client.post(
        "/tasks/",
        headers=pm_headers,
        json={
            "title": "PM Task",
            "description": "Test Description",
            "deadline": "2024-12-31T23:59:59"
        }
    )
    assert response.status_code == status.HTTP_200_OK


def test_role_hierarchy(client, admin_headers):
    roles = ["user", "pm", "admin"]
    users = {}

    for role in roles:
        rate_limiter.attempts = {}
        rate_limiter.blocked_until = {}
        email = f"{role}@example.com"
        rate_limiter.reset()

        response = client.post(
            "/users/",
            json={
                "email": email,
                "password": "testpass123",
                "secret_word": "secret"
            }
        )
        user_id = response.json()["id"]

        if role != "user":
            client.put(
                f"/users/{user_id}/role",
                headers=admin_headers,
                json={"role": role}
            )

        token_response = client.post(
            "/token",
            data={
                "username": email,
                "password": "testpass123"
            }
        )
        token = token_response.json()["access_token"]
        users[role] = {"Authorization": f"Bearer {token}"}

    for role, headers in users.items():
        response = client.get("/users", headers=headers)
        if role == "admin":
            assert response.status_code == status.HTTP_200_OK
        else:
            assert response.status_code == status.HTTP_403_FORBIDDEN
