from fastapi import status

from backend import crud, schemas
from backend.rate_limiter import rate_limiter


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


def test_get_tasks_with_filters(client, auth_headers):
    rate_limiter.reset_all()

    tasks_data = [
        {"title": "High Priority", "priority": 1},
        {"title": "Medium Priority", "priority": 2},
        {"title": "Low Priority", "priority": 3}]

    for task in tasks_data:
        response = client.post(
            "/tasks/",
            headers=auth_headers,
            json={
                **task,
                "description": "Test",
                "deadline": "2024-12-31T23:59:59"
            }
        )
        assert response.status_code == status.HTTP_200_OK

    response = client.get("/tasks/?priority=1", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    filtered_tasks = response.json()
    assert len(filtered_tasks) == 1
    assert filtered_tasks[0]["title"] == "High Priority"


def test_update_task_status(client, auth_headers):
    rate_limiter.reset_all()

    create_response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={
            "title": "Test Task",
            "description": "Test Description",
            "deadline": "2024-12-31T23:59:59",
            "status": "pending"
        }
    )
    task_id = create_response.json()["id"]

    response = client.put(
        f"/tasks/{task_id}/status",
        headers=auth_headers,
        json={"status": "completed"}
    )
    assert response.status_code == status.HTTP_200_OK


def test_delete_completed_tasks(client, auth_headers):
    rate_limiter.reset_all()

    tasks = []
    for i in range(3):
        response = client.post(
            "/tasks/",
            headers=auth_headers,
            json={
                "title": f"Task {i}",
                "description": "Test Description",
                "deadline": "2024-12-31T23:59:59",
                "priority": 1
            }
        )
        assert response.status_code == status.HTTP_200_OK
        tasks.append(response.json()["id"])

    for task_id in tasks:
        response = client.put(
            f"/tasks/{task_id}/status",
            headers=auth_headers,
            json={"status": 2}
        )
        assert response.status_code == status.HTTP_200_OK

    response = client.delete("/tasks/completed", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    response = client.get("/tasks/", headers=auth_headers)
    assert len(response.json()) == 0


def test_task_validation(client, auth_headers):
    response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={
            "title": "Test Task",
            "description": "Test Description",
            "priority": 5,
            "deadline": "2024-12-31T23:59:59"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={
            "title": "Test Task",
            "description": "Test Description",
            "deadline": "2020-12-31T23:59:59"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


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

    assert "Creating new task" in caplog.text
    assert "Test Task" in caplog.text


def test_error_logging(client, auth_headers, caplog):
    response = client.get("/tasks/99999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND

    assert "Task not found" in caplog.text
    assert "99999" in caplog.text
