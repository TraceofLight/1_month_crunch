"""공통 관심사(cross-cutting concern)를 분리하는 데코레이터.

명령 처리 함수 본문은 "무엇을 하는가"에만 집중하고, 아래의 부수 관심사는
데코레이터로 빼낸다.

    log_call      : 호출 시작/종료를 로그로 남긴다.
    timed         : 실행 시간을 측정해 로그로 남긴다.
    handle_errors : BudgetAppError 를 잡아 "원인 + 힌트" 로 출력하고 종료
                    코드를 반환한다(스택트레이스 미출력).

세 데코레이터는 독립적이라 자유롭게 조합(stack)할 수 있다. CLI 의 각 명령
핸들러는 ``@handle_errors`` / ``@timed`` / ``@log_call`` 순으로 감싼다.
"""

from __future__ import annotations

import functools
import logging
import sys
import time
from typing import Any, Callable, TypeVar

from .errors import BudgetAppError

logger = logging.getLogger("budget_app")

F = TypeVar("F", bound=Callable[..., Any])


def log_call(func: F) -> F:
    """함수 호출 시작과 종료를 INFO 로그로 남긴다."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        logger.info("호출 시작: %s", func.__name__)
        result = func(*args, **kwargs)
        logger.info("호출 종료: %s", func.__name__)
        return result

    return wrapper  # type: ignore[return-value]


def timed(func: F) -> F:
    """함수 실행 시간을 측정해 밀리초 단위로 로그에 남긴다."""

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.info("실행 시간: %s = %.2f ms", func.__name__, elapsed_ms)

    return wrapper  # type: ignore[return-value]


def handle_errors(func: F) -> F:
    """BudgetAppError 를 잡아 사용자 메시지를 출력하고 종료 코드를 반환한다.

    정상 종료 시 함수 반환값(없으면 0)을, 오류 시 예외의 ``exit_code`` 를
    반환한다. 스택트레이스는 출력하지 않는다.
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> int:
        try:
            result = func(*args, **kwargs)
            return 0 if result is None else int(result)
        except BudgetAppError as exc:
            logger.error("처리 실패: %s - %s", func.__name__, exc.message)
            print(f"[오류] {exc.message}", file=sys.stderr)
            if exc.hint:
                print(f"[힌트] {exc.hint}", file=sys.stderr)
            return exc.exit_code

    return wrapper  # type: ignore[return-value]
