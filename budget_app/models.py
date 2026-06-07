"""데이터 구조(dataclass) 정의.

저장 포맷은 JSONL 이므로 각 모델은 ``to_dict``/``from_dict`` 로 직렬화 계약을
명확히 한다. 타입 힌트로 각 필드의 형(型)을 고정해 저장소/서비스 계층이
일관된 형태의 데이터를 주고받도록 한다.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

VALID_TYPES: tuple[str, ...] = ("income", "expense")


@dataclass
class Transaction:
    """단일 거래 내역.

    Attributes:
        id: 유일 식별자(예: ``TX-000012``).
        type: ``income`` 또는 ``expense``.
        date: ``YYYY-MM-DD`` 형식 문자열.
        amount: 양의 정수 금액.
        category: 등록된 카테고리 이름.
        memo: 선택 메모.
        tags: 선택 태그 목록.
    """

    id: str
    type: str
    date: str
    amount: int
    category: str
    memo: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """JSONL 직렬화를 위한 dict 로 변환한다."""
        return {
            "id": self.id,
            "type": self.type,
            "date": self.date,
            "amount": self.amount,
            "category": self.category,
            "memo": self.memo,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Transaction":
        """JSONL 한 줄을 파싱한 dict 로부터 ``Transaction`` 을 만든다."""
        return cls(
            id=str(data["id"]),
            type=str(data["type"]),
            date=str(data["date"]),
            amount=int(data["amount"]),
            category=str(data["category"]),
            memo=str(data.get("memo", "")),
            tags=list(data.get("tags", []) or []),
        )


@dataclass
class Category:
    """거래에 사용할 수 있는 카테고리.

    Attributes:
        name: 카테고리 이름(유일).
    """

    name: str

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Category":
        return cls(name=str(data["name"]))


@dataclass
class Budget:
    """월 단위 예산.

    Attributes:
        month: ``YYYY-MM`` 형식 문자열.
        amount: 양의 정수 예산 금액.
    """

    month: str
    amount: int

    def to_dict(self) -> dict[str, Any]:
        return {"month": self.month, "amount": self.amount}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Budget":
        return cls(month=str(data["month"]), amount=int(data["amount"]))


@dataclass
class Recurring:
    """매월 자동 생성되는 반복 내역 규칙(보너스 기능).

    Attributes:
        id: 유일 식별자(예: ``RC-0001``).
        type: ``income`` 또는 ``expense``.
        day: 매월 적용 일(1~28).
        amount: 양의 정수 금액.
        category: 등록된 카테고리 이름.
        memo: 선택 메모.
        tags: 선택 태그 목록.
    """

    id: str
    type: str
    day: int
    amount: int
    category: str
    memo: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "day": self.day,
            "amount": self.amount,
            "category": self.category,
            "memo": self.memo,
            "tags": list(self.tags),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Recurring":
        return cls(
            id=str(data["id"]),
            type=str(data["type"]),
            day=int(data["day"]),
            amount=int(data["amount"]),
            category=str(data["category"]),
            memo=str(data.get("memo", "")),
            tags=list(data.get("tags", []) or []),
        )
