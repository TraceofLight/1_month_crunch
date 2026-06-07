"""``python -m budget_app`` 실행 진입점.

CLI 의 ``main`` 을 호출하고 반환된 종료 코드로 프로세스를 종료한다.
"""

from __future__ import annotations

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
