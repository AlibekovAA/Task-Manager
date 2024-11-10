import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base
from main import app
from backend.utils import get_db

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def user_headers(client):
    client.post(
        "/users/",
        json={
            "email": "user@example.com",
            "password": "userpass123",
            "secret_word": "secret"
        }
    )

    response = client.post(
        "/token",
        data={
            "username": "user@example.com",
            "password": "userpass123"
        }
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def create_task(client, auth_headers):
    def _create_task(title="Test Task", description="Test Description", deadline="2024-12-31T23:59:59"):
        return client.post(
            "/tasks/",
            headers=auth_headers,
            json={
                "title": title,
                "description": description,
                "deadline": deadline
            }
        )
    return _create_task


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
