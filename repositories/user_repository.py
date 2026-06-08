"""Data access helpers for users."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import User


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Return a user by primary key."""

    return db.get(User, user_id)


def get_user_by_username(db: Session, username: str) -> User | None:
    """Return a user by login name."""

    return db.scalar(select(User).where(User.username == username))
