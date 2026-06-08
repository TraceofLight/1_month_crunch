#!/usr/bin/env python3
"""Run the portfolio verification pipeline and save evidence artifacts."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_DIR = ROOT / "evidence"
GITHUB_API = "https://api.github.com/users/TraceofLight/repos"
PAGES_API = "https://api.github.com/repos/TraceofLight/ai-assignment/pages"
PAGES_URL = "https://traceoflight.github.io/ai-assignment/"


def write_text(path: Path, content: str) -> None:
    """Write UTF-8 text, creating parent directories when needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_source(relative_path: str) -> str:
    """Read a repository source file as UTF-8 text."""
    return (ROOT / relative_path).read_text(encoding="utf-8")


def require(condition: bool, message: str, failures: list[str]) -> None:
    """Record a failed verification without stopping the whole run."""
    if not condition:
        failures.append(message)


def verify_static_requirements() -> list[str]:
    """Check the source files for required HTML, CSS, and JavaScript features."""
    failures: list[str] = []
    required_paths = [
        "index.html",
        "css/style.css",
        "js/main.js",
        "images/profile.svg",
        "Dockerfile",
    ]

    for relative_path in required_paths:
        require((ROOT / relative_path).exists(), f"missing file: {relative_path}", failures)

    html = read_source("index.html")
    css = read_source("css/style.css")
    js = read_source("js/main.js")

    for tag in ["header", "nav", "main", "section", "article", "footer"]:
        require(f"<{tag}" in html, f"missing semantic tag: {tag}", failures)

    for section_id in ["hero", "about", "skills", "projects", "contact"]:
        require(f'id="{section_id}"' in html, f"missing section id: {section_id}", failures)
        require(f'href="#{section_id}"' in html, f"missing nav anchor: {section_id}", failures)

    require('alt="노트북 앞에서 웹 페이지를 설계하는 개발자 일러스트"' in html, "missing meaningful image alt", failures)
    require('for="name"' in html and 'id="name"' in html, "name label is not connected", failures)
    require('for="email"' in html and 'id="email"' in html, "email label is not connected", failures)
    require('for="message"' in html and 'id="message"' in html, "message label is not connected", failures)
    require('script src="js/main.js" defer' in html, "JavaScript is not loaded with defer", failures)
    require('link rel="stylesheet" href="css/style.css"' in html, "stylesheet is not linked", failures)

    require(":root" in css, "missing CSS variables", failures)
    require('[data-theme="dark"]' in css, "missing dark theme variables", failures)
    require("display: flex" in css, "missing Flexbox layout", failures)
    require("auto-fit" in css and "minmax(240px, 1fr)" in css, "missing responsive Grid layout", failures)
    require("@media (min-width: 768px)" in css, "missing 768px breakpoint", failures)
    require("@media (min-width: 1024px)" in css, "missing 1024px breakpoint", failures)
    require("box-shadow" in css and "transition" in css, "missing visual effects", failures)

    require("var " not in js, "var keyword is used", failures)
    require("querySelector" in js and "querySelectorAll" in js, "missing DOM selectors", failures)
    require("addEventListener" in js, "missing event listeners", failures)
    require("textContent" in js and "innerHTML" in js, "missing DOM content updates", failures)
    require("classList.add" in js and "classList.remove" in js and "classList.toggle" in js, "missing classList operations", failures)
    require("preventDefault()" in js, "missing preventDefault", failures)
    require("fetch(API_URL)" in js and "async ()" in js, "missing fetch async flow", failures)
    require(".map(" in js and ".filter(" in js and ".forEach(" in js, "missing array methods", failures)
    require("localStorage" in js, "missing localStorage persistence", failures)
    require("IntersectionObserver" in js and "OBSERVER_THRESHOLD = 0.25" in js, "missing observer threshold", failures)

    return failures


def verify_readme_requirements() -> list[str]:
    """Check that README explains the design rationale requested by the assignment."""
    failures: list[str] = []
    readme = read_source("README.md")
    required_explanations = {
        "separated file rationale": "파일을 분리한 이유는 관심사를 나누기 위해서다",
        "event listener rationale": "`onclick`은 동작을 HTML 속성에 직접 섞는다",
        "try catch flow": "`try/catch` 흐름은 네 단계",
        "layout comparison": "Flexbox와 Grid의 차이는 축의 수",
        "state object rationale": "단순 변수 여러 개로 흩어지면",
        "mobile first rationale": "모바일 퍼스트를 선택한 이유는 제약이 큰 화면을 기본값으로 삼기 위해서다",
    }

    for label, phrase in required_explanations.items():
        require(phrase in readme, f"README missing explanation: {label}", failures)

    return failures


