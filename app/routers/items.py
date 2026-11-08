"""CRUD with response models, status codes, pagination, filtering and role-protected delete."""
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Path, Query, status

from ..deps import Pagination, get_item_store, pagination, require_role
from ..schemas import Item, ItemCreate, ItemPage, ItemUpdate
from ..store import ItemStore, User

router = APIRouter(prefix="/items", tags=["items"])

Store = Annotated[ItemStore, Depends(get_item_store)]
ItemId = Annotated[int, Path(ge=1)]


@router.post("", response_model=Item, status_code=status.HTTP_201_CREATED)
def create_item(data: ItemCreate, store: Store):
    return store.create(data)


@router.get("", response_model=ItemPage)
def list_items(store: Store,
               page: Annotated[Pagination, Depends(pagination)],
               min_price: Annotated[float | None, Query(ge=0)] = None,
               tag: str | None = None,
               sort: Literal["id", "name", "price"] = "id"):
    items, total = store.list(min_price=min_price, tag=tag, sort=sort,
                              limit=page.limit, offset=page.offset)
    return ItemPage(items=items, total=total, limit=page.limit, offset=page.offset)


@router.get("/{item_id}", response_model=Item)
def read_item(item_id: ItemId, store: Store):
    return store.get(item_id)


@router.put("/{item_id}", response_model=Item)
def replace_item(item_id: ItemId, data: ItemCreate, store: Store):
    return store.replace(item_id, data)


@router.patch("/{item_id}", response_model=Item)
def update_item(item_id: ItemId, data: ItemUpdate, store: Store):
    return store.update(item_id, data)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: ItemId, store: Store,
                _admin: Annotated[User, Depends(require_role("admin"))]):
    """Only users with the ``admin`` role may delete."""
    store.delete(item_id)
