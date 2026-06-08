"""Run an end-to-end verification flow against the FastAPI service."""

from __future__ import annotations

import http.cookiejar
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


BASE_URL = "http://127.0.0.1:8000"
ROOT_DIR = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT_DIR / "evidence"
LOG_PATH = EVIDENCE_DIR / "verification.log"


class HttpClient:
    """Small cookie-aware HTTP client for verification without external test tools."""

    def __init__(self) -> None:
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar),
            urllib.request.HTTPRedirectHandler(),
        )

    def get(self, path: str) -> tuple[int, str]:
        return self._request("GET", path)

    def post(self, path: str, data: dict[str, str]) -> tuple[int, str]:
        encoded = urllib.parse.urlencode(data).encode()
        return self._request("POST", path, encoded)

    def _request(self, method: str, path: str, data: bytes | None = None) -> tuple[int, str]:
        request = urllib.request.Request(f"{BASE_URL}{path}", data=data, method=method)
        try:
            with self.opener.open(request, timeout=10) as response:
                return response.status, response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read().decode("utf-8")


def wait_for_server(process: subprocess.Popen[str]) -> None:
    """Wait until the server accepts HTTP requests or fail with process output."""

    deadline = time.time() + 20
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError("서버 프로세스가 시작 중 종료되었습니다.")
        try:
            with urllib.request.urlopen(f"{BASE_URL}/", timeout=1):
                return
        except OSError:
            time.sleep(0.25)
    raise RuntimeError("서버가 제한 시간 안에 시작되지 않았습니다.")


def assert_contains(body: str, expected: str, label: str) -> None:
    """Assert that a response body contains the expected text."""

    if expected not in body:
        raise AssertionError(f"{label}: '{expected}' 문구를 찾지 못했습니다.")


def main() -> int:
    """Execute the full login-to-state-change verification scenario."""

    EVIDENCE_DIR.mkdir(exist_ok=True)
    db_path = ROOT_DIR / "verification.db"
    if db_path.exists():
        db_path.unlink()

    env = os.environ.copy()
    env["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    env["SESSION_SECRET"] = "verification-secret"

    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=ROOT_DIR,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    results: list[str] = []
    try:
        wait_for_server(process)
        client = HttpClient()

        status, body = client.get("/app")
        results.append(f"비로그인 /app 접근 상태: {status}")
        assert_contains(body, "로그인이 필요합니다", "비로그인 접근 차단")

        status, body = client.post("/login", {"username": "demo", "password": "wrong"})
        results.append(f"잘못된 로그인 상태: {status}")
        assert_contains(body, "아이디 또는 비밀번호가 올바르지 않습니다", "로그인 실패 안내")

        status, body = client.post("/login", {"username": "demo", "password": "demo1234"})
        results.append(f"정상 로그인 후 상태: {status}")
        assert_contains(body, "demo님 환영합니다", "로그인 UI")

        status, body = client.post("/app/projects", {"name": "검증 프로젝트", "description": "요구사항 확인"})
        results.append(f"프로젝트 생성 상태: {status}")
        assert_contains(body, "검증 프로젝트", "프로젝트 생성 결과")

        status, body = client.post("/app/tasks", {"project_id": "1", "title": "상태 변경 확인"})
        results.append(f"작업 생성 상태: {status}")
        assert_contains(body, "진행 전", "작업 초기 상태")

        status, body = client.post("/app/tasks/1/complete", {})
        results.append(f"작업 완료 상태 변경 상태: {status}")
        assert_contains(body, "완료", "작업 완료 상태")
        assert_contains(body, "진행 전 → 완료", "상태 변경 전후 안내")

        LOG_PATH.write_text("\n".join(results) + "\n", encoding="utf-8")
        return 0
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
