"""카페 주문 SQLite 과제 파이프라인을 한 번에 실행한다."""

from __future__ import annotations

import io
import sqlite3
from contextlib import redirect_stdout
from pathlib import Path

import verify


ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"
EVIDENCE_DIR = ROOT / "evidence"
DB_PATH = EVIDENCE_DIR / "cafe_orders.db"


def _read_sql(path: Path) -> str:
    """SQL 파일을 UTF-8로 읽는다."""
    return path.read_text(encoding="utf-8")


def _open_database() -> sqlite3.Connection:
    """기존 결과 DB를 지우고 FK 제약조건이 켜진 SQLite 연결을 반환한다."""
    EVIDENCE_DIR.mkdir(exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _query_blocks(sql: str) -> list[str]:
    """queries.sql을 Q 번호 단위 블록으로 나눈다."""
    blocks: list[str] = []
    current: list[str] = []
    for line in sql.splitlines():
        if line.startswith("-- Q") and current:
            blocks.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        blocks.append("\n".join(current).strip())
    return [block for block in blocks if block.startswith("-- Q")]


def _split_statements(block: str) -> list[str]:
    """SQLite가 실행할 수 있는 완성된 SQL 문장 단위로 블록을 나눈다."""
    statements: list[str] = []
    buffer: list[str] = []
    for line in block.splitlines():
        buffer.append(line)
        candidate = "\n".join(buffer).strip()
        if sqlite3.complete_statement(candidate):
            statements.append(candidate)
            buffer = []
    if buffer:
        trailing = "\n".join(buffer).strip()
        if trailing:
            statements.append(trailing)
    return statements


def _statement_body(statement: str) -> str:
    """주석을 제외한 SQL 본문을 반환한다."""
    lines = []
    for line in statement.splitlines():
        stripped = line.strip()
        if stripped.startswith("--") or not stripped:
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _description(block: str) -> str:
    """쿼리 블록의 첫 설명 주석을 읽는다."""
    first_line = block.splitlines()[0]
    return first_line.removeprefix("-- ").strip()


def _format_rows(cursor: sqlite3.Cursor) -> str:
    """SELECT 결과를 텍스트 표 형태로 변환한다."""
    rows = cursor.fetchall()
    if cursor.description is None:
        return "결과 행 없음"

    columns = [description[0] for description in cursor.description]
    output = [" | ".join(columns), " | ".join("---" for _ in columns)]
    for row in rows:
        output.append(" | ".join(str(row[column]) for column in columns))
    if not rows:
        output.append("(행 없음)")
    return "\n".join(output)


def _execute_query_blocks(connection: sqlite3.Connection) -> str:
    """핵심 쿼리 15개를 실행하고 결과 텍스트를 반환한다."""
    blocks = _query_blocks(_read_sql(SQL_DIR / "queries.sql"))
    output: list[str] = []

    for index, block in enumerate(blocks, start=1):
        output.append(f"## Q{index:02d}")
        output.append(_description(block))
        for statement in _split_statements(block):
            body = _statement_body(statement)
            if not body:
                continue
            cursor = connection.execute(body)
            first_keyword = body.split(None, 1)[0].upper()
            if first_keyword in {"SELECT", "EXPLAIN"}:
                output.append(_format_rows(cursor))
            elif first_keyword in {"UPDATE", "DELETE"}:
                output.append(f"{first_keyword} 적용 행 수: {cursor.rowcount}")
            else:
                output.append(f"{first_keyword} 실행 완료")
        connection.commit()
        output.append("")

    return "\n".join(output).strip() + "\n"


def _write_integrity_check(connection: sqlite3.Connection) -> None:
    """일부러 FK 오류를 내고 차단 결과를 evidence에 저장한다."""
    lines = [
        "없는 customer_id를 참조하는 주문 입력을 시도했다.",
        "실행 SQL:",
        "INSERT INTO cafe_order (order_id, customer_id, staff_id, ordered_at, order_type, status)",
        "VALUES (999, 999, 1, '2026-05-15 09:00:00', 'takeout', 'paid');",
    ]
    try:
        connection.execute(
            """
            INSERT INTO cafe_order
                (order_id, customer_id, staff_id, ordered_at, order_type, status)
            VALUES
                (999, 999, 1, '2026-05-15 09:00:00', 'takeout', 'paid')
            """
        )
    except sqlite3.IntegrityError as error:
        lines.append(f"결과: FK 제약조건으로 차단됨 ({error})")
    else:
        lines.append("결과: 오류 없이 입력됨")
        raise AssertionError("FK 제약조건 검증 입력이 차단되지 않았습니다.")

    (EVIDENCE_DIR / "integrity_check.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    """전체 파이프라인을 실행하고 evidence 파일을 저장한다."""
    with _open_database() as connection:
        connection.executescript(_read_sql(SQL_DIR / "schema.sql"))
        connection.executescript(_read_sql(SQL_DIR / "seed.sql"))
        query_results = _execute_query_blocks(connection)
        (EVIDENCE_DIR / "query_results.txt").write_text(query_results, encoding="utf-8")
        _write_integrity_check(connection)

    (EVIDENCE_DIR / "verification.log").write_text("검증 실행 전 로그 생성\n", encoding="utf-8")
    verification_buffer = io.StringIO()
    with redirect_stdout(verification_buffer):
        verify.main()

    verification_text = (
        "파이프라인 실행 완료\n"
        f"DB 파일: {DB_PATH.relative_to(ROOT)}\n"
        "검증 결과:\n"
        f"{verification_buffer.getvalue()}"
    )
    (EVIDENCE_DIR / "verification.log").write_text(verification_text, encoding="utf-8")
    print(verification_text, end="")


if __name__ == "__main__":
    main()
