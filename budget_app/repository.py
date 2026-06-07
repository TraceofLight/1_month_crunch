"""저장소 계층: 파일 1개 = 저장소 1개.

각 저장소는 ``storage`` 모듈의 저수준 I/O 위에서 특정 모델의 영속화를
담당한다. 저장 파일은 다음과 같이 3개 이상으로 분리된다.

    transactions.jsonl : 거래 내역
    categories.jsonl   : 카테고리 목록
    budgets.jsonl      : 월별 예산
    recurring.jsonl    : 반복 내역 규칙(보너스)

거래 조회는 제너레이터를 그대로 반환해 상위 계층까지 스트리밍이 유지된다.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator

from .errors import StorageError
from .models import Budget, Category, Recurring, Transaction
from . import storage

DEFAULT_CATEGORIES: tuple[str, ...] = ("food", "transport", "rent", "salary", "etc")


def _loads(line: str) -> dict:
    """JSONL 한 줄을 dict 로 파싱한다(손상 줄은 명확한 오류로 변환)."""
    try:
        return json.loads(line)
    except json.JSONDecodeError as exc:
        raise StorageError(
            "저장 파일의 한 줄을 읽을 수 없습니다(JSON 손상).",
            hint="해당 파일을 백업본으로 복구하거나 손상된 줄을 제거하세요.",
        ) from exc


def _dumps(payload: dict) -> str:
    """dict 를 JSONL 한 줄 문자열로 직렬화한다(한글 보존)."""
    return json.dumps(payload, ensure_ascii=False)


class TransactionRepository:
    """``transactions.jsonl`` 에 대한 거래 저장소.

    추가는 append, 수정/삭제는 전체 재작성 + 원자적 교체로 처리한다.
    """

    def __init__(self, path: Path) -> None:
        self.path = path

    def iter_recent(self) -> Iterator[Transaction]:
        """최신(파일 끝)부터 거래를 스트리밍한다."""
        for line in storage.iter_lines_reverse(self.path):
            yield Transaction.from_dict(_loads(line))

    def iter_all(self) -> Iterator[Transaction]:
        """과거(파일 앞)부터 거래를 스트리밍한다(집계용)."""
        for line in storage.iter_lines_forward(self.path):
            yield Transaction.from_dict(_loads(line))

    def next_id(self) -> str:
        """기존 ID 중 최대 일련번호 + 1 로 새 ID 를 만든다."""
        max_seq = 0
        for tx in self.iter_all():
            if tx.id.startswith("TX-"):
                try:
                    max_seq = max(max_seq, int(tx.id[3:]))
                except ValueError:
                    continue
        return f"TX-{max_seq + 1:06d}"

    def add(self, tx: Transaction) -> None:
        """거래 한 건을 파일 끝에 추가한다."""
        storage.append_line(self.path, _dumps(tx.to_dict()))

    def get(self, tx_id: str) -> Transaction | None:
        """ID 로 거래를 찾는다(없으면 None)."""
        for tx in self.iter_recent():
            if tx.id == tx_id:
                return tx
        return None

    def replace_all(self, transactions: list[Transaction]) -> None:
        """전체 거래를 원자적으로 다시 쓴다(수정/삭제 반영)."""
        storage.atomic_write_lines(
            self.path, (_dumps(tx.to_dict()) for tx in transactions)
        )


class CategoryStore:
    """``categories.jsonl`` 에 대한 카테고리 저장소."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def list(self) -> list[str]:
        """등록된 카테고리 이름을 입력 순서대로 반환한다."""
        names: list[str] = []
        for line in storage.iter_lines_forward(self.path):
            names.append(Category.from_dict(_loads(line)).name)
        return names

    def exists(self, name: str) -> bool:
        return name in self.list()

    def add(self, name: str) -> bool:
        """카테고리를 추가한다. 이미 있으면 False, 추가하면 True."""
        if self.exists(name):
            return False
        storage.append_line(self.path, _dumps(Category(name=name).to_dict()))
        return True

    def remove(self, name: str) -> None:
        """카테고리를 제거한다(존재 여부는 상위 서비스가 검증)."""
        remaining = [n for n in self.list() if n != name]
        storage.atomic_write_lines(
            self.path, (_dumps(Category(name=n).to_dict()) for n in remaining)
        )

    def ensure_defaults(self) -> list[str]:
        """카테고리 파일이 비어 있으면 기본 카테고리를 생성한다(안 A)."""
        if self.list():
            return []
        for name in DEFAULT_CATEGORIES:
            storage.append_line(self.path, _dumps(Category(name=name).to_dict()))
        return list(DEFAULT_CATEGORIES)


class BudgetStore:
    """``budgets.jsonl`` 에 대한 월별 예산 저장소."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def all(self) -> dict[str, int]:
        """``{month: amount}`` 형태로 전체 예산을 반환한다."""
        result: dict[str, int] = {}
        for line in storage.iter_lines_forward(self.path):
            budget = Budget.from_dict(_loads(line))
            result[budget.month] = budget.amount  # 같은 달은 최신 값 우선
        return result

    def get(self, month: str) -> int | None:
        return self.all().get(month)

    def set(self, month: str, amount: int) -> None:
        """월 예산을 저장한다(같은 달이 있으면 덮어쓰기)."""
        budgets = self.all()
        budgets[month] = amount
        storage.atomic_write_lines(
            self.path,
            (
                _dumps(Budget(month=m, amount=a).to_dict())
                for m, a in sorted(budgets.items())
            ),
        )


class RecurringStore:
    """``recurring.jsonl`` 에 대한 반복 내역 저장소(보너스)."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def list(self) -> list[Recurring]:
        items: list[Recurring] = []
        for line in storage.iter_lines_forward(self.path):
            items.append(Recurring.from_dict(_loads(line)))
        return items

    def next_id(self) -> str:
        max_seq = 0
        for item in self.list():
            if item.id.startswith("RC-"):
                try:
                    max_seq = max(max_seq, int(item.id[3:]))
                except ValueError:
                    continue
        return f"RC-{max_seq + 1:04d}"

    def add(self, rule: Recurring) -> None:
        storage.append_line(self.path, _dumps(rule.to_dict()))
