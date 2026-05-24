from __future__ import annotations

import sys
from dataclasses import dataclass

from .ai_client import AIResponse
from .safe_mode import SafeReport
from .validators import CommitDraft, PRDraft


DIVIDER = "=" * 60
SUB_DIVIDER = "-" * 60


def info(message: str) -> None:
    print(f"[INFO] {message}", file=sys.stderr)


def done(message: str) -> None:
    print(f"[DONE] {message}", file=sys.stderr)


def warn(message: str) -> None:
    print(f"[WARN] {message}", file=sys.stderr)


def error(message: str) -> None:
    print(f"[ERROR] {message}", file=sys.stderr)


@dataclass
class CallLog:
    command: str
    safe_report: SafeReport
    ai: AIResponse
    api_calls: int = 1

    def emit(self) -> None:
        info(f"AI API 호출 횟수: {self.api_calls}회")
        info(
            f"모델={self.ai.model} latency={self.ai.latency_ms}ms "
            f"tokens(in/out)={self.ai.input_tokens}/{self.ai.output_tokens}"
        )
        if self.safe_report.enabled:
            counts = self.safe_report.mask.counts
            info(
                "safe-mode 적용: 파일 "
                f"{self.safe_report.truncate.kept_files}/{self.safe_report.truncate.original_files}, "
                f"라인 {self.safe_report.truncate.kept_lines}/{self.safe_report.truncate.original_lines}, "
                f"마스킹 {self.safe_report.mask.total}건"
                + (f" {counts}" if counts else "")
            )


def render_commit(draft: CommitDraft) -> None:
    print(DIVIDER)
    print("                       Commit Message")
    print(DIVIDER)
    print(draft.render())
    print(DIVIDER)
    for w in draft.warnings:
        warn(w)


def render_pr(draft: PRDraft) -> None:
    print(DIVIDER)
    print("                          PR Title")
    print(DIVIDER)
    print(draft.title)
    print()
    print(DIVIDER)
    print("                          PR Body")
    print(DIVIDER)
    print(draft.body.rstrip())
    print(DIVIDER)
    for w in draft.warnings:
        warn(w)
