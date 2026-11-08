"""Plain unit tests for the non-web parts (no HTTP involved)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.config import Settings
from app.errors import DuplicateError, NotFoundError
from app.schemas import ItemCreate, ItemUpdate
from app.security import (InvalidTokenError, create_access_token, decode_access_token,
                          hash_password, verify_password)
from app.store import ItemStore, UserStore

KEY = "unit-test-secret-key-0123456789-abcdef"


def test_password_hash_roundtrip_and_salting():
    h1, h2 = hash_password("pw-1234567", 1000), hash_password("pw-1234567", 1000)
    assert h1 != h2 and h1.startswith("pbkdf2_sha256$1000$")
    assert verify_password("pw-1234567", h1) and verify_password("pw-1234567", h2)
    assert not verify_password("pw-1234568", h1)
    assert not verify_password("x", "garbage") and not verify_password("x", "a$b$c$d")


def test_token_roundtrip_and_failures():
    token = create_access_token("alice", KEY, minutes=5)
    assert decode_access_token(token, KEY) == "alice"
    with pytest.raises(InvalidTokenError):
        decode_access_token(token, KEY + "x")
    with pytest.raises(InvalidTokenError):
        decode_access_token("junk", KEY)
    old = create_access_token("alice", KEY, 1, now=datetime.now(timezone.utc) - timedelta(hours=1))
    with pytest.raises(InvalidTokenError):
        decode_access_token(old, KEY)


def test_item_store_crud_and_errors():
    s = ItemStore()
    a = s.create(ItemCreate(name="A", price=1))
    b = s.create(ItemCreate(name="B", price=2, tags=["t"]))
    assert (a.id, b.id) == (1, 2)
    with pytest.raises(DuplicateError):
        s.create(ItemCreate(name="a", price=3))
    assert s.update(1, ItemUpdate(price=9)).price == 9
    s.delete(1)
    with pytest.raises(NotFoundError):
        s.get(1)
    assert s.create(ItemCreate(name="C", price=1)).id == 3      # ids are never reused


def test_item_store_list_filters():
    s = ItemStore()
    for n, p, t in [("a", 3, ["x"]), ("b", 1, ["y"]), ("c", 2, ["x", "y"])]:
        s.create(ItemCreate(name=n, price=p, tags=t))
    items, total = s.list(sort="price")
    assert [i.name for i in items] == ["b", "c", "a"] and total == 3
    items, total = s.list(tag="x", limit=1, offset=1)
    assert [i.name for i in items] == ["c"] and total == 2
    assert s.list(min_price=2.5)[1] == 1


def test_user_store():
    u = UserStore(1000)
    u.create("bob", "bob-password")
    assert u.authenticate("bob", "bob-password").username == "bob"
    assert u.authenticate("bob", "wrong") is None and u.authenticate("zed", "x") is None
    with pytest.raises(DuplicateError):
        u.create("bob", "other-password")


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("APP_SECRET_KEY", "k" * 40)
    monkeypatch.setenv("APP_TOKEN_MINUTES", "7")
    monkeypatch.setenv("APP_SEED_DEMO_DATA", "false")
    s = Settings.from_env()
    assert s.secret_key == "k" * 40 and s.token_minutes == 7 and s.seed_demo_data is False
