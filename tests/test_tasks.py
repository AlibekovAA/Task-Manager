import pytest
from fastapi import status


@pytest.fixture
def auth_headers(client):
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
    return {"Authorization": f"Bearer {token}"}


def test_create_task(client, auth_headers):
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
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test Description"


def test_get_tasks(client, auth_headers):
    client.post(
        "/tasks/",
        headers=auth_headers,
        json={
            "title": "Test Task",
            "description": "Test Description",
            "deadline": "2024-12-31T23:59:59"
        }
    )

    response = client.get("/tasks/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) > 0
    assert data[0]["title"] == "Test Task"


def test_update_task(client, auth_headers):
    create_response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={
            "title": "Test Task",
            "description": "Test Description",
            "deadline": "2024-12-31T23:59:59"
        }
    )
    task_id = create_response.json()["id"]

    response = client.put(
        f"/tasks/{task_id}",
        headers=auth_headers,
        json={
            "title": "Updated Task",
            "description": "Updated Description",
            "deadline": "2024-12-31T23:59:59"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Updated Task"
    assert data["description"] == "Updated Description"


def test_delete_task(client, auth_headers):
    create_response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={
            "title": "Test Task",
            "description": "Test Description",
            "deadline": "2024-12-31T23:59:59"
        }
    )
    task_id = create_response.json()["id"]

    response = client.delete(f"/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    response = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_assigned_tasks(client, auth_headers):
    client.post(
        "/tasks/",
        headers=auth_headers,
        json={
            "title": "Assigned Task",
            "description": "Test Description",
            "deadline": "2024-12-31T23:59:59"
        }
    )

    response = client.get("/assigned-tasks/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)


def test_get_task_by_id(client, auth_headers):
    create_response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={
            "title": "Test Task",
            "description": "Test Description",
            "deadline": "2024-12-31T23:59:59"
        }
    )
    task_id = create_response.json()["id"]

    response = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test Description"


def test_get_nonexistent_task(client, auth_headers):
    response = client.get("/tasks/999999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_task_invalid_data(client, auth_headers):
    create_response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={
            "title": "Test Task",
            "description": "Test Description",
            "deadline": "2024-12-31T23:59:59"
        }
    )
    task_id = create_response.json()["id"]

    response = client.put(
        f"/tasks/{task_id}",
        headers=auth_headers,
        json={
            "title": "",
            "description": "Updated Description",
            "deadline": "2024-12-31T23:59:59"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