def capture_github_api() -> tuple[bool, str]:
    """Call the GitHub API and persist the raw response or error evidence."""
    request = urllib.request.Request(GITHUB_API, headers={"User-Agent": "ai-assignment-verifier"})

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode("utf-8")
            write_text(EVIDENCE_DIR / "github-api-response.json", body)
            repos = json.loads(body)
            return True, f"GitHub API 응답 성공: HTTP {response.status}, 저장소 {len(repos)}개"
    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        write_text(EVIDENCE_DIR / "github-api-error.txt", body)
        return False, f"GitHub API 응답 실패: HTTP {error.code}"
    except urllib.error.URLError as error:
        write_text(EVIDENCE_DIR / "github-api-error.txt", str(error))
        return False, f"GitHub API 연결 실패: {error.reason}"


def capture_pages_status() -> str:
    """Check GitHub Pages configuration and the public URL without failing local verification."""
    lines = ["GitHub Pages 외부 배포 확인"]

    for label, url in [("Pages API", PAGES_API), ("Pages URL", PAGES_URL)]:
        request = urllib.request.Request(url, headers={"User-Agent": "ai-assignment-verifier"})

        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                body = response.read().decode("utf-8", errors="replace")
                contains_current_page = "TraceofLight Portfolio" in body or "Frontend Portfolio" in body
                lines.append(f"{label}: HTTP {response.status}, 현재 페이지 식별자 포함={contains_current_page}")
        except urllib.error.HTTPError as error:
            lines.append(f"{label}: HTTP {error.code}")
        except urllib.error.URLError as error:
            lines.append(f"{label}: 연결 실패 {error.reason}")

    result = "\n".join(lines) + "\n"
    write_text(EVIDENCE_DIR / "pages-check.txt", result)
    return "GitHub Pages 확인 결과 저장: evidence/pages-check.txt"


def capture_screenshot(name: str, width: int, height: int, extra_args: list[str] | None = None) -> tuple[bool, str]:
    """Capture a headless Chromium screenshot for the static portfolio."""
    chromium = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")

    if chromium is None:
        return False, "Chromium 실행 파일을 찾을 수 없어 스크린샷을 건너뜀"

    output = EVIDENCE_DIR / name
    file_url = (ROOT / "index.html").as_uri()
    command = [
        chromium,
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--disable-background-networking",
        "--disable-extensions",
        "--disable-features=Translate",
        "--hide-scrollbars",
        "--no-first-run",
        "--run-all-compositor-stages-before-draw",
        "--virtual-time-budget=5000",
        f"--window-size={width},{height}",
        f"--screenshot={output}",
    ]

    if extra_args:
        command.extend(extra_args)

    command.append(file_url)
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=35,
        )
    except subprocess.TimeoutExpired:
        return False, f"{name} 캡처 실패: Chrome 실행 시간이 35초를 초과함"

    if result.returncode != 0:
        return False, f"{name} 캡처 실패: {result.stderr.strip()}"

    return output.exists() and output.stat().st_size > 0, f"{name} 캡처 완료"


def main() -> int:
    """Execute verification, write logs, and return a process exit code."""
    EVIDENCE_DIR.mkdir(exist_ok=True)
    failures = verify_static_requirements()
    failures.extend(verify_readme_requirements())
    api_ok, api_message = capture_github_api()
    pages_message = capture_pages_status()
    screenshot_results = [
        capture_screenshot("desktop.png", 1440, 1100),
        capture_screenshot("mobile.png", 390, 844),
        capture_screenshot("dark-mode.png", 1440, 1100, ["--force-dark-mode"]),
    ]

    log_lines = [
        f"검증 시각: {datetime.now(timezone.utc).isoformat()}",
        "정적 요구사항 검사: " + ("통과" if not failures else "실패"),
        api_message,
        pages_message,
    ]

    for ok, message in screenshot_results:
        log_lines.append(message)
        if not ok:
            failures.append(message)

    if not api_ok:
        failures.append(api_message)

    if failures:
        log_lines.append("실패 항목:")
        log_lines.extend(f"- {failure}" for failure in failures)
    else:
        log_lines.append("모든 자동 검증 항목 통과")

    write_text(EVIDENCE_DIR / "run-log.txt", "\n".join(log_lines) + "\n")
    print("\n".join(log_lines))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
