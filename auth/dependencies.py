"""FastAPI dependencies for authentication and authorization."""

from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from auth.exceptions import AuthRequiredError
from database import get_db
from models import User
from repositories.user_repository import get_user_by_id


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Resolve the current user from the signed session cookie."""

    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    return get_user_by_id(db, int(user_id))


def require_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Require a logged-in user for protected routes."""

    user = get_current_user(request, db)
    if user is None:
        raise AuthRequiredError()
    return user
