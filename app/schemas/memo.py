"""DTOs used by the memo service and router layers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.models.memo import Memo


@dataclass(frozen=True)
class MemoFormData:
    """Normalized form input for creating or updating a memo."""

    title: str
    content: str
    category: str


@dataclass(frozen=True)
class MemoView:
    """Template-facing memo data that hides direct ORM usage from routers."""

    id: int
    title: str
    content: str
    category: str
    created_at: datetime
    updated_at: datetime
    created_at_text: str
    updated_at_text: str

    @classmethod
    def from_model(cls, memo: Memo) -> "MemoView":
        """Build a template DTO from a SQLAlchemy model instance."""
        return cls(
            id=memo.id,
            title=memo.title,
            content=memo.content,
            category=memo.category,
            created_at=memo.created_at,
            updated_at=memo.updated_at,
            created_at_text=memo.created_at.strftime("%Y-%m-%d %H:%M"),
            updated_at_text=memo.updated_at.strftime("%Y-%m-%d %H:%M"),
        )
