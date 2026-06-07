"""애플리케이션 전용 예외 정의.

모든 사용자 대상 오류는 ``BudgetAppError`` 를 상속한다. CLI 계층은 이 예외를
잡아 스택트레이스 대신 "원인 + 해결 힌트" 형태로 출력하고, 0이 아닌 종료 코드를
반환한다. 예상치 못한 일반 예외는 최상위에서 별도로 처리한다.
"""

from __future__ import annotations


class BudgetAppError(Exception):
    """사용자에게 보여줄 원인과 해결 힌트를 갖는 기본 예외.

    Attributes:
        message: 오류의 원인 설명.
        hint: 해결을 위한 힌트(선택).
        exit_code: 프로세스 종료 코드(0이 아니어야 함).
    """

    exit_code: int = 1

    def __init__(self, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.hint = hint


class ValidationError(BudgetAppError):
    """입력 값 검증 실패(날짜 형식, 금액, 타입 등)."""


class NotFoundError(BudgetAppError):
    """존재하지 않는 거래/카테고리 등을 참조했을 때."""


class CategoryInUseError(BudgetAppError):
    """사용 중인 카테고리를 삭제하려 할 때."""


class StorageError(BudgetAppError):
    """파일 입출력 단계에서 발생한 오류."""
