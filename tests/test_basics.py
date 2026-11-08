import pytest


def test_hello(client):
    assert client.get("/basics/hello").json() == {"message": "Hello, World!"}


def test_hello_name(client):
    assert client.get("/basics/hello/Ada").json() == {"message": "Hello, Ada!"}
    assert client.get("/basics/hello/" + "x" * 51).status_code == 422


def test_add_converts_types(client):
    r = client.get("/basics/add", params={"a": "2", "b": "40"})
    assert r.json() == {"a": 2, "b": 40, "sum": 42}


@pytest.mark.parametrize("params", [{"a": 1}, {"a": "x", "b": 2}, {}])
def test_add_rejects_bad_input(client, params):
    r = client.get("/basics/add", params=params)
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"][0] == "query"


def test_search_defaults_and_list_params(client):
    assert client.get("/basics/search", params={"q": "foo"}).json() == {
        "q": "foo", "limit": 10, "tags": []}
    r = client.get("/basics/search", params={"q": "foo", "tags": ["a", "b"], "limit": 5})
    assert r.json() == {"q": "foo", "limit": 5, "tags": ["a", "b"]}


@pytest.mark.parametrize("params", [{"q": "f"}, {"q": "foo", "limit": 0}, {"q": "foo", "limit": 101}, {}])
def test_search_validation(client, params):
    assert client.get("/basics/search", params=params).status_code == 422


def test_enum_path_parameter(client):
    assert client.get("/basics/sizes/large").json() == {"size": "large", "rank": 2}
    assert client.get("/basics/sizes/huge").status_code == 422


def test_path_converter_allows_slashes(client):
    r = client.get("/basics/files/a/b/c.txt")
    assert r.json() == {"file_path": "a/b/c.txt", "parts": ["a", "b", "c.txt"]}


def test_headers_map_underscores_to_hyphens(client):
    r = client.get("/basics/headers", headers={"X-Token": "abc", "User-Agent": "pytest-agent"})
    assert r.json() == {"user_agent": "pytest-agent", "x_token": "abc"}
    assert client.get("/basics/headers").json()["x_token"] is None


def test_echo_body(client):
    assert client.post("/basics/echo", json={"text": "ab", "repeat": 3}).json() == {"result": "ababab"}
    assert client.post("/basics/echo", json={"text": "ab"}).json() == {"result": "ab"}


@pytest.mark.parametrize("body", [{"text": ""}, {"text": "a", "repeat": 6}, {"repeat": 2}, {"text": 5}])
def test_echo_validation(client, body):
    r = client.post("/basics/echo", json=body)
    assert r.status_code == 422
    assert r.json()["detail"][0]["loc"][0] == "body"
