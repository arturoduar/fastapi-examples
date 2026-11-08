from fastapi.testclient import TestClient

from app.config import Settings
from app.deps import get_settings
from app.main import create_app


def test_root_and_health(client):
    assert client.get("/").json()["docs"] == "/docs"
    assert client.get("/health").json()["status"] == "ok"


def test_process_time_middleware_header(client):
    r = client.get("/health")
    assert float(r.headers["x-process-time"]) >= 0
    assert "x-process-time" in client.get("/items/999").headers    # also on error responses


def test_lifespan_runs_startup_and_shutdown(app):
    assert app.state.events == []
    with TestClient(app) as c:
        c.get("/health")
        assert app.state.events == ["startup"]
    assert app.state.events == ["startup", "shutdown"]


def test_openapi_schema_lists_routes(client):
    schema = client.get("/openapi.json").json()
    assert schema["info"]["title"] == "FastAPI Examples"
    for path in ("/items", "/items/{item_id}", "/auth/token", "/basics/search", "/uploads/file"):
        assert path in schema["paths"], path
    assert client.get("/docs").status_code == 200


def test_unknown_route_and_method(client):
    assert client.get("/nope").status_code == 404
    assert client.delete("/health").status_code == 405


def test_can_disable_seed_data():
    app = create_app(Settings(seed_demo_data=False, hash_iterations=1000))
    with TestClient(app) as c:
        assert c.get("/items").json()["total"] == 0
        assert c.post("/auth/token", data={"username": "alice", "password": "alice-password"}).status_code == 401


def test_dependency_override(app):
    """dependency_overrides swaps a dependency for the duration of a test."""
    app.dependency_overrides[get_settings] = lambda: Settings(
        secret_key="another-secret-key-0123456789-abcdefgh", hash_iterations=1000)
    with TestClient(app) as c:
        # tokens are now signed/verified with the overriding settings' key
        r = c.post("/auth/token", data={"username": "alice", "password": "alice-password"})
        assert r.status_code == 200
        token = r.json()["access_token"]
        assert c.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 200
    app.dependency_overrides.clear()
    with TestClient(app) as c:      # original key again: the token no longer verifies
        assert c.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401
