"""명령행 진입점(argparse 기반).

책임:
    - 서브커맨드 정의와 ``--help`` 제공(모든 옵션은 리눅스 표준 ``--`` 사용).
    - 대화형 입력(add, category add, recurring add)과 옵션 입력 처리.
    - 서비스 호출 결과를 포맷터로 출력.
    - 데코레이터(@handle_errors/@timed/@log_call)로 로그/시간/예외를 분리.
    - 정상 종료 0, 오류 종료 0이 아닌 코드 반환.

업무 로직은 services 계층에, 출력 포맷은 formatting 계층에 위임한다.
"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
import sys
from pathlib import Path
from typing import Callable

from . import formatting
from .decorators import handle_errors, log_call, timed
from .errors import BudgetAppError, ValidationError
from .services import (
    BudgetService,
    SearchFilter,
    parse_tags,
    validate_amount,
    validate_date,
    validate_type,
)

DEFAULT_LIST_LIMIT = 20
DEFAULT_TOP = 3


# --------------------------------------------------------------------------- #
# 입력 헬퍼
# --------------------------------------------------------------------------- #
def _prompt_until(prompt: str, validator: Callable[[str], object]) -> object:
    """유효한 값이 입력될 때까지 재입력을 요구한다(EOF 시 중단 오류)."""
    while True:
        try:
            raw = input(prompt)
        except EOFError as exc:
            raise ValidationError(
                "입력이 중단되었습니다.",
                hint="필수 항목을 모두 입력하세요.",
            ) from exc
        try:
            return validator(raw)
        except ValidationError as exc:
            print(f"[오류] {exc.message}")
            if exc.hint:
                print(f"[힌트] {exc.hint}")


def _input_optional(prompt: str) -> str:
    """선택 입력. EOF 면 빈 문자열로 처리한다."""
    try:
        return input(prompt)
    except EOFError:
        return ""


def _category_validator(service: BudgetService) -> Callable[[str], str]:
    """등록된 카테고리인지 검증하는 검증기를 만든다."""

    def validate(raw: str) -> str:
        name = raw.strip()
        if not service.categories.exists(name):
            raise ValidationError(
                f"등록되지 않은 카테고리입니다: {name}",
                hint="category add 로 먼저 등록하거나 category list 로 확인하세요.",
            )
        return name

    return validate


def _build_service(args: argparse.Namespace) -> BudgetService:
    """서비스를 만들고 저장소를 초기화한다(필요 시 안내 출력)."""
    service = BudgetService(Path(args.data_dir))
    created = service.bootstrap()
    if created:
        print(f"[안내] 저장소를 초기화했습니다. 기본 카테고리: {', '.join(created)}")
    return service


# --------------------------------------------------------------------------- #
# 명령 핸들러 (데코레이터로 로그/시간/예외 분리)
# --------------------------------------------------------------------------- #
@handle_errors
@timed
@log_call
def cmd_add(args: argparse.Namespace) -> int:
    """add: 대화형으로 거래를 입력받아 저장한다."""
    service = _build_service(args)
    date = _prompt_until("날짜(YYYY-MM-DD): ", validate_date)
    tx_type = _prompt_until("타입(income/expense): ", validate_type)
    category = _prompt_until("카테고리: ", _category_validator(service))
    amount = _prompt_until("금액(양수): ", validate_amount)
    memo = _input_optional("메모(선택): ").strip()
    tags = parse_tags(_input_optional("태그(쉼표로 구분, 없으면 엔터): "))
    tx = service.create_transaction(
        date=str(date),
        type=str(tx_type),
        category=str(category),
        amount=int(amount),  # type: ignore[arg-type]
        memo=memo,
        tags=tags,
    )
    print(f"[저장 완료] id={tx.id}")
    return 0


@handle_errors
@timed
@log_call
def cmd_list(args: argparse.Namespace) -> int:
    """list: 최신순으로 거래를 출력한다(스트리밍)."""
    service = _build_service(args)
    transactions = service.list_transactions(limit=args.limit)
    print(formatting.format_transactions(transactions))
    return 0


@handle_errors
@timed
@log_call
def cmd_search(args: argparse.Namespace) -> int:
    """search: 조건에 맞는 거래를 최신순으로 출력한다(스트리밍)."""
    service = _build_service(args)
    criteria = SearchFilter(
        date_from=args.date_from,
        date_to=args.date_to,
        category=args.category,
        type=args.type,
        query=args.q,
        tag=args.tag,
    )
    transactions = service.search(criteria, limit=args.limit)
    print(formatting.format_transactions(transactions))
    return 0


@handle_errors
@timed
@log_call
def cmd_summary(args: argparse.Namespace) -> int:
    """summary: 월별 수입/지출/잔액과 카테고리별 지출 TOP N 을 출력한다."""
    service = _build_service(args)
    summary = service.summarize(month=args.month, top=args.top)
    print(formatting.format_summary(summary))
    return 0


@handle_errors
@timed
@log_call
def cmd_budget_set(args: argparse.Namespace) -> int:
    """budget set: 월 예산을 저장한다."""
    service = _build_service(args)
    month, amount = service.set_budget(month=args.month, amount=args.amount)
    print(f"[저장 완료] {month} 예산 {amount:,}원")
    return 0


@handle_errors
@timed
@log_call
def cmd_category_add(args: argparse.Namespace) -> int:
    """category add: 대화형으로 카테고리를 추가한다."""
    service = _build_service(args)
    name = _input_optional("카테고리명: ").strip()
    if service.add_category(name):
        print(f"[저장 완료] category={name}")
    else:
        print(f"[안내] 이미 존재하는 카테고리입니다: {name}")
    return 0


@handle_errors
@timed
@log_call
def cmd_category_list(args: argparse.Namespace) -> int:
    """category list: 등록된 카테고리를 출력한다."""
    service = _build_service(args)
    names = service.list_categories()
    if not names:
        print("(카테고리 없음)")
    for name in names:
        print(f"- {name}")
    return 0


@handle_errors
@timed
@log_call
def cmd_category_remove(args: argparse.Namespace) -> int:
    """category remove: 카테고리를 삭제한다(사용 중이면 대체 카테고리 필요)."""
    service = _build_service(args)
    moved = service.remove_category(args.name, into=args.into)
    if moved:
        print(f"[삭제 완료] category={args.name} (거래 {moved}건을 '{args.into}'로 이동)")
    else:
        print(f"[삭제 완료] category={args.name}")
    return 0


@handle_errors
@timed
@log_call
def cmd_update(args: argparse.Namespace) -> int:
    """update: 옵션으로 지정한 필드만 수정한다(옵션 기반, 안 A)."""
    service = _build_service(args)
    fields = (args.date, args.type, args.category, args.amount, args.memo, args.tags)
    if all(value is None for value in fields):
        raise ValidationError(
            "수정할 필드를 하나 이상 지정하세요.",
            hint="예: update --id TX-000001 --amount 20000",
        )
    tx = service.update_transaction(
        args.id,
        date=args.date,
        type=args.type,
        category=args.category,
        amount=args.amount,
        memo=args.memo,
        tags=parse_tags(args.tags) if args.tags is not None else None,
    )
    print(f"[수정 완료] id={tx.id}")
    return 0


@handle_errors
@timed
@log_call
def cmd_delete(args: argparse.Namespace) -> int:
    """delete: id 로 거래를 삭제한다."""
    service = _build_service(args)
    tx = service.delete_transaction(args.id)
    print(f"[삭제 완료] id={tx.id}")
    return 0


@handle_errors
@timed
@log_call
def cmd_import(args: argparse.Namespace) -> int:
    """import: CSV 에서 거래를 일괄 등록한다."""
    service = _build_service(args)
    imported, skipped, reasons = service.import_csv(Path(getattr(args, "from")))
    print(f"[완료] imported={imported}, skipped={skipped}")
    for reason in reasons:
        print(f"  - 건너뜀 {reason}")
    return 0


@handle_errors
@timed
@log_call
def cmd_export(args: argparse.Namespace) -> int:
    """export: 조건에 맞는 거래를 CSV 로 내보낸다(month 또는 from/to 필수)."""
    service = _build_service(args)
    if not args.month and not (getattr(args, "from") or args.to):
        raise ValidationError(
            "export 는 --month 또는 --from/--to 조건이 필요합니다.",
            hint="예: export --out out.csv --month 2024-01",
        )
    criteria = SearchFilter(
        month=args.month,
        date_from=getattr(args, "from"),
        date_to=args.to,
    )
    count = service.export_csv(Path(args.out), criteria)
    print(f"[완료] {args.out} ({count} records)")
    return 0


@handle_errors
@timed
@log_call
def cmd_backup(args: argparse.Namespace) -> int:
    """backup: 데이터 파일을 타임스탬프 폴더로 복사한다(보너스)."""
    service = _build_service(args)
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_dir = service.backup(timestamp)
    print(f"[완료] 백업 생성: {backup_dir}")
    return 0


@handle_errors
@timed
@log_call
def cmd_recurring_add(args: argparse.Namespace) -> int:
    """recurring add: 매월 자동 생성할 반복 규칙을 등록한다(보너스)."""
    service = _build_service(args)
    tx_type = _prompt_until("타입(income/expense): ", validate_type)
    category = _prompt_until("카테고리: ", _category_validator(service))
    amount = _prompt_until("금액(양수): ", validate_amount)

    def _day(raw: str) -> int:
        try:
            day = int(raw.strip())
        except ValueError as exc:
            raise ValidationError("일(day)은 정수여야 합니다.", hint="1~28") from exc
        if not 1 <= day <= 28:
            raise ValidationError("일(day)은 1~28 사이여야 합니다.", hint="예: 25")
        return day

    day = _prompt_until("매월 적용 일(1~28): ", _day)
    memo = _input_optional("메모(선택): ").strip()
    tags = parse_tags(_input_optional("태그(쉼표로 구분, 없으면 엔터): "))
    rule = service.add_recurring(
        type=str(tx_type),
        day=int(day),  # type: ignore[arg-type]
        category=str(category),
        amount=int(amount),  # type: ignore[arg-type]
        memo=memo,
        tags=tags,
    )
    print(f"[저장 완료] recurring={rule.id} (매월 {rule.day}일)")
    return 0


@handle_errors
@timed
@log_call
def cmd_recurring_apply(args: argparse.Namespace) -> int:
    """recurring apply: 반복 규칙을 특정 월에 적용한다(중복 방지, 보너스)."""
    service = _build_service(args)
    created, skipped = service.apply_recurring(args.month)
    print(f"[완료] 생성={created}, 건너뜀={skipped}")
    return 0


# --------------------------------------------------------------------------- #
# 파서 구성
# --------------------------------------------------------------------------- #
def build_parser() -> argparse.ArgumentParser:
    """모든 서브커맨드를 포함한 argparse 파서를 만든다."""
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--data-dir",
        default="data",
        help="저장 폴더 경로(기본: ./data)",
    )

    parser = argparse.ArgumentParser(
        prog="budget_app",
        description="파일 기반 가계부 콘솔 프로그램",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")

    # add
    p_add = sub.add_parser("add", parents=[common], help="거래 추가(대화형)")
    p_add.set_defaults(handler=cmd_add)

    # list
    p_list = sub.add_parser("list", parents=[common], help="거래 목록(최신순)")
    p_list.add_argument(
        "--limit", type=int, default=DEFAULT_LIST_LIMIT, help="출력 개수(기본 20)"
    )
    p_list.set_defaults(handler=cmd_list)

    # search
    p_search = sub.add_parser("search", parents=[common], help="거래 검색(최신순)")
    p_search.add_argument("--from", dest="date_from", help="시작일 YYYY-MM-DD")
    p_search.add_argument("--to", dest="date_to", help="종료일 YYYY-MM-DD")
    p_search.add_argument("--category", help="카테고리")
    p_search.add_argument("--type", help="income 또는 expense")
    p_search.add_argument("--q", help="메모 키워드")
    p_search.add_argument("--tag", help="태그")
    p_search.add_argument("--limit", type=int, default=None, help="출력 개수 제한")
    p_search.set_defaults(handler=cmd_search)

    # summary
    p_summary = sub.add_parser("summary", parents=[common], help="월별 요약")
    p_summary.add_argument("--month", required=True, help="대상 월 YYYY-MM")
    p_summary.add_argument("--top", type=int, default=DEFAULT_TOP, help="지출 TOP N")
    p_summary.set_defaults(handler=cmd_summary)

    # budget
    p_budget = sub.add_parser("budget", parents=[common], help="예산 설정/조회")
    budget_sub = p_budget.add_subparsers(dest="action", required=True, metavar="<action>")
    p_budget_set = budget_sub.add_parser("set", parents=[common], help="월 예산 저장")
    p_budget_set.add_argument("--month", required=True, help="대상 월 YYYY-MM")
    p_budget_set.add_argument("--amount", required=True, help="예산 금액(양수)")
    p_budget_set.set_defaults(handler=cmd_budget_set)

    # category
    p_cat = sub.add_parser("category", parents=[common], help="카테고리 관리")
    cat_sub = p_cat.add_subparsers(dest="action", required=True, metavar="<action>")
    p_cat_add = cat_sub.add_parser("add", parents=[common], help="카테고리 추가(대화형)")
    p_cat_add.set_defaults(handler=cmd_category_add)
    p_cat_list = cat_sub.add_parser("list", parents=[common], help="카테고리 목록")
    p_cat_list.set_defaults(handler=cmd_category_list)
    p_cat_remove = cat_sub.add_parser("remove", parents=[common], help="카테고리 삭제")
    p_cat_remove.add_argument("--name", required=True, help="삭제할 카테고리")
    p_cat_remove.add_argument("--into", help="사용 중일 때 거래를 옮길 대체 카테고리")
    p_cat_remove.set_defaults(handler=cmd_category_remove)

    # update (옵션 기반, 안 A)
    p_update = sub.add_parser("update", parents=[common], help="거래 수정(옵션 기반)")
    p_update.add_argument("--id", required=True, help="수정할 거래 id")
    p_update.add_argument("--date", help="YYYY-MM-DD")
    p_update.add_argument("--type", help="income 또는 expense")
    p_update.add_argument("--category", help="카테고리")
    p_update.add_argument("--amount", help="양수 금액")
    p_update.add_argument("--memo", help="메모")
    p_update.add_argument("--tags", help="쉼표로 구분한 태그")
    p_update.set_defaults(handler=cmd_update)

    # delete
    p_delete = sub.add_parser("delete", parents=[common], help="거래 삭제")
    p_delete.add_argument("--id", required=True, help="삭제할 거래 id")
    p_delete.set_defaults(handler=cmd_delete)

    # import
    p_import = sub.add_parser("import", parents=[common], help="CSV 가져오기")
    p_import.add_argument("--from", dest="from", required=True, help="입력 CSV 경로")
    p_import.set_defaults(handler=cmd_import)

    # export
    p_export = sub.add_parser("export", parents=[common], help="CSV 내보내기")
    p_export.add_argument("--out", required=True, help="출력 CSV 경로")
    p_export.add_argument("--month", help="대상 월 YYYY-MM")
    p_export.add_argument("--from", dest="from", help="시작일 YYYY-MM-DD")
    p_export.add_argument("--to", help="종료일 YYYY-MM-DD")
    p_export.set_defaults(handler=cmd_export)

    # backup (보너스)
    p_backup = sub.add_parser("backup", parents=[common], help="데이터 백업(보너스)")
    p_backup.set_defaults(handler=cmd_backup)

    # recurring (보너스)
    p_rec = sub.add_parser("recurring", parents=[common], help="반복 내역(보너스)")
    rec_sub = p_rec.add_subparsers(dest="action", required=True, metavar="<action>")
    p_rec_add = rec_sub.add_parser("add", parents=[common], help="반복 규칙 추가(대화형)")
    p_rec_add.set_defaults(handler=cmd_recurring_add)
    p_rec_apply = rec_sub.add_parser("apply", parents=[common], help="특정 월에 적용")
    p_rec_apply.add_argument("--month", required=True, help="적용할 월 YYYY-MM")
    p_rec_apply.set_defaults(handler=cmd_recurring_apply)

    return parser


def _enable_utf8_io() -> None:
    """리다이렉트/파이프된 표준 입출력을 UTF-8 로 고정한다.

    대화형 콘솔(tty)은 OS 기본 인코딩을 유지하고, 파일/파이프로 연결된
    경우에만 UTF-8 로 맞춰 한글 깨짐을 방지한다(Windows cp949 환경 대비).
    """
    for name in ("stdout", "stderr", "stdin"):
        stream = getattr(sys, name, None)
        if stream is None or not hasattr(stream, "reconfigure"):
            continue
        try:
            if not stream.isatty():
                stream.reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            pass


def _setup_logging(data_dir: Path) -> None:
    """로그를 ``<data_dir>/budget_app.log`` 파일로 남긴다(콘솔은 깨끗하게)."""
    data_dir.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(data_dir / "budget_app.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    app_logger = logging.getLogger("budget_app")
    app_logger.setLevel(logging.INFO)
    _teardown_logging()  # 이전 핸들러를 닫아 파일 잠금/누수를 방지
    app_logger.addHandler(handler)
    app_logger.propagate = False


def _teardown_logging() -> None:
    """로그 핸들러를 닫아 파일 핸들을 해제한다(반복 호출/테스트 대비)."""
    app_logger = logging.getLogger("budget_app")
    for handler in list(app_logger.handlers):
        handler.close()
        app_logger.removeHandler(handler)


def main(argv: list[str] | None = None) -> int:
    """진입점. 정상 0, 오류 시 0이 아닌 종료 코드를 반환한다."""
    _enable_utf8_io()
    parser = build_parser()
    args = parser.parse_args(argv)
    data_dir = Path(getattr(args, "data_dir", "data"))
    _setup_logging(data_dir)
    try:
        return int(args.handler(args))
    except KeyboardInterrupt:
        print("[안내] 작업이 취소되었습니다.", file=sys.stderr)
        return 130
    except BudgetAppError as exc:  # 핸들러가 못 잡은 경우의 안전망
        print(f"[오류] {exc.message}", file=sys.stderr)
        if exc.hint:
            print(f"[힌트] {exc.hint}", file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # 예상치 못한 오류: 스택트레이스 대신 요약 출력
        logging.getLogger("budget_app").exception("예상치 못한 오류")
        print(f"[오류] 예상치 못한 오류가 발생했습니다: {exc}", file=sys.stderr)
        print("[힌트] data 폴더 권한과 저장 파일 상태를 확인하세요.", file=sys.stderr)
        return 1
    finally:
        _teardown_logging()
