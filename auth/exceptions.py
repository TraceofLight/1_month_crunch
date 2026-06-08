"""Application exception types."""

from __future__ import annotations


class AuthRequiredError(Exception):
    """Raised when an anonymous request tries to access a protected resource."""

    def __init__(self, message: str = "로그인이 필요합니다.") -> None:
        self.message = message


class DomainError(Exception):
    """Raised when business rules reject an operation."""

    def __init__(self, message: str) -> None:
        self.message = message
