"""전체 기능을 한 번에 시연하고 evidence 산출물을 생성하는 단일 진입점.

실행:
    python scripts/run_demo.py

동작:
    1. 깨끗한 ``./data`` 폴더에서 10개 기능을 순서대로 실행한다.
    2. 명령/출력/종료 코드를 ``evidence/demo_run.txt`` 에 기록한다.
    3. ``--help``, 저장 파일 내용, 오류 처리, 단위 테스트 결과를 각각
       evidence 파일로 저장한다.

평가자는 코드를 다시 실행하지 않아도 evidence 파일로 동작을 확인할 수 있다.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
EVIDENCE_DIR = REPO_ROOT / "evidence"
SAMPLE_CSV = REPO_ROOT / "samples" / "import_sample.csv"
EXPORT_CSV = EVIDENCE_DIR / "export_2024-01.csv"
# 명령줄 로그를 이식 가능하게 보이도록 REPO_ROOT 기준 상대 경로를 쓴다.
SAMPLE_REL = "samples/import_sample.csv"
EXPORT_REL = "evidence/export_2024-01.csv"

# 자식 프로세스가 OS 기본 인코딩과 무관하게 UTF-8 로 입출력하도록 강제한다.
ENV = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}


def run(args: list[str], stdin: str | None = None) -> tuple[str, int]:
    """budget_app 명령을 실행하고 (출력, 종료코드)를 돌려준다."""
    result = subprocess.run(
        [sys.executable, "-m", "budget_app", *args],
        input=stdin,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=ENV,
        cwd=str(REPO_ROOT),
    )
    output = result.stdout + result.stderr
    return output, result.returncode


def section(buffer: list[str], title: str) -> None:
    buffer.append("")
    buffer.append("=" * 70)
    buffer.append(f"# {title}")
    buffer.append("=" * 70)


def step(buffer: list[str], args: list[str], stdin: str | None = None) -> None:
    """명령 한 건을 실행하고 명령줄/입력/출력/종료코드를 기록한다."""
    cmdline = "$ python -m budget_app " + " ".join(args)
    buffer.append("")
    buffer.append(cmdline)
    if stdin:
        shown = stdin.replace("\n", "\\n")
        buffer.append(f"  (입력: {shown})")
    output, code = run(args, stdin)
    buffer.append(output.rstrip("\n"))
    buffer.append(f"[exit code] {code}")


def write_evidence(name: str, content: str) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / name).write_text(content, encoding="utf-8", newline="\n")
    print(f"  - evidence/{name}")


def main() -> int:
    print("[run_demo] 데이터 초기화")
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    log: list[str] = ["파일 기반 가계부 콘솔 프로그램 - 기능 시연 로그"]

    # 1) 카테고리: 초기 부트스트랩 + 추가
    section(log, "1. category (초기화 + 추가/목록)")
    step(log, ["category", "list"])  # 첫 실행 시 기본 카테고리 자동 생성
    step(log, ["category", "add"], stdin="cafe\n")
    step(log, ["category", "list"])

    # 2) add: 대화형 거래 추가 (2024-01 시나리오)
    section(log, "2. add (대화형 거래 추가)")
    adds = [
        "2024-01-12\nexpense\ntransport\n20000\n버스\n\n",
        "2024-01-14\nincome\nsalary\n3000000\n월급\n\n",
        "2024-01-15\nexpense\nfood\n15000\n점심\nmeal\n",
        "2024-01-18\nexpense\nrent\n150000\n월세\n\n",
        "2024-01-22\nexpense\nfood\n30000\n외식\nmeal\n",
    ]
    for payload in adds:
        step(log, ["add"], stdin=payload)

    # 3) list: 최신순 스트리밍
    section(log, "3. list (최신순, 스트리밍)")
    step(log, ["list", "--limit", "3"])

    # 4) search: 다양한 조건
    section(log, "4. search (조건 검색)")
    step(log, ["search", "--type", "expense", "--category", "food"])
    step(log, ["search", "--from", "2024-01-15", "--to", "2024-01-31"])
    step(log, ["search", "--tag", "meal"])

    # 5) budget + 6) summary
    section(log, "5+6. budget set & summary (예산/요약)")
    step(log, ["budget", "set", "--month", "2024-01", "--amount", "500000"])
    step(log, ["summary", "--month", "2024-01", "--top", "3"])

    # 7) update
    section(log, "7. update (옵션 기반 수정)")
    step(log, ["update", "--id", "TX-000005", "--amount", "28000", "--memo", "외식수정"])
    step(log, ["search", "--category", "food"])

    # 8) delete
    section(log, "8. delete (삭제)")
    step(log, ["delete", "--id", "TX-000001"])
    step(log, ["list", "--limit", "10"])

    # 9) export / import
    section(log, "9. export / import (CSV 입출력)")
    step(log, ["export", "--out", EXPORT_REL, "--month", "2024-01"])
    step(log, ["import", "--from", SAMPLE_REL])
    step(log, ["list", "--limit", "10"])

    # 10) 예산 초과 경고 시연
    section(log, "10. budget 초과 경고 (summary)")
    step(log, ["budget", "set", "--month", "2024-02", "--amount", "10000"])
    step(log, ["add"], stdin="2024-02-03\nexpense\nfood\n25000\n초과지출\n\n")
    step(log, ["summary", "--month", "2024-02", "--top", "3"])

    # 보너스: backup, recurring
    section(log, "보너스. backup / recurring")
    step(log, ["backup"])
    step(log, ["recurring", "add"], stdin="expense\nrent\n800000\n25\n월세\n\n")
    step(log, ["recurring", "apply", "--month", "2024-03"])
    step(log, ["recurring", "apply", "--month", "2024-03"])  # 중복 방지 확인

    write_evidence("demo_run.txt", "\n".join(log) + "\n")

    # --help 모음
    help_log: list[str] = ["명령별 --help 출력"]
    for cmd in (
        [],
        ["add"],
        ["list"],
        ["search"],
        ["summary"],
        ["budget", "set"],
        ["category", "remove"],
        ["update"],
        ["delete"],
        ["import"],
        ["export"],
        ["backup"],
        ["recurring", "apply"],
    ):
        section(help_log, "budget_app " + " ".join(cmd) + " --help")
        output, _ = run([*cmd, "--help"])
        help_log.append(output.rstrip("\n"))
    write_evidence("help.txt", "\n".join(help_log) + "\n")

    # 저장 파일 내용
    files_log: list[str] = ["영구 저장 파일 내용(3개 이상 분리 저장)"]
    for filename in (
        "transactions.jsonl",
        "categories.jsonl",
        "budgets.jsonl",
        "recurring.jsonl",
    ):
        section(files_log, f"data/{filename}")
        path = DATA_DIR / filename
        files_log.append(path.read_text(encoding="utf-8").rstrip("\n") if path.exists() else "(없음)")
    section(files_log, "evidence/export_2024-01.csv")
    files_log.append(EXPORT_CSV.read_text(encoding="utf-8").rstrip("\n") if EXPORT_CSV.exists() else "(없음)")
    write_evidence("data_files.txt", "\n".join(files_log) + "\n")

    # 오류 처리 및 종료 코드
    err_log: list[str] = ["오류 처리 및 종료 코드(원인 + 힌트, exit != 0)"]
    section(err_log, "잘못된 날짜 형식(대화형, 재입력 안내 후 EOF 중단)")
    step(err_log, ["add"], stdin="2024-13-40\n")
    section(err_log, "존재하지 않는 id 삭제")
    step(err_log, ["delete", "--id", "TX-999999"])
    section(err_log, "export 조건 누락")
    step(err_log, ["export", "--out", "evidence/x.csv"])
    section(err_log, "사용 중 카테고리 삭제 차단")
    step(err_log, ["category", "remove", "--name", "transport"])
    section(err_log, "허용되지 않은 타입으로 수정")
    step(err_log, ["update", "--id", "TX-000002", "--type", "spend"])
    write_evidence("errors.txt", "\n".join(err_log) + "\n")

    # 단위 테스트 결과
    test_proc = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=ENV,
        cwd=str(REPO_ROOT),
    )
    write_evidence("tests.txt", test_proc.stdout + test_proc.stderr)

    print("[run_demo] 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main())
