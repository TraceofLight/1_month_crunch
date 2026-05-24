from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # dotenv is convenience-only; missing or failing it should never break the CLI.
    pass

from . import __version__
from .ai_client import (
    AIClientError,
    DEFAULT_MODEL,
    MissingAPIKeyError,
    call_anthropic,
)
from .git_ops import GitError, snapshot
from .prompts import build_commit_prompt, build_pr_prompt
from .render import CallLog, done, error, info, render_commit, render_pr
from .safe_mode import apply_safe_mode
from .validators import parse_commit, parse_pr


def _common_options(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"AI 모델 식별자 (기본: {DEFAULT_MODEL})",
    )
    p.add_argument(
        "--temperature",
        type=float,
        default=0.3,
        help="샘플링 온도 0.0~1.0 (기본: 0.3, 결정적 출력은 낮게)",
    )
    p.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="응답 최대 토큰 (기본: 1024)",
    )
    p.add_argument(
        "--safe-mode",
        action="store_true",
        help="민감정보 마스킹 + diff 분량 제한을 적용한 뒤 프롬프트로 전송",
    )
    p.add_argument(
        "--max-files",
        type=int,
        default=10,
        help="safe-mode 활성 시 전송할 최대 파일 수 (기본: 10, 0=무제한)",
    )
    p.add_argument(
        "--max-lines",
        type=int,
        default=200,
        help="safe-mode 활성 시 전송할 최대 diff 라인 수 (기본: 200, 0=무제한)",
    )
    p.add_argument(
        "--cwd",
        type=Path,
        default=None,
        help="대상 Git 저장소 경로 (기본: 현재 작업 디렉터리)",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="AI API 를 호출하지 않고 구성된 프롬프트만 출력하여 점검",
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-gitgen",
        description="Git 변경 사항을 입력으로 받아 커밋 메시지 / PR 초안을 생성하는 CLI",
    )
    parser.add_argument("--version", action="version", version=f"ai-gitgen {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    commit_p = sub.add_parser("commit", help="현재 변경을 요약한 커밋 메시지 1개 생성")
    _common_options(commit_p)
    commit_p.add_argument(
        "--staged",
        action="store_true",
        help="staging area 의 변경만 사용 (기본: staged + unstaged 모두)",
    )

    pr_p = sub.add_parser("pr", help="현재 브랜치와 base 브랜치 차이로 PR 초안 생성")
    _common_options(pr_p)
    pr_p.add_argument(
        "--base",
        default="main",
        help="비교 기준 base 브랜치 (기본: main)",
    )

    return parser


def _collect_snapshot(args: argparse.Namespace, *, base: str | None):
    info("Git 변경 사항 수집 중...")
    snap = snapshot(
        cwd=args.cwd,
        staged_only=getattr(args, "staged", False),
        base=base,
    )
    info(f"변경 파일 {len(snap.changed_files)}개 / diff {snap.diff.count(chr(10))}줄 감지")
    return snap


def _no_changes_exit() -> int:
    info("변경 사항이 없습니다. 커밋 메시지를 생성하지 않고 종료합니다.")
    return 0


def cmd_commit(args: argparse.Namespace) -> int:
    snap = _collect_snapshot(args, base=None)
    if not snap.has_changes:
        return _no_changes_exit()

    safe_diff, safe_report = apply_safe_mode(
        snap.diff,
        enabled=args.safe_mode,
        max_files=args.max_files,
        max_lines=args.max_lines,
    )
    bundle = build_commit_prompt(snap.status, safe_diff, snap.changed_files)

    if args.dry_run:
        info("--dry-run: AI 호출 없이 프롬프트만 출력합니다.")
        print("=== SYSTEM ===")
        print(bundle.system)
        print("=== USER ===")
        print(bundle.user)
        return 0

    info("AI API 요청 중...")
    ai = call_anthropic(
        bundle.system,
        bundle.user,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )
    done("커밋 메시지 생성 완료")

    draft = parse_commit(ai.text)
    CallLog(command="commit", safe_report=safe_report, ai=ai).emit()
    render_commit(draft)
    return 0


def cmd_pr(args: argparse.Namespace) -> int:
    snap = _collect_snapshot(args, base=args.base)
    info(f"현재 브랜치: {snap.branch}, base: {args.base}")
    if not snap.has_changes:
        info("변경 사항이 없습니다. PR 초안을 생성하지 않고 종료합니다.")
        return 0

    safe_diff, safe_report = apply_safe_mode(
        snap.diff,
        enabled=args.safe_mode,
        max_files=args.max_files,
        max_lines=args.max_lines,
    )
    bundle = build_pr_prompt(snap.branch, args.base, snap.status, safe_diff, snap.changed_files)

    if args.dry_run:
        info("--dry-run: AI 호출 없이 프롬프트만 출력합니다.")
        print("=== SYSTEM ===")
        print(bundle.system)
        print("=== USER ===")
        print(bundle.user)
        return 0

    info("AI API 요청 중...")
    ai = call_anthropic(
        bundle.system,
        bundle.user,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )
    done("PR 초안 생성 완료")

    draft = parse_pr(ai.text)
    CallLog(command="pr", safe_report=safe_report, ai=ai).emit()
    render_pr(draft)
    return 0


_DISPATCH = {
    "commit": cmd_commit,
    "pr": cmd_pr,
}


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    handler = _DISPATCH.get(args.command)
    if handler is None:
        parser.print_help(sys.stderr)
        return 2

    try:
        return handler(args)
    except MissingAPIKeyError as exc:
        error(str(exc))
        return 2
    except AIClientError as exc:
        error(str(exc))
        return 1
    except GitError as exc:
        error(str(exc))
        return 1
    except KeyboardInterrupt:
        error("사용자 인터럽트로 중단되었습니다.")
        return 130
