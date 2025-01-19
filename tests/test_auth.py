from fastapi import status

from backend.rate_limiter import rate_limiter


def test_register_user(client):
    response = client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "secret_word": "secret"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "email" in data
    assert data["email"] == "test@example.com"


def test_register_duplicate_email(client):
    client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "secret_word": "secret"
        }
    )

    response = client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "password": "different123",
            "secret_word": "different"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_login_user(client):
    client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "secret_word": "secret"
        }
    )

    response = client.post(
        "/token",
        data={
            "username": "test@example.com",
            "password": "testpass123"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "secret_word": "secret"
        }
    )

    response = client.post(
        "/token",
        data={
            "username": "test@example.com",
            "password": "wrongpass"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_reset_password(client):
    client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "secret_word": "secret"
        }
    )

    response = client.post(
        "/users/reset-password",
        json={
            "email": "test@example.com",
            "secret_word": "secret",
            "new_password": "newpass123"
        }
    )
    assert response.status_code == status.HTTP_200_OK

    response = client.post(
        "/token",
        data={
            "username": "test@example.com",
            "password": "newpass123"
        }
    )
    assert response.status_code == status.HTTP_200_OK


def test_verify_token(client):
    client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "secret_word": "secret"
        }
    )

    response = client.post(
        "/token",
        data={
            "username": "test@example.com",
            "password": "testpass123"
        }
    )
    token = response.json()["access_token"]

    verify_response = client.get(
        "/token/verify",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert verify_response.status_code == status.HTTP_200_OK
    data = verify_response.json()
    assert data["valid"] is True
    assert data["user"] == "test@example.com"
    assert "role" in data


def test_verify_reset_credentials(client):
    client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "secret_word": "secret"
        }
    )

    response = client.post(
        "/users/verify-reset",
        json={
            "email": "test@example.com",
            "secret_word": "secret"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["message"] == "Данные подтверждены"


def test_verify_reset_credentials_wrong_secret(client):
    client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "secret_word": "secret"
        }
    )

    response = client.post(
        "/users/verify-reset",
        json={
            "email": "test@example.com",
            "secret_word": "wrong_secret"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_check_password(client):
    client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "secret_word": "secret"
        }
    )

    response = client.post(
        "/token",
        data={
            "username": "test@example.com",
            "password": "testpass123"
        }
    )
    token = response.json()["access_token"]

    check_response = client.post(
        "/users/me/check-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": "testpass123"}
    )
    assert check_response.status_code == status.HTTP_200_OK
    assert check_response.json()["message"] == "Пароль верный"


def test_check_password_invalid(client):
    client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "secret_word": "secret"
        }
    )

    response = client.post(
        "/token",
        data={
            "username": "test@example.com",
            "password": "testpass123"
        }
    )
    token = response.json()["access_token"]

    check_response = client.post(
        "/users/me/check-password",
        headers={"Authorization": f"Bearer {token}"},
        json={"password": "wrongpass"}
    )
    assert check_response.status_code == status.HTTP_401_UNAUTHORIZED


def test_check_password_missing(client):
    client.post(
        "/users/",
        json={
            "email": "test@example.com",
            "password": "testpass123",
            "secret_word": "secret"
        }
    )

    response = client.post(
        "/token",
        data={
            "username": "test@example.com",
            "password": "testpass123"
        }
    )
    token = response.json()["access_token"]

    check_response = client.post(
        "/users/me/check-password",
        headers={"Authorization": f"Bearer {token}"},
        json={}
    )
    assert check_response.status_code == status.HTTP_400_BAD_REQUEST


def test_reset_password_nonexistent_user(client):
    response = client.post(
        "/users/reset-password",
        json={
            "email": "nonexistent@example.com",
            "secret_word": "secret",
            "new_password": "newpass123"
        }
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_password_reset_flow(client):
    client.post(
        "/users/",
        json={
            "email": "reset@example.com",
            "password": "oldpass123",
            "secret_word": "secret"
        }
    )

    reset_response = client.post(
        "/users/reset-password",
        json={
            "email": "reset@example.com",
            "secret_word": "secret",
            "new_password": "newpass123"
        }
    )
    assert reset_response.status_code == status.HTTP_200_OK

    login_response = client.post(
        "/token",
        data={
            "username": "reset@example.com",
            "password": "newpass123"
        }
    )
    assert login_response.status_code == status.HTTP_200_OK


def test_rate_limiter(client):
    rate_limiter.reset("test@example.com")

    for _ in range(6):
        response = client.post(
            "/token",
            data={
                "username": "test@example.com",
                "password": "wrongpass"
            }
        )

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert "Слишком много попыток" in response.json()["detail"]
