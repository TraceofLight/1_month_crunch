"""도메인 서비스 계층.

CLI(입출력)와 저장소(파일 I/O) 사이에서 검증과 집계 등 업무 규칙을 담당한다.
모든 입력 검증은 여기에서 ``ValidationError`` 등으로 일원화하며, CLI 는 결과만
출력한다. 함수 시그니처의 타입 힌트로 입출력 계약을 명확히 한다.
"""

from __future__ import annotations

import csv
import datetime as dt
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

from .errors import (
    CategoryInUseError,
    NotFoundError,
    ValidationError,
)
from .models import VALID_TYPES, Recurring, Transaction
from .repository import (
    BudgetStore,
    CategoryStore,
    RecurringStore,
    TransactionRepository,
)

CSV_COLUMNS: tuple[str, ...] = ("date", "type", "category", "amount", "memo", "tags")


# --------------------------------------------------------------------------- #
# 입력 검증 헬퍼 (순수 함수)
# --------------------------------------------------------------------------- #
def validate_date(value: str) -> str:
    """``YYYY-MM-DD`` 형식인지 검증하고 정규화한 문자열을 반환한다."""
    text = value.strip()
    try:
        parsed = dt.datetime.strptime(text, "%Y-%m-%d")
    except ValueError as exc:
        raise ValidationError(
            "날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).",
            hint="예: 2024-01-15",
        ) from exc
    return parsed.strftime("%Y-%m-%d")


def validate_month(value: str) -> str:
    """``YYYY-MM`` 형식인지 검증하고 정규화한 문자열을 반환한다."""
    text = value.strip()
    try:
        parsed = dt.datetime.strptime(text, "%Y-%m")
    except ValueError as exc:
        raise ValidationError(
            "월 형식이 올바르지 않습니다 (YYYY-MM).",
            hint="예: 2024-01",
        ) from exc
    return parsed.strftime("%Y-%m")


def validate_type(value: str) -> str:
    """타입이 ``income``/``expense`` 인지 검증한다."""
    text = value.strip().lower()
    if text not in VALID_TYPES:
        raise ValidationError(
            f"타입은 {' 또는 '.join(VALID_TYPES)} 만 가능합니다.",
            hint="예: expense",
        )
    return text


def validate_amount(value: str | int) -> int:
    """금액이 양의 정수인지 검증한다."""
    try:
        amount = int(str(value).strip())
    except ValueError as exc:
        raise ValidationError(
            "금액은 정수여야 합니다.",
            hint="예: 15000",
        ) from exc
    if amount <= 0:
        raise ValidationError(
            "금액은 0보다 큰 양수여야 합니다.",
            hint="0 또는 음수는 입력할 수 없습니다.",
        )
    return amount


def parse_tags(value: str) -> list[str]:
    """쉼표로 구분된 태그 문자열을 리스트로 변환한다(공백 제거)."""
    return [tag.strip() for tag in value.split(",") if tag.strip()]


@dataclass
class SearchFilter:
    """검색 조건 묶음. None 인 항목은 조건에서 제외된다."""

    date_from: str | None = None
    date_to: str | None = None
    category: str | None = None
    type: str | None = None
    query: str | None = None
    tag: str | None = None
    month: str | None = None  # export 의 --month 편의 조건(YYYY-MM 접두 일치)

    def matches(self, tx: Transaction) -> bool:
        if self.month and not tx.date.startswith(self.month):
            return False
        if self.date_from and tx.date < self.date_from:
            return False
        if self.date_to and tx.date > self.date_to:
            return False
        if self.category and tx.category != self.category:
            return False
        if self.type and tx.type != self.type:
            return False
        if self.query and self.query.lower() not in tx.memo.lower():
            return False
        if self.tag and self.tag not in tx.tags:
            return False
        return True


@dataclass
class SummaryResult:
    """월별 요약 결과."""

    month: str
    total_income: int
    total_expense: int
    balance: int
    top_expenses: list[tuple[str, int]]
    budget: int | None
    usage_rate: float | None
    over_budget: bool
    has_data: bool


