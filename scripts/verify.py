"""카페 주문 SQLite 과제 산출물이 요구사항을 만족하는지 검증한다."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SQL_DIR = ROOT / "sql"
EVIDENCE_DIR = ROOT / "evidence"
DB_PATH = EVIDENCE_DIR / "cafe_orders.db"


def _read_sql(path: Path) -> str:
    """SQL 파일을 UTF-8로 읽고 파일이 없으면 명확한 오류를 낸다."""
    if not path.exists():
        raise AssertionError(f"필수 파일이 없습니다: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def _connect_memory() -> sqlite3.Connection:
    """FK 제약조건을 켠 메모리 SQLite 연결을 만든다."""
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _load_database(connection: sqlite3.Connection) -> None:
    """스키마와 샘플 데이터를 검증용 메모리 DB에 적재한다."""
    connection.executescript(_read_sql(SQL_DIR / "schema.sql"))
    connection.executescript(_read_sql(SQL_DIR / "seed.sql"))


def _query_blocks() -> list[str]:
    """queries.sql에서 번호가 붙은 쿼리 블록을 추출한다."""
    sql = _read_sql(SQL_DIR / "queries.sql")
    return re.findall(r"--\s*Q\d{2}\..*?(?=\n--\s*Q\d{2}\.|\Z)", sql, flags=re.S)


def verify_database_shape() -> None:
    """테이블 수, 행 수, PK/FK/UNIQUE 같은 기본 모델 요구사항을 확인한다."""
    with _connect_memory() as connection:
        _load_database(connection)

        tables = ["customer", "staff", "menu_category", "menu_item", "cafe_order", "order_item"]
        for table in tables:
            count = connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            if count < 10:
                raise AssertionError(f"{table} 테이블 행 수가 10개 미만입니다: {count}")

        fk_count = 0
        for table in tables:
            fk_count += len(connection.execute(f"PRAGMA foreign_key_list({table})").fetchall())
        if fk_count < 2:
            raise AssertionError(f"FK가 2개 미만입니다: {fk_count}")

        indexes = connection.execute("PRAGMA index_list(customer)").fetchall()
        if not any(row[2] for row in indexes):
            raise AssertionError("customer 테이블에서 UNIQUE 인덱스를 찾지 못했습니다.")

        try:
            connection.execute(
                """
                INSERT INTO cafe_order
                    (order_id, customer_id, staff_id, ordered_at, order_type, status)
                VALUES
                    (999, 999, 1, '2026-05-15 09:00:00', 'takeout', 'paid')
                """
            )
        except sqlite3.IntegrityError:
            pass
        else:
            raise AssertionError("존재하지 않는 customer_id 참조가 차단되지 않았습니다.")


def verify_queries_file() -> None:
    """핵심 쿼리 15개와 필수 SQL 범주가 queries.sql에 들어 있는지 확인한다."""
    sql = _read_sql(SQL_DIR / "queries.sql")
    blocks = _query_blocks()
    if len(blocks) != 15:
        raise AssertionError(f"쿼리 블록은 15개여야 합니다: {len(blocks)}")

    lowered = " ".join(sql.lower().split())
    required_terms = [
        "where",
        "order by",
        "limit",
        "inner join",
        "left join",
        "group by",
        "count(",
        "sum(",
        "avg(",
        "update",
        "delete",
        "create index",
    ]
    missing = [term for term in required_terms if term not in lowered]
    if missing:
        raise AssertionError(f"필수 SQL 요소가 없습니다: {', '.join(missing)}")

    if not re.search(r"\(\s*select\b", lowered):
        raise AssertionError("서브쿼리를 찾지 못했습니다.")


def verify_evidence() -> None:
    """재현 실행 결과가 evidence 디렉터리에 텍스트로 보존됐는지 확인한다."""
    expected_files = [
        EVIDENCE_DIR / "query_results.txt",
        EVIDENCE_DIR / "sample_row_counts.txt",
        EVIDENCE_DIR / "verification.log",
        EVIDENCE_DIR / "integrity_check.txt",
        DB_PATH,
    ]
    for path in expected_files:
        if not path.exists():
            raise AssertionError(f"증거 파일이 없습니다: {path.relative_to(ROOT)}")

    result_text = (EVIDENCE_DIR / "query_results.txt").read_text(encoding="utf-8")
    for number in range(1, 16):
        marker = f"Q{number:02d}"
        if marker not in result_text:
            raise AssertionError(f"실행 결과에 {marker}가 없습니다.")

    row_count_text = (EVIDENCE_DIR / "sample_row_counts.txt").read_text(encoding="utf-8")
    for table in ["customer", "staff", "menu_category", "menu_item", "cafe_order", "order_item"]:
        if table not in row_count_text:
            raise AssertionError(f"샘플 행 수 증거에 {table}가 없습니다.")


def main() -> None:
    """모든 검증을 실행하고 통과 메시지를 출력한다."""
    verify_database_shape()
    verify_queries_file()
    verify_evidence()
    print("검증 통과: SQLite 스키마, 샘플 데이터, 쿼리, evidence 산출물이 요구사항을 만족합니다.")


if __name__ == "__main__":
    main()
