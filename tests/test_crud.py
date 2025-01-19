from fastapi import status

from backend import crud, schemas


def test_create_user_with_role(client, db_session):
    user = crud.create_user(
        db_session,
        schemas.UserCreate(
            email="test@example.com",
            password="testpass123",
            secret_word="secret"
        )
    )
    user.role = "admin"
    db_session.commit()
    assert user.role == "admin"
    assert user.email == "test@example.com"


def test_email_validation(client):
    response = client.post(
        "/users/",
        json={
            "email": "invalid_email",
            "password": "testpass123",
            "secret_word": "secret"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_logging_user_actions(client, auth_headers, caplog):
    response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={
            "title": "Test Task",
            "description": "Test Description",
            "deadline": "2024-12-31T23:59:59"
        }
    )
    assert response.status_code == status.HTTP_200_OK

    assert "Successfully retrieve user by email" in caplog.text
    assert "Test Task" in caplog.text


def test_error_logging(client, auth_headers, caplog):
    response = client.get("/tasks/99999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    assert "Task not found" in caplog.text
    assert "99999" in caplog.text
