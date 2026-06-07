"""콘솔 출력 포맷터(보너스: 외부 라이브러리 없는 테이블 정렬).

한글은 터미널에서 두 칸 폭을 차지하므로 ``unicodedata`` 로 표시 폭을 계산해
열을 정렬한다. 출력 포맷을 이 모듈로 분리해 서비스/CLI 로직과 떼어 둔다.
"""

from __future__ import annotations

import unicodedata
from typing import Sequence

from .models import Transaction


def display_width(text: str) -> int:
    """터미널 표시 폭을 계산한다(동아시아 전각 문자는 2칸)."""
    width = 0
    for char in text:
        width += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return width


def pad(text: str, width: int) -> str:
    """표시 폭 기준으로 오른쪽에 공백을 채워 열을 맞춘다."""
    gap = width - display_width(text)
    return text + " " * max(gap, 0)


def format_transactions(transactions: Sequence[Transaction]) -> str:
    """거래 목록을 폭 정렬된 표 형태 문자열로 만든다."""
    if not transactions:
        return "(거래 없음)"
    headers = ["id", "date", "type", "category", "amount", "memo", "tags"]
    rows: list[list[str]] = [headers]
    for tx in transactions:
        rows.append(
            [
                tx.id,
                tx.date,
                tx.type,
                tx.category,
                f"{tx.amount:,}",
                tx.memo,
                ",".join(tx.tags),
            ]
        )
    widths = [
        max(display_width(row[col]) for row in rows) for col in range(len(headers))
    ]
    lines = []
    for index, row in enumerate(rows):
        line = " | ".join(pad(cell, widths[col]) for col, cell in enumerate(row))
        lines.append(line.rstrip())
        if index == 0:
            lines.append("-" * display_width(lines[0]))
    return "\n".join(lines)


def format_summary(summary) -> str:  # type: ignore[no-untyped-def]
    """월별 요약(SummaryResult)을 사람이 읽기 좋은 문자열로 만든다."""
    if not summary.has_data and summary.budget is None:
        return f"{summary.month}: 데이터 없음"
    lines = [
        f"[{summary.month} 요약]",
        f"총 수입: {summary.total_income:,}원",
        f"총 지출: {summary.total_expense:,}원",
        f"잔액: {summary.balance:,}원",
    ]
    if summary.budget is not None:
        budget_line = f"예산: {summary.budget:,}원"
        if summary.usage_rate is not None:
            budget_line += f" (사용률 {summary.usage_rate}%)"
        lines.append(budget_line)
        if summary.over_budget:
            over = summary.total_expense - summary.budget
            lines.append(f"[경고] 예산을 {over:,}원 초과했습니다.")
    if summary.top_expenses:
        lines.append("")
        lines.append(f"지출 TOP {len(summary.top_expenses)}")
        for rank, (category, amount) in enumerate(summary.top_expenses, start=1):
            lines.append(f"{rank}) {category} {amount:,}원")
    elif summary.has_data:
        lines.append("")
        lines.append("지출 내역 없음")
    return "\n".join(lines)