class BudgetService:
    """가계부의 모든 업무 로직을 제공하는 진입 서비스.

    저장소 4종을 조합해 거래 CRUD, 검색, 요약, 예산, 카테고리, 가져오기/
    내보내기, 백업, 반복 내역을 처리한다.
    """

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.transactions = TransactionRepository(data_dir / "transactions.jsonl")
        self.categories = CategoryStore(data_dir / "categories.jsonl")
        self.budgets = BudgetStore(data_dir / "budgets.jsonl")
        self.recurring = RecurringStore(data_dir / "recurring.jsonl")

    # ----------------------------- 초기화 ------------------------------ #
    def bootstrap(self) -> list[str]:
        """저장 폴더/파일을 준비하고 기본 카테고리를 생성한다.

        Returns:
            새로 생성된 기본 카테고리 목록(없으면 빈 리스트).
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)
        return self.categories.ensure_defaults()

    # --------------------------- 거래 추가 ----------------------------- #
    def create_transaction(
        self,
        *,
        date: str,
        type: str,
        category: str,
        amount: int | str,
        memo: str = "",
        tags: Iterable[str] | None = None,
    ) -> Transaction:
        """검증 후 거래를 저장하고 생성된 ``Transaction`` 을 반환한다."""
        clean_date = validate_date(date)
        clean_type = validate_type(type)
        clean_amount = validate_amount(amount)
        self._require_category(category)
        tx = Transaction(
            id=self.transactions.next_id(),
            type=clean_type,
            date=clean_date,
            amount=clean_amount,
            category=category,
            memo=memo.strip(),
            tags=list(tags or []),
        )
        self.transactions.add(tx)
        return tx

    # --------------------------- 목록/검색 ----------------------------- #
    def list_transactions(self, limit: int) -> list[Transaction]:
        """최신순으로 최대 ``limit`` 건을 반환한다(스트리밍, 조기 종료)."""
        if limit <= 0:
            raise ValidationError(
                "limit 은 1 이상이어야 합니다.", hint="예: --limit 10"
            )
        return list(_take(self.transactions.iter_recent(), limit))

    def search(
        self, criteria: SearchFilter, limit: int | None = None
    ) -> list[Transaction]:
        """조건에 맞는 거래를 최신순으로 반환한다(스트리밍)."""
        if criteria.date_from:
            criteria.date_from = validate_date(criteria.date_from)
        if criteria.date_to:
            criteria.date_to = validate_date(criteria.date_to)
        if criteria.type:
            criteria.type = validate_type(criteria.type)
        if criteria.month:
            criteria.month = validate_month(criteria.month)
        matched = (tx for tx in self.transactions.iter_recent() if criteria.matches(tx))
        if limit is not None:
            matched = _take(matched, limit)
        return list(matched)

    # --------------------------- 수정/삭제 ----------------------------- #
    def update_transaction(
        self,
        tx_id: str,
        *,
        date: str | None = None,
        type: str | None = None,
        category: str | None = None,
        amount: int | str | None = None,
        memo: str | None = None,
        tags: Iterable[str] | None = None,
    ) -> Transaction:
        """ID 기반으로 지정한 필드만 수정한다(원자적 재작성)."""
        records = list(self.transactions.iter_all())
        target: Transaction | None = None
        for tx in records:
            if tx.id == tx_id:
                target = tx
                break
        if target is None:
            raise NotFoundError(
                f"거래를 찾을 수 없습니다: {tx_id}",
                hint="list 명령으로 존재하는 id 를 확인하세요.",
            )
        if date is not None:
            target.date = validate_date(date)
        if type is not None:
            target.type = validate_type(type)
        if amount is not None:
            target.amount = validate_amount(amount)
        if category is not None:
            self._require_category(category)
            target.category = category
        if memo is not None:
            target.memo = memo.strip()
        if tags is not None:
            target.tags = list(tags)
        self.transactions.replace_all(records)
        return target

    def delete_transaction(self, tx_id: str) -> Transaction:
        """ID 로 거래를 삭제한다(없으면 NotFoundError)."""
        records = list(self.transactions.iter_all())
        kept = [tx for tx in records if tx.id != tx_id]
        if len(kept) == len(records):
            raise NotFoundError(
                f"거래를 찾을 수 없습니다: {tx_id}",
                hint="list 명령으로 존재하는 id 를 확인하세요.",
            )
        removed = next(tx for tx in records if tx.id == tx_id)
        self.transactions.replace_all(kept)
        return removed

    # ----------------------------- 요약 -------------------------------- #
    def summarize(self, month: str, top: int) -> SummaryResult:
        """해당 월의 수입/지출/잔액과 카테고리별 지출 TOP N 을 계산한다."""
        clean_month = validate_month(month)
        if top <= 0:
            raise ValidationError("top 은 1 이상이어야 합니다.", hint="예: --top 3")
        total_income = 0
        total_expense = 0
        per_category: dict[str, int] = {}
        has_data = False
        for tx in self.transactions.iter_all():  # 스트리밍 누적
            if not tx.date.startswith(clean_month):
                continue
            has_data = True
            if tx.type == "income":
                total_income += tx.amount
            else:
                total_expense += tx.amount
                per_category[tx.category] = per_category.get(tx.category, 0) + tx.amount
        top_expenses = sorted(
            per_category.items(), key=lambda item: item[1], reverse=True
        )[:top]
        budget = self.budgets.get(clean_month)
        usage_rate: float | None = None
        over_budget = False
        if budget is not None and budget > 0:
            usage_rate = round(total_expense / budget * 100, 1)
            over_budget = total_expense > budget
        return SummaryResult(
            month=clean_month,
            total_income=total_income,
            total_expense=total_expense,
            balance=total_income - total_expense,
            top_expenses=top_expenses,
            budget=budget,
            usage_rate=usage_rate,
            over_budget=over_budget,
            has_data=has_data,
        )

    # ----------------------------- 예산 -------------------------------- #
    def set_budget(self, month: str, amount: int | str) -> tuple[str, int]:
        """월 예산을 저장한다."""
        clean_month = validate_month(month)
        clean_amount = validate_amount(amount)
        self.budgets.set(clean_month, clean_amount)
        return clean_month, clean_amount

    # --------------------------- 카테고리 ------------------------------ #
    def add_category(self, name: str) -> bool:
        clean = name.strip()
        if not clean:
            raise ValidationError(
                "카테고리 이름이 비어 있습니다.", hint="예: food"
            )
        return self.categories.add(clean)

    def list_categories(self) -> list[str]:
        return self.categories.list()

    def remove_category(self, name: str, into: str | None = None) -> int:
        """카테고리를 삭제한다.

        사용 중이면 삭제를 막고, ``into`` 로 대체 카테고리를 주면 사용 중인
        거래를 모두 대체 카테고리로 옮긴 뒤 삭제한다.

        Returns:
            대체된 거래 건수(into 미사용 시 0).
        """
        clean = name.strip()
        if not self.categories.exists(clean):
            raise NotFoundError(
                f"카테고리를 찾을 수 없습니다: {clean}",
                hint="category list 로 존재하는 카테고리를 확인하세요.",
            )
        in_use = [tx for tx in self.transactions.iter_all() if tx.category == clean]
        moved = 0
        if in_use:
            if into is None:
                raise CategoryInUseError(
                    f"'{clean}' 카테고리를 사용하는 거래가 {len(in_use)}건 있습니다.",
                    hint="--into <대체카테고리> 로 거래를 옮긴 뒤 삭제하세요.",
                )
            into_clean = into.strip()
            if not self.categories.exists(into_clean):
                raise NotFoundError(
                    f"대체 카테고리를 찾을 수 없습니다: {into_clean}",
                    hint="먼저 category add 로 대체 카테고리를 등록하세요.",
                )
            records = list(self.transactions.iter_all())
            for tx in records:
                if tx.category == clean:
                    tx.category = into_clean
                    moved += 1
            self.transactions.replace_all(records)
        self.categories.remove(clean)
        return moved

    # -------------------------- 가져오기/내보내기 ----------------------- #
    def export_csv(self, out_path: Path, criteria: SearchFilter) -> int:
        """조건에 맞는 거래를 CSV 로 저장하고 건수를 반환한다."""
        rows = self.search(criteria)  # 최신순
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(CSV_COLUMNS)
            for tx in rows:
                writer.writerow(
                    [
                        tx.date,
                        tx.type,
                        tx.category,
                        tx.amount,
                        tx.memo,
                        ",".join(tx.tags),
                    ]
                )
        return len(rows)

    def import_csv(self, in_path: Path) -> tuple[int, int, list[str]]:
        """CSV 에서 거래를 일괄 등록한다.

        Returns:
            (imported, skipped, reasons) 튜플. reasons 는 건너뛴 행의 사유.
        """
        if not in_path.exists():
            raise NotFoundError(
                f"가져올 CSV 파일이 없습니다: {in_path}",
                hint="--from 경로를 확인하세요.",
            )
        imported = 0
        skipped = 0
        reasons: list[str] = []
        with in_path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            missing = [c for c in ("date", "type", "category", "amount") if c not in (reader.fieldnames or [])]
            if missing:
                raise ValidationError(
                    f"CSV 필수 열이 없습니다: {', '.join(missing)}",
                    hint="헤더는 date,type,category,amount,memo,tags 여야 합니다.",
                )
            for line_no, row in enumerate(reader, start=2):
                try:
                    tx = self.create_transaction(
                        date=row["date"],
                        type=row["type"],
                        category=row["category"],
                        amount=row["amount"],
                        memo=row.get("memo", "") or "",
                        tags=parse_tags(row.get("tags", "") or ""),
                    )
                    imported += 1
                    _ = tx
                except (ValidationError, NotFoundError) as exc:
                    skipped += 1
                    reasons.append(f"{line_no}행: {exc.message}")
        return imported, skipped, reasons

    # ----------------------------- 백업 -------------------------------- #
    def backup(self, timestamp: str) -> Path:
        """현재 데이터 파일들을 타임스탬프 폴더로 복사한다(보너스).

        Args:
            timestamp: 백업 폴더 이름에 쓸 타임스탬프 문자열.
        """
        backup_dir = self.data_dir / "backups" / f"backup-{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        for store_path in (
            self.transactions.path,
            self.categories.path,
            self.budgets.path,
            self.recurring.path,
        ):
            if store_path.exists():
                shutil.copy2(store_path, backup_dir / store_path.name)
        return backup_dir

    # --------------------------- 반복 내역 ----------------------------- #
    def add_recurring(
        self,
        *,
        type: str,
        day: int | str,
        category: str,
        amount: int | str,
        memo: str = "",
        tags: Iterable[str] | None = None,
    ) -> Recurring:
        """매월 자동 생성할 반복 규칙을 등록한다(보너스)."""
        clean_type = validate_type(type)
        clean_amount = validate_amount(amount)
        self._require_category(category)
        try:
            clean_day = int(str(day).strip())
        except ValueError as exc:
            raise ValidationError("일(day)은 정수여야 합니다.", hint="1~28") from exc
        if not 1 <= clean_day <= 28:
            raise ValidationError(
                "일(day)은 1~28 사이여야 합니다.",
                hint="모든 달에 존재하는 날짜만 허용합니다.",
            )
        rule = Recurring(
            id=self.recurring.next_id(),
            type=clean_type,
            day=clean_day,
            amount=clean_amount,
            category=category,
            memo=memo.strip(),
            tags=list(tags or []),
        )
        self.recurring.add(rule)
        return rule

    def apply_recurring(self, month: str) -> tuple[int, int]:
        """반복 규칙을 특정 월에 적용해 거래를 생성한다(중복 방지).

        같은 규칙이 같은 달에 이미 적용되었으면 ``recurring:<id>`` 태그로
        식별해 건너뛴다.

        Returns:
            (생성, 건너뜀) 튜플.
        """
        clean_month = validate_month(month)
        rules = self.recurring.list()
        if not rules:
            return 0, 0
        already = {
            tag
            for tx in self.transactions.iter_all()
            if tx.date.startswith(clean_month)
            for tag in tx.tags
            if tag.startswith("recurring:")
        }
        created = 0
        skipped = 0
        for rule in rules:
            marker = f"recurring:{rule.id}"
            if marker in already:
                skipped += 1
                continue
            self.create_transaction(
                date=f"{clean_month}-{rule.day:02d}",
                type=rule.type,
                category=rule.category,
                amount=rule.amount,
                memo=rule.memo,
                tags=[*rule.tags, marker],
            )
            created += 1
        return created, skipped

    # ----------------------------- 내부 -------------------------------- #
    def _require_category(self, name: str) -> None:
        if not self.categories.exists(name):
            raise NotFoundError(
                f"등록되지 않은 카테고리입니다: {name}",
                hint="category add 로 먼저 등록하거나 category list 로 확인하세요.",
            )


def _take(iterator: Iterator[Transaction], limit: int) -> Iterator[Transaction]:
    """제너레이터에서 앞쪽 ``limit`` 개만 취한다(조기 종료로 스트리밍 유지)."""
    for index, item in enumerate(iterator):
        if index >= limit:
            return
        yield item
