import pytest
from fastapi import status

from backend import crud
from backend.utils.rate_limiter import rate_limiter


@pytest.fixture
def auth_headers(client):
    rate_limiter.attempts = {}
    rate_limiter.blocked_until = {}
    _ = client.post("/users/", json={"email": "test@example.com", "password": "testpass123", "secret_word": "secret"})
    login_response = client.post("/token", data={"username": "test@example.com", "password": "testpass123"})
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def task_with_file(client, auth_headers):
    task_response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={"title": "Test Task", "description": "Test Description", "deadline": "2024-12-31T23:59:59"},
    )
    task_id = task_response.json()["id"]

    file_content = b"test file content"
    upload_response = client.post(
        f"/tasks/{task_id}/files/",
        headers=auth_headers,
        files={"file": ("test.txt", file_content, "text/plain")},
    )
    assert upload_response.status_code == status.HTTP_200_OK, f"File upload failed: {upload_response.json()}"
    file_id = upload_response.json()["id"]

    return {"task_id": task_id, "file_id": file_id}


def test_upload_file(client, auth_headers):
    task_response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={"title": "Test Task", "description": "Test Description", "deadline": "2024-12-31T23:59:59"},
    )
    task_id = task_response.json()["id"]

    file_content = b"test file content"
    response = client.post(
        f"/tasks/{task_id}/files/",
        headers=auth_headers,
        files={"file": ("test.txt", file_content, "text/plain")},
    )

    assert response.status_code == status.HTTP_200_OK
    assert "id" in response.json()
    assert response.json()["filename"] == "test.txt"


def test_upload_file_invalid_type(client, auth_headers):
    task_response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={"title": "Test Task", "description": "Test Description", "deadline": "2024-12-31T23:59:59"},
    )
    task_id = task_response.json()["id"]

    file_content = b"test file content"
    response = client.post(
        f"/tasks/{task_id}/files/",
        headers=auth_headers,
        files={"file": ("test.exe", file_content, "application/x-msdownload")},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


def test_upload_file_nonexistent_task(client, auth_headers):
    file_content = b"test file content"
    response = client.post(
        "/tasks/999999/files/",
        headers=auth_headers,
        files={"file": ("test.txt", file_content, "text/plain")},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_task_files(client, auth_headers, task_with_file):
    task_id = task_with_file["task_id"]
    response = client.get(f"/tasks/{task_id}/files/", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
    assert len(response.json()) > 0


def test_get_task_files_nonexistent_task(client, auth_headers):
    response = client.get("/tasks/999999/files/", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_download_file(client, auth_headers, task_with_file):
    task_id = task_with_file["task_id"]
    file_id = task_with_file["file_id"]

    response = client.get(f"/tasks/{task_id}/files/{file_id}", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.content == b"test file content"


def test_download_file_nonexistent_file(client, auth_headers, task_with_file):
    task_id = task_with_file["task_id"]
    response = client.get(f"/tasks/{task_id}/files/999999", headers=auth_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_download_file_nonexistent_task(client, auth_headers):
    response = client.get("/tasks/999999/files/1", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_file(client, auth_headers, task_with_file):
    task_id = task_with_file["task_id"]
    file_id = task_with_file["file_id"]

    response = client.delete(f"/tasks/{task_id}/files/{file_id}", headers=auth_headers)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == file_id


def test_delete_file_nonexistent_file(client, auth_headers, task_with_file):
    task_id = task_with_file["task_id"]
    response = client.delete(f"/tasks/{task_id}/files/999999", headers=auth_headers)

    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_file_nonexistent_task(client, auth_headers):
    response = client.delete("/tasks/999999/files/1", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_pm_can_access_assigned_task_file(client, auth_headers, db_session):
    rate_limiter.attempts = {}
    rate_limiter.blocked_until = {}
    pm_response = client.post(
        "/users/", json={"email": "pm@example.com", "password": "pmpass123", "secret_word": "secret"}
    )
    pm_id = pm_response.json()["id"]

    admin_info = client.get("/users/me/", headers=auth_headers).json()
    if admin_info["role"] != "admin":
        _ = client.post(
            "/users/",
            json={
                "email": "admin@test.com",
                "password": "adminpass123",
                "secret_word": "secret",
            },
        )
        admin_user = crud.get_user_by_email(db_session, "admin@test.com")
        admin_user.role = "admin"
        db_session.commit()

        admin_login = client.post("/token", data={"username": "admin@test.com", "password": "adminpass123"})
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    else:
        admin_headers = auth_headers

    client.put(f"/admin/users/{pm_id}/role", headers=admin_headers, json={"role": "pm"})

    pm_login = client.post("/token", data={"username": "pm@example.com", "password": "pmpass123"})
    pm_headers = {"Authorization": f"Bearer {pm_login.json()['access_token']}"}

    task_response = client.post(
        "/tasks/",
        headers=pm_headers,
        json={"title": "PM Task", "description": "Test Description", "deadline": "2024-12-31T23:59:59"},
    )
    task_id = task_response.json()["id"]

    file_content = b"pm file content"
    upload_response = client.post(
        f"/tasks/{task_id}/files/",
        headers=pm_headers,
        files={"file": ("pm_file.txt", file_content, "text/plain")},
    )
    assert upload_response.status_code == status.HTTP_200_OK
    file_id = upload_response.json()["id"]

    response = client.get(f"/tasks/{task_id}/files/{file_id}", headers=pm_headers)
    assert response.status_code == status.HTTP_200_OK
