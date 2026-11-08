"""Registration, OAuth2 password login returning a JWT, and protected endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..config import Settings
from ..deps import get_current_user, get_settings, get_user_store, require_role
from ..schemas import Token, UserCreate, UserPublic
from ..security import create_access_token
from ..store import User, UserStore

router = APIRouter(prefix="/auth", tags=["auth"])


def to_public(user: User) -> UserPublic:
    return UserPublic(username=user.username, role=user.role)


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, users: Annotated[UserStore, Depends(get_user_store)]):
    return to_public(users.create(data.username, data.password))


@router.post("/token", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()],
          users: Annotated[UserStore, Depends(get_user_store)],
          settings: Annotated[Settings, Depends(get_settings)]):
    """Form-encoded ``username`` and ``password`` (what the /docs "Authorize" button sends)."""
    user = users.authenticate(form.username, form.password)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    token = create_access_token(user.username, settings.secret_key, settings.token_minutes)
    return Token(access_token=token)


@router.get("/me", response_model=UserPublic)
def me(user: Annotated[User, Depends(get_current_user)]):
    return to_public(user)


@router.get("/admin/users", response_model=list[UserPublic])
def list_users(_admin: Annotated[User, Depends(require_role("admin"))],
               users: Annotated[UserStore, Depends(get_user_store)]):
    return [to_public(u) for u in users.all()]
