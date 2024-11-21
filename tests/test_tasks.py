import tempfile
import os
import asyncio
import aiohttp

import pytest
from fastapi import status


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
    assert create_response.status_code == status.HTTP_200_OK
    task_id = create_response.json()["id"]

    response = client.put(
        f"/tasks/{task_id}",
        headers=auth_headers,
        json={
            "title": "Valid Title",
            "description": "Updated Description",
            "deadline": "invalid_date"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_task_priority_update(client, auth_headers):
    create_response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={
            "title": "Priority Test",
            "description": "Test Description",
            "priority": 3,
            "deadline": "2024-12-31T23:59:59"
        }
    )
    task_id = create_response.json()["id"]

    response = client.put(
        f"/tasks/{task_id}",
        headers=auth_headers,
        json={
            "title": "Priority Test",
            "description": "Test Description",
            "priority": 1,
            "deadline": "2024-12-31T23:59:59"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["priority"] == 1


def test_task_status_transitions(client, auth_headers):
    create_response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={
            "title": "Status Test",
            "description": "Test Description",
            "deadline": "2024-12-31T23:59:59"
        }
    )
    assert create_response.status_code == status.HTTP_200_OK
    task_id = create_response.json()["id"]

    statuses = ["pending", "in_progress", "completed"]

    for status_value in statuses:
        response = client.put(
            f"/tasks/{task_id}",
            headers=auth_headers,
            json={
                "title": "Status Test",
                "description": "Test Description",
                "status": status_value,
                "deadline": "2024-12-31T23:59:59"
            }
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == status_value


def test_task_file_operations(client, auth_headers):
    create_response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={
            "title": "File Test",
            "description": "Test Description",
            "deadline": "2024-12-31T23:59:59"
        }
    )
    assert create_response.status_code == status.HTTP_200_OK
    task_id = create_response.json()["id"]

    with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp:
        tmp.write(b"test content")
        tmp_path = tmp.name

    try:
        with open(tmp_path, 'rb') as f:
            response = client.post(
                f"/tasks/{task_id}/attachments",
                headers=auth_headers,
                files={"file": ("test.txt", f, "text/plain")}
            )
            assert response.status_code == status.HTTP_200_OK

        response = client.get(
            f"/tasks/{task_id}/attachments",
            headers=auth_headers
        )
        assert response.status_code == status.HTTP_200_OK
        files = response.json()
        assert len(files) > 0

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_task_filters(client, auth_headers):
    tasks_data = [
        {
            "title": "High Priority",
            "description": "Test",
            "priority": "high",
            "status": "pending",
            "deadline": "2024-12-31T23:59:59"
        },
        {
            "title": "Medium Priority",
            "description": "Test",
            "priority": "medium",
            "status": "in_progress",
            "deadline": "2024-12-31T23:59:59"
        },
        {
            "title": "Low Priority",
            "description": "Test",
            "priority": "low",
            "status": "completed",
            "deadline": "2024-12-31T23:59:59"
        }
    ]

    for task in tasks_data:
        response = client.post("/tasks/", headers=auth_headers, json=task)
        assert response.status_code == status.HTTP_200_OK

    test_filters = [
        ("priority", "high"),
        ("status", "pending"),
        ("title", "High")
    ]

    for param, value in test_filters:
        response = client.get(f"/tasks/?{param}={value}", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK
        tasks = response.json()
        assert len(tasks) > 0
        if param != "title":
            assert all(task[param] == value for task in tasks)
        else:
            assert all(value in task[param] for task in tasks)


def test_invalid_file_upload(client, auth_headers):
    create_response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={
            "title": "File Test",
            "description": "Test Description",
            "deadline": "2024-12-31T23:59:59"
        }
    )
    task_id = create_response.json()["id"]

    large_data = b"x" * (10 * 1024 * 1024 + 1)
    response = client.post(
        f"/tasks/{task_id}/attachments",
        headers=auth_headers,
        files={"file": ("large.txt", large_data, "text/plain")}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = client.post(
        f"/tasks/{task_id}/attachments",
        headers=auth_headers,
        files={"file": ("test.exe", b"test", "application/x-msdownload")}
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
async def test_concurrent_task_creation(client, auth_headers):
    async def create_task(session, num):
        async with session.post(
            "http://testserver/tasks/",
            headers=auth_headers,
            json={
                "title": f"Concurrent Task {num}",
                "description": "Test Description",
                "deadline": "2024-12-31T23:59:59"
            }
        ) as response:
            return await response.json()

    async with aiohttp.ClientSession() as session:
        tasks = [create_task(session, i) for i in range(5)]
        results = await asyncio.gather(*tasks)

    assert len(results) == 5
    assert all(result["title"].startswith("Concurrent Task") for result in results)


def test_task_state_consistency(client, auth_headers):
    response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={
            "title": "State Test",
            "description": "Test Description",
            "deadline": "2024-12-31T23:59:59",
            "status": "pending"
        }
    )
    task_id = response.json()["id"]

    valid_transitions = [
        ("pending", "in_progress"),
        ("in_progress", "completed"),
        ("completed", "archived")
    ]

    for _, new_status in valid_transitions:
        response = client.put(
            f"/tasks/{task_id}/status",
            headers=auth_headers,
            json={"status": new_status}
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == new_status
