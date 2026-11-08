"""Pydantic request/response models."""
from enum import Enum

from pydantic import BaseModel, Field


class Size(str, Enum):
    small = "small"
    medium = "medium"
    large = "large"


class Echo(BaseModel):
    text: str = Field(min_length=1, max_length=100)
    repeat: int = Field(1, ge=1, le=5)


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)
    description: str | None = Field(None, max_length=500)
    tags: list[str] = Field(default_factory=list)

    model_config = {"json_schema_extra": {"examples": [
        {"name": "Widget", "price": 9.99, "description": "A small widget", "tags": ["tools"]}]}}


class ItemUpdate(BaseModel):
    """PATCH body: every field optional; only the fields sent are changed."""
    name: str | None = Field(None, min_length=1, max_length=100)
    price: float | None = Field(None, gt=0)
    description: str | None = Field(None, max_length=500)
    tags: list[str] | None = None


class Item(ItemCreate):
    id: int


class ItemPage(BaseModel):
    items: list[Item]
    total: int
    limit: int
    offset: int


class UserCreate(BaseModel):
    username: str = Field(pattern=r"^[a-z0-9_]{3,20}$")
    password: str = Field(min_length=8, max_length=128)


class UserPublic(BaseModel):
    username: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class Notification(BaseModel):
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    message: str = Field(min_length=1, max_length=500)


class Queued(BaseModel):
    status: str = "queued"


class UploadInfo(BaseModel):
    filename: str | None
    content_type: str | None
    size: int
    sha256: str
