import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def settings():
    # Few PBKDF2 iterations keep the tests fast; the secret is long enough for HS256.
    return Settings(secret_key="test-secret-key-0123456789-abcdefghij", hash_iterations=1000,
                    token_minutes=5)


@pytest.fixture
def app(settings):
    """A fresh application (and fresh in-memory data) for every test."""
    return create_app(settings)


@pytest.fixture
def client(app):
    with TestClient(app) as c:      # `with` runs the lifespan startup/shutdown
        yield c


@pytest.fixture
def login(client):
    def _login(username, password):
        r = client.post("/auth/token", data={"username": username, "password": password})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}
    return _login


@pytest.fixture
def user_headers(login):
    return login("alice", "alice-password")


@pytest.fixture
def admin_headers(login):
    return login("admin", "admin-password")
