"""Run end-to-end verification for the memo CRUD web application."""

from __future__ import annotations

import html
import os
import signal
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = ROOT_DIR / "database.db"
BASE_URL = "http://127.0.0.1:8000"


def request(path: str, method: str = "GET", data: dict[str, str] | None = None) -> tuple[int, str, str]:
    """Send an HTTP request and return status code, final URL, and response body."""
    encoded_data = None
    headers = {}
    if data is not None:
        encoded_data = urllib.parse.urlencode(data).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"

    req = urllib.request.Request(f"{BASE_URL}{path}", data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status, response.geturl(), response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.geturl(), exc.read().decode("utf-8")


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Disable automatic redirect following so POST responses can be inspected."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        """Return None to expose the redirect response to the caller."""
        return None


def request_without_redirect(path: str, method: str, data: dict[str, str]) -> tuple[int, str]:
    """Send an HTTP request without following redirects and return status and Location."""
    encoded_data = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=encoded_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method=method,
    )
    opener = urllib.request.build_opener(NoRedirectHandler)
    try:
        with opener.open(req, timeout=5) as response:
            return response.status, response.headers.get("Location", "")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.headers.get("Location", "")


def wait_until_ready(process: subprocess.Popen[str]) -> None:
    """Wait until the server accepts HTTP requests or fail with process output."""
    deadline = time.time() + 20
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"서버가 조기 종료되었습니다. 종료 코드: {process.returncode}")
        try:
            status, _, body = request("/")
            if status == 200 and "메모 관리" in body:
                return
        except Exception:
            time.sleep(0.3)
    raise RuntimeError("서버가 제한 시간 안에 준비되지 않았습니다.")


def assert_contains(body: str, expected: str) -> None:
    """Assert that expected text exists in an HTML response."""
    if expected not in body:
        raise AssertionError(f"응답에서 '{expected}'를 찾지 못했습니다.")


def assert_redirected_to(url: str, suffix: str) -> None:
    """Assert that urllib followed a redirect to the expected path."""
    if not url.endswith(suffix):
        raise AssertionError(f"리다이렉트 대상이 예상과 다릅니다. 실제: {url}, 예상 끝부분: {suffix}")


def verify_database(expected_title: str, expected_content: str) -> None:
    """Check persisted memo data directly through SQLite."""
    with sqlite3.connect(DB_PATH) as connection:
        row = connection.execute(
            "SELECT title, content FROM memos WHERE title = ?",
            (expected_title,),
        ).fetchone()
    if row != (expected_title, expected_content):
        raise AssertionError(f"DB 저장 내용이 예상과 다릅니다. 실제: {row}")


def run_checks() -> None:
    """Exercise home, create, read, update, search, delete, validation, and missing-item flows."""
    if DB_PATH.exists():
        DB_PATH.unlink()

    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT_DIR)
    process = subprocess.Popen(
        [sys.executable, "scripts/run.py", "--host", "127.0.0.1", "--port", "8000"],
        cwd=ROOT_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        wait_until_ready(process)

        status, _, home = request("/")
        if status != 200:
            raise AssertionError(f"홈 화면 상태 코드가 200이 아닙니다: {status}")
        assert_contains(home, "메모 관리")
        assert_contains(home, "메모 목록")
        assert_contains(home, "새 메모 작성")

        status, _, new_form = request("/memos/new")
        if status != 200:
            raise AssertionError(f"등록 화면 상태 코드가 200이 아닙니다: {status}")
        assert_contains(new_form, 'name="title"')
        assert_contains(new_form, 'name="content"')

        status, location = request_without_redirect(
            "/memos",
            "POST",
            {"title": "첫 번째 메모", "content": "FastAPI CRUD 흐름 확인", "category": "학습"},
        )
        if status != 303 or not location.endswith("/memos"):
            raise AssertionError(f"등록 후 303 리다이렉트가 아닙니다. 상태: {status}, Location: {location}")
        status, url, create_body = request(urllib.parse.urlparse(location).path)
        if status != 200:
            raise AssertionError(f"등록 후 최종 상태 코드가 200이 아닙니다: {status}")
        assert_redirected_to(url, "/memos")
        assert_contains(create_body, "첫 번째 메모")
        verify_database("첫 번째 메모", "FastAPI CRUD 흐름 확인")

        status, _, list_body = request("/memos")
        if status != 200:
            raise AssertionError(f"목록 화면 상태 코드가 200이 아닙니다: {status}")
        assert_contains(list_body, "첫 번째 메모")
        assert_contains(list_body, "상세")

        status, _, detail_body = request("/memos/1")
        if status != 200:
            raise AssertionError(f"상세 화면 상태 코드가 200이 아닙니다: {status}")
        for expected in ["첫 번째 메모", "FastAPI CRUD 흐름 확인", "학습", "작성일시", "수정일시"]:
            assert_contains(detail_body, expected)

        status, location = request_without_redirect(
            "/memos/1/edit",
            "POST",
            {"title": "수정된 메모", "content": "수정 흐름 확인", "category": "검증"},
        )
        if status != 303 or not location.endswith("/memos/1"):
            raise AssertionError(f"수정 후 303 리다이렉트가 아닙니다. 상태: {status}, Location: {location}")
        status, url, update_body = request(urllib.parse.urlparse(location).path)
        if status != 200:
            raise AssertionError(f"수정 후 최종 상태 코드가 200이 아닙니다: {status}")
        assert_redirected_to(url, "/memos/1")
        assert_contains(update_body, "수정된 메모")
        verify_database("수정된 메모", "수정 흐름 확인")

        status, _, search_body = request("/memos?q=%EC%88%98%EC%A0%95")
        if status != 200:
            raise AssertionError(f"검색 화면 상태 코드가 200이 아닙니다: {status}")
        assert_contains(search_body, "수정된 메모")

        status, _, invalid_body = request(
            "/memos",
            "POST",
            {"title": "", "content": "", "category": ""},
        )
        if status != 400:
            raise AssertionError(f"검증 실패 상태 코드가 400이 아닙니다: {status}")
        assert_contains(invalid_body, "제목은 필수입니다")
        assert_contains(invalid_body, "내용은 필수입니다")

        status, _, missing_body = request("/memos/999")
        if status != 404:
            raise AssertionError(f"없는 메모 상태 코드가 404가 아닙니다: {status}")
        assert_contains(missing_body, "해당 메모를 찾을 수 없습니다")

        status, location = request_without_redirect("/memos/1/delete", "POST", {})
        if status != 303 or not location.endswith("/memos"):
            raise AssertionError(f"삭제 후 303 리다이렉트가 아닙니다. 상태: {status}, Location: {location}")
        status, url, delete_body = request(urllib.parse.urlparse(location).path)
        if status != 200:
            raise AssertionError(f"삭제 후 최종 상태 코드가 200이 아닙니다: {status}")
        assert_redirected_to(url, "/memos")
        if html.escape("수정된 메모") in delete_body or "수정된 메모" in delete_body:
            raise AssertionError("삭제된 메모가 목록에 남아 있습니다.")

        with sqlite3.connect(DB_PATH) as connection:
            count = connection.execute("SELECT COUNT(*) FROM memos").fetchone()[0]
        if count != 0:
            raise AssertionError(f"삭제 후 DB 행 수가 0이 아닙니다: {count}")

        print("검증 성공: 홈, SSR CRUD, PRG, 검색, 검증, 404 안내, SQLite 저장을 모두 확인했습니다.")
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        if process.stdout is not None:
            server_output = process.stdout.read()
            if server_output:
                print("\n서버 로그:")
                print(server_output.strip())


if __name__ == "__main__":
    run_checks()
