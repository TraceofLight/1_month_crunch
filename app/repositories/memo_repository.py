"""Repository layer for memo database operations."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.memo import Memo


class MemoRepository:
    """Access memo rows through a SQLAlchemy session."""

    def __init__(self, db: Session) -> None:
        """Store the request-scoped database session."""
        self.db = db

    def list(self, query: str | None = None) -> list[Memo]:
        """Return memos ordered by newest first, optionally filtered by text."""
        statement = select(Memo).order_by(Memo.created_at.desc(), Memo.id.desc())
        if query:
            pattern = f"%{query}%"
            statement = statement.where(or_(Memo.title.like(pattern), Memo.content.like(pattern)))
        return list(self.db.execute(statement).scalars())

    def get(self, memo_id: int) -> Memo | None:
        """Return one memo by id or None when it does not exist."""
        return self.db.get(Memo, memo_id)

    def create(self, title: str, content: str, category: str) -> Memo:
        """Insert and return a new memo row."""
        memo = Memo(title=title, content=content, category=category)
        self.db.add(memo)
        self.db.commit()
        self.db.refresh(memo)
        return memo

    def update(self, memo: Memo, title: str, content: str, category: str) -> Memo:
        """Update an existing memo row and return the refreshed row."""
        memo.title = title
        memo.content = content
        memo.category = category
        self.db.commit()
        self.db.refresh(memo)
        return memo

    def delete(self, memo: Memo) -> None:
        """Delete an existing memo row."""
        self.db.delete(memo)
        self.db.commit()
