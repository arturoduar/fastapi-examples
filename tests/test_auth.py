import jwt


def test_login_returns_bearer_token(client, settings):
    r = client.post("/auth/token", data={"username": "alice", "password": "alice-password"})
    body = r.json()
    assert r.status_code == 200 and body["token_type"] == "bearer"
    claims = jwt.decode(body["access_token"], settings.secret_key, algorithms=["HS256"])
    assert claims["sub"] == "alice"


def test_login_failures_are_indistinguishable(client):
    wrong_pw = client.post("/auth/token", data={"username": "alice", "password": "nope"})
    no_user = client.post("/auth/token", data={"username": "ghost", "password": "whatever1"})
    for r in (wrong_pw, no_user):
        assert r.status_code == 401
        assert r.json() == {"detail": "Incorrect username or password"}
        assert r.headers["www-authenticate"] == "Bearer"


def test_login_requires_form_fields(client):
    assert client.post("/auth/token", data={"username": "alice"}).status_code == 422
    assert client.post("/auth/token", json={"username": "alice", "password": "x"}).status_code == 422


def test_me_returns_current_user(client, user_headers, admin_headers):
    assert client.get("/auth/me", headers=user_headers).json() == {"username": "alice", "role": "user"}
    assert client.get("/auth/me", headers=admin_headers).json() == {"username": "admin", "role": "admin"}


def test_me_without_or_with_bad_token(client):
    assert client.get("/auth/me").status_code == 401
    r = client.get("/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401 and r.json()["detail"] == "Invalid or expired token"
    assert client.get("/auth/me", headers={"Authorization": "Basic abc"}).status_code == 401


def test_token_signed_with_other_key_is_rejected(client):
    forged = jwt.encode({"sub": "admin", "exp": 4102444800}, "x" * 40, algorithm="HS256")
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {forged}"}).status_code == 401


def test_expired_token_is_rejected(client, settings):
    expired = jwt.encode({"sub": "alice", "exp": 1}, settings.secret_key, algorithm="HS256")
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_token_for_deleted_user_is_rejected(client, settings):
    token = jwt.encode({"sub": "nobody", "exp": 4102444800}, settings.secret_key, algorithm="HS256")
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_register_then_login(client):
    r = client.post("/auth/register", json={"username": "newuser", "password": "s3cretpass"})
    assert r.status_code == 201 and r.json() == {"username": "newuser", "role": "user"}
    assert "password" not in r.text
    r = client.post("/auth/token", data={"username": "newuser", "password": "s3cretpass"})
    assert r.status_code == 200


def test_register_validation_and_duplicates(client):
    assert client.post("/auth/register", json={"username": "ab", "password": "longenough"}).status_code == 422
    assert client.post("/auth/register", json={"username": "Bad Name", "password": "longenough"}).status_code == 422
    assert client.post("/auth/register", json={"username": "okname", "password": "short"}).status_code == 422
    assert client.post("/auth/register", json={"username": "alice", "password": "longenough"}).status_code == 409


def test_register_cannot_choose_role(client):
    r = client.post("/auth/register", json={"username": "sneaky", "password": "longenough", "role": "admin"})
    assert r.status_code == 201 and r.json()["role"] == "user"


def test_admin_user_list(client, user_headers, admin_headers):
    assert client.get("/auth/admin/users").status_code == 401
    assert client.get("/auth/admin/users", headers=user_headers).status_code == 403
    r = client.get("/auth/admin/users", headers=admin_headers)
    assert r.json() == [{"username": "admin", "role": "admin"}, {"username": "alice", "role": "user"}]
