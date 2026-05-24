from __future__ import annotations

import re
from dataclasses import dataclass


# Patterns ordered by specificity. Each entry: (label, compiled regex, masker).
# The masker receives a re.Match and returns the replacement string so we can
# keep partial context (e.g. token prefix) while hiding the secret material.
_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    # Provider-prefixed API keys: sk-XXXX, sk-ant-XXXX, gh[opsu]_XXXX, AKIA..., xox[abp]-...
    ("api_key_prefixed", re.compile(
        r"\b(sk-(?:ant-)?[A-Za-z0-9_\-]{20,}"
        r"|gh[opsu]_[A-Za-z0-9]{20,}"
        r"|AKIA[0-9A-Z]{12,}"
        r"|xox[abprs]-[A-Za-z0-9-]{10,})\b"
    )),
    # Bearer / Token assignments in headers or config
    ("bearer", re.compile(r"(?i)(authorization\s*[:=]\s*bearer\s+)([A-Za-z0-9._\-]+)")),
    # Generic key=value where key looks sensitive
    ("kv_secret", re.compile(
        r"(?i)\b(api[_-]?key|secret(?:_key)?|access[_-]?token|password|passwd|private[_-]?key)"
        r"\s*[:=]\s*[\"']?([^\s\"',]{6,})[\"']?"
    )),
    # JWT-like tokens (three base64url segments)
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\b")),
    # Email addresses
    ("email", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")),
    # PEM private key block (collapse the whole thing)
    ("pem", re.compile(
        r"-----BEGIN[^-]+PRIVATE KEY-----[\s\S]+?-----END[^-]+PRIVATE KEY-----"
    )),
]


@dataclass
class MaskStats:
    counts: dict[str, int]

    @property
    def total(self) -> int:
        return sum(self.counts.values())


def _mask_token(token: str) -> str:
    if len(token) <= 6:
        return "***"
    return f"{token[:3]}***{token[-2:]}"


def mask_text(text: str) -> tuple[str, MaskStats]:
    counts: dict[str, int] = {}
    result = text

    for label, pattern in _PATTERNS:
        def _replace(m: re.Match[str], _label: str = label) -> str:
            counts[_label] = counts.get(_label, 0) + 1
            if _label == "bearer":
                return f"{m.group(1)}***MASKED***"
            if _label == "kv_secret":
                return f"{m.group(1)}=***MASKED***"
            if _label == "pem":
                return "-----BEGIN PRIVATE KEY-----\n***MASKED***\n-----END PRIVATE KEY-----"
            if _label == "email":
                full = m.group(0)
                local, _, domain = full.partition("@")
                redacted_local = local[0] + "***" if local else "***"
                return f"{redacted_local}@{domain}"
            return _mask_token(m.group(0))

        result = pattern.sub(_replace, result)

    return result, MaskStats(counts=counts)


@dataclass
class TruncateStats:
    original_files: int
    kept_files: int
    original_lines: int
    kept_lines: int

    @property
    def truncated(self) -> bool:
        return self.kept_files < self.original_files or self.kept_lines < self.original_lines


def _split_into_file_chunks(diff: str) -> list[str]:
    """Split a unified diff into per-file chunks. Each chunk starts with `diff --git`."""
    if not diff.strip():
        return []
    chunks: list[str] = []
    current: list[str] = []
    for line in diff.splitlines(keepends=True):
        if line.startswith("diff --git ") and current:
            chunks.append("".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        chunks.append("".join(current))
    return chunks


def truncate_diff(diff: str, max_files: int, max_lines: int) -> tuple[str, TruncateStats]:
    chunks = _split_into_file_chunks(diff)
    original_files = len(chunks)
    original_lines = diff.count("\n")

    if max_files > 0:
        kept_chunks = chunks[:max_files]
    else:
        kept_chunks = chunks
    kept_files = len(kept_chunks)
    omitted_files = original_files - kept_files

    out_lines: list[str] = []
    total_lines = 0
    line_budget = max_lines if max_lines > 0 else None

    for chunk in kept_chunks:
        chunk_lines = chunk.splitlines(keepends=True)
        if line_budget is not None and total_lines + len(chunk_lines) > line_budget:
            remaining = line_budget - total_lines
            if remaining > 0:
                out_lines.extend(chunk_lines[:remaining])
                total_lines += remaining
            break
        out_lines.extend(chunk_lines)
        total_lines += len(chunk_lines)

    if omitted_files > 0:
        out_lines.append(f"\n[...{omitted_files}개 파일의 diff는 safe-mode 정책으로 생략됨...]\n")
    if line_budget is not None and original_lines > line_budget:
        out_lines.append(
            f"[...총 {original_lines}줄 중 {min(total_lines, line_budget)}줄까지 전송, "
            f"나머지는 safe-mode 정책으로 생략됨...]\n"
        )

    return "".join(out_lines), TruncateStats(
        original_files=original_files,
        kept_files=kept_files,
        original_lines=original_lines,
        kept_lines=min(total_lines, original_lines),
    )


@dataclass
class SafeReport:
    enabled: bool
    mask: MaskStats
    truncate: TruncateStats


def apply_safe_mode(
    diff: str,
    enabled: bool,
    max_files: int = 10,
    max_lines: int = 200,
) -> tuple[str, SafeReport]:
    if not enabled:
        return diff, SafeReport(
            enabled=False,
            mask=MaskStats(counts={}),
            truncate=TruncateStats(
                original_files=len(_split_into_file_chunks(diff)),
                kept_files=len(_split_into_file_chunks(diff)),
                original_lines=diff.count("\n"),
                kept_lines=diff.count("\n"),
            ),
        )

    truncated, truncate_stats = truncate_diff(diff, max_files=max_files, max_lines=max_lines)
    masked, mask_stats = mask_text(truncated)
    return masked, SafeReport(enabled=True, mask=mask_stats, truncate=truncate_stats)
