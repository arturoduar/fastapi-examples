import hashlib
import json

import pytest


# ---- background tasks
def test_notify_returns_202_and_task_runs(client):
    assert client.get("/background/log").json() == []
    r = client.post("/background/notify", json={"email": "a@example.com", "message": "hi"})
    assert r.status_code == 202 and r.json() == {"status": "queued"}
    assert client.get("/background/log").json() == ["to=a@example.com message=hi"]


@pytest.mark.parametrize("body", [{"email": "not-an-email", "message": "x"},
                                  {"email": "a@example.com", "message": ""},
                                  {"message": "x"}])
def test_notify_validation_and_no_task_on_error(client, body):
    assert client.post("/background/notify", json=body).status_code == 422
    assert client.get("/background/log").json() == []


# ---- streaming
def test_count_stream(client):
    r = client.get("/stream/count", params={"n": 4})
    assert r.headers["content-type"].startswith("text/plain")
    assert r.text.split() == ["1", "2", "3", "4"]
    assert client.get("/stream/count").text.split() == ["1", "2", "3", "4", "5"]
    assert client.get("/stream/count", params={"n": 0}).status_code == 422


def test_server_sent_events(client):
    r = client.get("/stream/sse", params={"n": 3})
    assert r.headers["content-type"].startswith("text/event-stream")
    events = [e for e in r.text.split("\n\n") if e]
    assert [json.loads(e.removeprefix("data: ")) for e in events] == [
        {"tick": 0}, {"tick": 1}, {"tick": 2}]


def test_websocket_echo(client):
    with client.websocket_connect("/stream/ws/echo") as ws:
        ws.send_text("hello")
        assert ws.receive_text() == "echo: hello"
        ws.send_text("again")
        assert ws.receive_text() == "echo: again"


# ---- uploads and forms
def test_file_upload(client):
    payload = b"hello world"
    r = client.post("/uploads/file", files={"file": ("hello.txt", payload, "text/plain")})
    assert r.status_code == 200
    assert r.json() == {"filename": "hello.txt", "content_type": "text/plain", "size": 11,
                        "sha256": hashlib.sha256(payload).hexdigest()}


def test_upload_missing_file(client):
    assert client.post("/uploads/file").status_code == 422


def test_upload_size_limit(app, client):
    app.state.settings = app.state.settings.model_copy(update={"max_upload_bytes": 10})
    r = client.post("/uploads/file", files={"file": ("big.bin", b"x" * 11)})
    assert r.status_code == 413
    assert client.post("/uploads/file", files={"file": ("ok.bin", b"x" * 10)}).status_code == 200


def test_form_fields(client):
    assert client.post("/uploads/form", data={"name": "Ada", "age": "36"}).json() == {"name": "Ada", "age": 36}
    assert client.post("/uploads/form", data={"name": "Ada", "age": "-1"}).status_code == 422
    assert client.post("/uploads/form", data={"name": "Ada"}).status_code == 422
