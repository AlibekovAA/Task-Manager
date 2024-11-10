from fastapi import status


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
