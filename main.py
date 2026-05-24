"""ai-gitgen CLI entrypoint.

`python main.py commit` 또는 `python main.py pr` 형태로 실행한다.
모듈 경로는 aigitgen 패키지에서 임포트하며, 이 파일은 얇은 위임자다.
"""
from __future__ import annotations

import sys

# Windows 한글 콘솔(cp949) 환경에서도 출력이 깨지지 않도록 UTF-8 로 재설정.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, OSError):
        pass

from aigitgen.cli import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
