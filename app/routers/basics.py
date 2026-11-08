"""Path, query and header parameters, validation, enums, and a JSON body."""
from typing import Annotated

from fastapi import APIRouter, Header, Path, Query

from ..schemas import Echo, Size

router = APIRouter(prefix="/basics", tags=["basics"])


@router.get("/hello")
def hello():
    return {"message": "Hello, World!"}


@router.get("/hello/{name}")
def hello_name(name: Annotated[str, Path(min_length=1, max_length=50)]):
    return {"message": f"Hello, {name}!"}


@router.get("/add")
def add(a: int, b: int):
    """``a`` and ``b`` are required query parameters, converted to int (422 if they are not)."""
    return {"a": a, "b": b, "sum": a + b}


@router.get("/search")
def search(q: Annotated[str, Query(min_length=2, max_length=50)],
           limit: Annotated[int, Query(ge=1, le=100)] = 10,
           tags: Annotated[list[str] | None, Query()] = None):
    """Repeat ``tags`` to send a list: ``/basics/search?q=foo&tags=a&tags=b``."""
    return {"q": q, "limit": limit, "tags": tags or []}


@router.get("/sizes/{size}")
def size_info(size: Size):
    """Path parameter restricted to an Enum; other values give 422."""
    return {"size": size, "rank": list(Size).index(size)}


@router.get("/files/{file_path:path}")
def file_path_echo(file_path: str):
    """``:path`` lets the parameter contain slashes."""
    return {"file_path": file_path, "parts": file_path.split("/")}


@router.get("/headers")
def headers(user_agent: Annotated[str | None, Header()] = None,
            x_token: Annotated[str | None, Header()] = None):
    """Header names map underscores to hyphens: ``x_token`` reads ``X-Token``."""
    return {"user_agent": user_agent, "x_token": x_token}


@router.post("/echo")
def echo(body: Echo):
    return {"result": body.text * body.repeat}
