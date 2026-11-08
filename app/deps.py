"""Reusable dependencies: settings, stores, pagination, authentication, role checks."""
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Query, Request, status
from fastapi.security import OAuth2PasswordBearer

from .config import Settings
from .security import InvalidTokenError, decode_access_token
from .store import ItemStore, User, UserStore

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_item_store(request: Request) -> ItemStore:
    return request.app.state.items


def get_user_store(request: Request) -> UserStore:
    return request.app.state.users


def get_audit_log(request: Request) -> list[str]:
    return request.app.state.audit_log


@dataclass
class Pagination:
    limit: int
    offset: int


def pagination(limit: Annotated[int, Query(ge=1, le=100)] = 20,
               offset: Annotated[int, Query(ge=0)] = 0) -> Pagination:
    return Pagination(limit, offset)


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],
                     settings: Annotated[Settings, Depends(get_settings)],
                     users: Annotated[UserStore, Depends(get_user_store)]) -> User:
    unauthorized = HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token",
                                 headers={"WWW-Authenticate": "Bearer"})
    try:
        username = decode_access_token(token, settings.secret_key)
    except InvalidTokenError:
        raise unauthorized from None
    user = users.get(username)
    if user is None:
        raise unauthorized
    return user


def require_role(role: str):
    """Dependency factory: the current user must have ``role`` (else 403)."""
    def checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role != role:
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"Requires role '{role}'")
        return user
    return checker
