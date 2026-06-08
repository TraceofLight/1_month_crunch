"""Service layer containing memo business rules."""

from __future__ import annotations

from app.repositories.memo_repository import MemoRepository
from app.schemas.memo import MemoFormData, MemoView


class MemoService:
    """Coordinate memo validation and repository calls."""

    def __init__(self, repository: MemoRepository) -> None:
        """Store the repository used for persistence."""
        self.repository = repository

    def list_memos(self, query: str | None = None) -> list[MemoView]:
        """Return memo DTOs for list rendering."""
        normalized_query = query.strip() if query else None
        return [MemoView.from_model(memo) for memo in self.repository.list(normalized_query)]

    def get_memo(self, memo_id: int) -> MemoView | None:
        """Return one memo DTO or None when the memo does not exist."""
        memo = self.repository.get(memo_id)
        return MemoView.from_model(memo) if memo else None

    def create_memo(self, form: MemoFormData) -> tuple[MemoView | None, list[str]]:
        """Validate form data, create a memo, and return errors when invalid."""
        normalized, errors = self._normalize_and_validate(form)
        if errors:
            return None, errors
        memo = self.repository.create(normalized.title, normalized.content, normalized.category)
        return MemoView.from_model(memo), []

    def update_memo(self, memo_id: int, form: MemoFormData) -> tuple[MemoView | None, list[str], bool]:
        """Validate form data and update an existing memo."""
        memo = self.repository.get(memo_id)
        if memo is None:
            return None, [], False

        normalized, errors = self._normalize_and_validate(form)
        if errors:
            return MemoView.from_model(memo), errors, True

        updated = self.repository.update(memo, normalized.title, normalized.content, normalized.category)
        return MemoView.from_model(updated), [], True

    def delete_memo(self, memo_id: int) -> bool:
        """Delete a memo and return whether a row was found."""
        memo = self.repository.get(memo_id)
        if memo is None:
            return False
        self.repository.delete(memo)
        return True

    def _normalize_and_validate(self, form: MemoFormData) -> tuple[MemoFormData, list[str]]:
        """Trim form values and enforce required fields."""
        normalized = MemoFormData(
            title=form.title.strip(),
            content=form.content.strip(),
            category=form.category.strip() or "일반",
        )
        errors: list[str] = []
        if not normalized.title:
            errors.append("제목은 필수입니다.")
        if not normalized.content:
            errors.append("내용은 필수입니다.")
        return normalized, errors
