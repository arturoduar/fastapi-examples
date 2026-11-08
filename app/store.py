"""In-memory repositories (stand-ins for a database)."""
from dataclasses import dataclass

from .errors import DuplicateError, NotFoundError
from .schemas import Item, ItemCreate, ItemUpdate
from .security import hash_password, verify_password


class ItemStore:
    def __init__(self):
        self._items: dict[int, Item] = {}
        self._next_id = 1

    def _check_name(self, name: str, ignore_id: int | None = None):
        for item in self._items.values():
            if item.name.lower() == name.lower() and item.id != ignore_id:
                raise DuplicateError("item", name)

    def create(self, data: ItemCreate) -> Item:
        self._check_name(data.name)
        item = Item(id=self._next_id, **data.model_dump())
        self._items[item.id] = item
        self._next_id += 1
        return item

    def get(self, item_id: int) -> Item:
        try:
            return self._items[item_id]
        except KeyError:
            raise NotFoundError("item", item_id) from None

    def replace(self, item_id: int, data: ItemCreate) -> Item:
        self.get(item_id)
        self._check_name(data.name, ignore_id=item_id)
        item = Item(id=item_id, **data.model_dump())
        self._items[item_id] = item
        return item

    def update(self, item_id: int, data: ItemUpdate) -> Item:
        current = self.get(item_id)
        changes = data.model_dump(exclude_unset=True)
        if "name" in changes and changes["name"] is not None:
            self._check_name(changes["name"], ignore_id=item_id)
        merged = {**current.model_dump(), **{k: v for k, v in changes.items()
                                             if v is not None or k == "description"}}
        item = Item(**merged)
        self._items[item_id] = item
        return item

    def delete(self, item_id: int) -> None:
        self.get(item_id)
        del self._items[item_id]

    def list(self, *, min_price: float | None = None, tag: str | None = None,
             sort: str = "id", limit: int = 20, offset: int = 0) -> tuple[list[Item], int]:
        items = list(self._items.values())
        if min_price is not None:
            items = [i for i in items if i.price >= min_price]
        if tag is not None:
            items = [i for i in items if tag in i.tags]
        items.sort(key=lambda i: getattr(i, sort))
        return items[offset:offset + limit], len(items)


@dataclass
class User:
    username: str
    password_hash: str
    role: str = "user"


class UserStore:
    def __init__(self, hash_iterations: int = 200_000):
        self._users: dict[str, User] = {}
        self._iterations = hash_iterations

    def create(self, username: str, password: str, role: str = "user") -> User:
        if username in self._users:
            raise DuplicateError("user", username)
        user = User(username, hash_password(password, self._iterations), role)
        self._users[username] = user
        return user

    def get(self, username: str) -> User | None:
        return self._users.get(username)

    def authenticate(self, username: str, password: str) -> User | None:
        user = self._users.get(username)
        if user is not None and verify_password(password, user.password_hash):
            return user
        return None

    def all(self) -> list[User]:
        return sorted(self._users.values(), key=lambda u: u.username)
