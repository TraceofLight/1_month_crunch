"""Shared FastAPI dependencies for routers."""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.memo_repository import MemoRepository
from app.services.memo_service import MemoService


def get_memo_service(db: Session = Depends(get_db)) -> MemoService:
    """Build a memo service from the request-scoped database session."""
    return MemoService(MemoRepository(db))
