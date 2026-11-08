import pytest


def new_item(**over):
    return {"name": "Thing", "price": 5.0, "tags": ["x"], **over}


def test_seeded_items_are_listed(client):
    r = client.get("/items")
    body = r.json()
    assert r.status_code == 200
    assert body["total"] == 3 and body["limit"] == 20 and body["offset"] == 0
    assert [i["name"] for i in body["items"]] == ["Widget", "Gadget", "Gizmo"]


def test_create_returns_201_and_item(client):
    r = client.post("/items", json=new_item())
    assert r.status_code == 201
    assert r.json() == {"id": 4, "name": "Thing", "price": 5.0, "description": None, "tags": ["x"]}
    assert client.get("/items/4").json()["name"] == "Thing"


def test_create_duplicate_name_conflicts_case_insensitively(client):
    r = client.post("/items", json=new_item(name="widget"))
    assert r.status_code == 409
    assert "already exists" in r.json()["detail"]


@pytest.mark.parametrize("body", [new_item(name=""), new_item(price=0), new_item(price=-1),
                                  {"name": "x"}, new_item(tags="nope")])
def test_create_validation(client, body):
    assert client.post("/items", json=body).status_code == 422


def test_read_missing_and_invalid_id(client):
    assert client.get("/items/999").status_code == 404
    assert client.get("/items/999").json()["detail"] == "item 999 not found"
    assert client.get("/items/0").status_code == 422
    assert client.get("/items/abc").status_code == 422


def test_pagination(client):
    r = client.get("/items", params={"limit": 2, "offset": 1}).json()
    assert [i["name"] for i in r["items"]] == ["Gadget", "Gizmo"]
    assert (r["total"], r["limit"], r["offset"]) == (3, 2, 1)
    assert client.get("/items", params={"limit": 0}).status_code == 422
    assert client.get("/items", params={"limit": 101}).status_code == 422
    assert client.get("/items", params={"offset": -1}).status_code == 422


def test_filtering_and_sorting(client):
    names = lambda r: [i["name"] for i in r.json()["items"]]
    assert names(client.get("/items", params={"tag": "tech"})) == ["Gadget", "Gizmo"]
    assert names(client.get("/items", params={"min_price": 5})) == ["Widget", "Gadget"]
    assert names(client.get("/items", params={"sort": "price"})) == ["Gizmo", "Widget", "Gadget"]
    assert names(client.get("/items", params={"sort": "name"})) == ["Gadget", "Gizmo", "Widget"]
    assert client.get("/items", params={"sort": "color"}).status_code == 422


def test_put_replaces_everything(client):
    r = client.put("/items/1", json=new_item(name="Renamed", description="d"))
    assert r.status_code == 200
    assert r.json() == {"id": 1, "name": "Renamed", "price": 5.0, "description": "d", "tags": ["x"]}


def test_put_missing_and_duplicate(client):
    assert client.put("/items/99", json=new_item()).status_code == 404
    assert client.put("/items/1", json=new_item(name="Gadget")).status_code == 409
    assert client.put("/items/1", json=new_item(name="Widget")).status_code == 200  # own name is fine


def test_patch_changes_only_sent_fields(client):
    r = client.patch("/items/1", json={"price": 11.0})
    assert r.json() == {"id": 1, "name": "Widget", "price": 11.0, "description": None, "tags": ["tools"]}
    r = client.patch("/items/1", json={"description": "now described"}).json()
    assert r["description"] == "now described" and r["price"] == 11.0
    r = client.patch("/items/1", json={"description": None}).json()
    assert r["description"] is None


def test_patch_errors(client):
    assert client.patch("/items/99", json={"price": 1}).status_code == 404
    assert client.patch("/items/1", json={"name": "Gadget"}).status_code == 409
    assert client.patch("/items/1", json={"price": -5}).status_code == 422


def test_delete_requires_authentication(client):
    r = client.delete("/items/1")
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == "Bearer"


def test_delete_requires_admin_role(client, user_headers):
    assert client.delete("/items/1", headers=user_headers).status_code == 403
    assert client.get("/items/1").status_code == 200


def test_admin_can_delete(client, admin_headers):
    r = client.delete("/items/1", headers=admin_headers)
    assert r.status_code == 204 and r.content == b""
    assert client.get("/items/1").status_code == 404
    assert client.get("/items").json()["total"] == 2
    assert client.delete("/items/1", headers=admin_headers).status_code == 404


def test_each_test_gets_fresh_data(client):
    assert client.get("/items").json()["total"] == 3
