from datetime import datetime, timedelta

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


def test_get_tasks_with_filters(client, auth_headers):
    tasks_data = [
        {"title": "High Priority", "description": "Test", "deadline": "2024-12-31T23:59:59", "priority": 1},
        {"title": "Low Priority", "description": "Test", "deadline": "2024-12-31T23:59:59", "priority": 3},
        {"title": "Medium Priority", "description": "Test", "deadline": "2024-12-31T23:59:59", "priority": 2}
    ]

    for task in tasks_data:
        response = client.post("/tasks/", headers=auth_headers, json=task)
        assert response.status_code == status.HTTP_200_OK

    response = client.get("/tasks/?priority=1", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 1
    assert data[0]["priority"] == 1


def test_update_task_status(client, auth_headers):
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
        f"/tasks/{task_id}/complete",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK


def test_get_tasks_by_date_range(client, auth_headers):
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(days=7)

    tasks_data = [
        {"title": "Today", "description": "Test", "deadline": today.isoformat()},
        {"title": "Tomorrow", "description": "Test", "deadline": tomorrow.isoformat()},
        {"title": "Next Week", "description": "Test", "deadline": next_week.isoformat()}
    ]

    for task in tasks_data:
        response = client.post("/tasks/", headers=auth_headers, json=task)
        assert response.status_code == status.HTTP_200_OK

    response = client.get(
        f"/tasks/?start_date={today.date().isoformat()}&end_date={tomorrow.date().isoformat()}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2


def test_delete_completed_tasks(client, auth_headers):
    tasks = []
    for i in range(3):
        response = client.post(
            "/tasks/",
            headers=auth_headers,
            json={
                "title": f"Task {i}",
                "description": "Test Description",
                "deadline": "2024-12-31T23:59:59"
            }
        )
        tasks.append(response.json()["id"])

    for task_id in tasks:
        client.put(
            f"/tasks/{task_id}/status",
            headers=auth_headers,
            json={"status": "completed"}
        )

    response = client.delete("/tasks/completed", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK

    response = client.get("/tasks/", headers=auth_headers)
    assert len(response.json()) == 0
