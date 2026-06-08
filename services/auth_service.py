"""Authentication business logic."""

from __future__ import annotations

from sqlalchemy.orm import Session

from auth.passwords import verify_password
from models import User
from repositories.user_repository import get_user_by_username


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """Return a user when credentials are valid."""

    user = get_user_by_username(db, username)
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
