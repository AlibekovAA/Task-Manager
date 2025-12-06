from fastapi import status


def test_create_task(client, auth_headers):
    response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={"title": "Test Task", "description": "Test Description", "deadline": "2024-12-31T23:59:59"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test Description"


def test_get_tasks(client, auth_headers):
    client.post(
        "/tasks/",
        headers=auth_headers,
        json={"title": "Test Task", "description": "Test Description", "deadline": "2024-12-31T23:59:59"},
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
        json={"title": "Test Task", "description": "Test Description", "deadline": "2024-12-31T23:59:59"},
    )
    task_id = create_response.json()["id"]

    response = client.put(
        f"/tasks/{task_id}",
        headers=auth_headers,
        json={"title": "Updated Task", "description": "Updated Description", "deadline": "2024-12-31T23:59:59"},
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Updated Task"
    assert data["description"] == "Updated Description"


def test_delete_task(client, auth_headers):
    create_response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={"title": "Test Task", "description": "Test Description", "deadline": "2024-12-31T23:59:59"},
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
        json={"title": "Assigned Task", "description": "Test Description", "deadline": "2024-12-31T23:59:59"},
    )

    response = client.get("/tasks/assigned-tasks/", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)


def test_get_task_by_id(client, auth_headers):
    create_response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={"title": "Test Task", "description": "Test Description", "deadline": "2024-12-31T23:59:59"},
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


def test_task_priority_update(client, auth_headers):
    create_response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={
            "title": "Priority Test",
            "description": "Test Description",
            "priority": 3,
            "deadline": "2024-12-31T23:59:59",
        },
    )
    task_id = create_response.json()["id"]

    response = client.put(
        f"/tasks/{task_id}",
        headers=auth_headers,
        json={
            "title": "Priority Test",
            "description": "Test Description",
            "priority": 1,
            "deadline": "2024-12-31T23:59:59",
        },
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["priority"] == 1


def test_reassign_task(client, auth_headers):
    from backend.utils.rate_limiter import rate_limiter

    create_response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={"title": "Reassign Task", "description": "Test Description", "deadline": "2024-12-31T23:59:59"},
    )
    task_id = create_response.json()["id"]

    rate_limiter.attempts = {}
    rate_limiter.blocked_until = {}
    new_user_response = client.post(
        "/users/", json={"email": "newuser@example.com", "password": "testpass123", "secret_word": "secret"}
    )
    new_user_id = new_user_response.json()["id"]

    response = client.put(f"/tasks/{task_id}/reassign?new_user_id={new_user_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["user_id"] == new_user_id


def test_reassign_nonexistent_task(client, auth_headers):
    from backend.utils.rate_limiter import rate_limiter

    rate_limiter.attempts = {}
    rate_limiter.blocked_until = {}
    new_user_response = client.post(
        "/users/", json={"email": "newuser2@example.com", "password": "testpass123", "secret_word": "secret"}
    )
    new_user_id = new_user_response.json()["id"]

    response = client.put(f"/tasks/999999/reassign?new_user_id={new_user_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_assigned_task(client, auth_headers):
    create_response = client.post(
        "/tasks/",
        headers=auth_headers,
        json={"title": "Assigned Task to Delete", "description": "Test Description", "deadline": "2024-12-31T23:59:59"},
    )
    task_id = create_response.json()["id"]

    response = client.delete(f"/tasks/assigned-tasks/{task_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    response = client.get(f"/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_assigned_nonexistent_task(client, auth_headers):
    response = client.delete("/tasks/assigned-tasks/999999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_get_assigned_tasks_with_pagination(client, auth_headers):
    for i in range(3):
        client.post(
            "/tasks/",
            headers=auth_headers,
            json={
                "title": f"Assigned Task {i}",
                "description": "Test Description",
                "deadline": "2024-12-31T23:59:59",
            },
        )

    response = client.get("/tasks/assigned-tasks/?skip=0&limit=2", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) <= 2
