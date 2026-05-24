from __future__ import annotations

import re
from dataclasses import dataclass, field


COMMIT_TITLE_HARD_MAX = 72
COMMIT_TITLE_SOFT_MAX = 50
PR_TITLE_MAX = 80

PR_REQUIRED_SECTIONS = ("Why", "What", "How to Test")


@dataclass
class CommitDraft:
    title: str
    body: str
    warnings: list[str] = field(default_factory=list)

    def render(self) -> str:
        if not self.body.strip():
            return self.title
        return f"{self.title}\n\n{self.body.rstrip()}"


@dataclass
class PRDraft:
    title: str
    body: str
    warnings: list[str] = field(default_factory=list)


def _strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        # remove first fence line
        lines = text.split("\n")
        lines = lines[1:]
        # drop trailing closing fence if present
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def _enforce_title_length(title: str, hard_max: int, warnings: list[str], label: str) -> str:
    title = title.strip().rstrip(".。 ").strip()
    if len(title) > hard_max:
        warnings.append(
            f"{label}이 {hard_max}자를 초과하여 {hard_max - 1}자로 잘랐습니다 (원본 {len(title)}자)."
        )
        title = title[: hard_max - 1].rstrip() + "…"
    return title


def parse_commit(raw: str) -> CommitDraft:
    warnings: list[str] = []
    text = _strip_code_fence(raw)
    lines = text.split("\n")
    if not lines:
        return CommitDraft(title="", body="", warnings=["AI 응답이 비어 있습니다."])

    title = lines[0].strip()
    rest = lines[1:]
    # strip leading blank lines from body
    while rest and not rest[0].strip():
        rest.pop(0)
    body_lines = rest

    title = _enforce_title_length(title, COMMIT_TITLE_HARD_MAX, warnings, "커밋 제목")
    if len(title) > COMMIT_TITLE_SOFT_MAX:
        warnings.append(f"커밋 제목이 권장 {COMMIT_TITLE_SOFT_MAX}자를 초과합니다 ({len(title)}자).")

    body = "\n".join(body_lines).strip()
    if body:
        bullet_count = sum(1 for line in body_lines if line.lstrip().startswith(("-", "*")))
        if bullet_count == 0:
            warnings.append("커밋 본문에 불릿(- ) 형식이 감지되지 않았습니다.")

    return CommitDraft(title=title, body=body, warnings=warnings)


_TITLE_PATTERN = re.compile(r"^\s*TITLE\s*:\s*(.+?)\s*$", re.IGNORECASE | re.MULTILINE)


def parse_pr(raw: str) -> PRDraft:
    warnings: list[str] = []
    text = _strip_code_fence(raw)

    title_match = _TITLE_PATTERN.search(text)
    if title_match:
        title = title_match.group(1).strip()
        body_start = title_match.end()
        body = text[body_start:].lstrip("\n")
        # drop a leading separator like "---"
        if body.startswith("---"):
            body = body.split("\n", 1)[1] if "\n" in body else ""
        body = body.lstrip("\n")
    else:
        # Fallback: assume first line is title, rest is body
        warnings.append("AI 응답에서 `TITLE:` 헤더를 찾지 못해 첫 줄을 제목으로 사용했습니다.")
        lines = text.split("\n", 1)
        title = lines[0].strip().lstrip("#").strip()
        body = lines[1].strip() if len(lines) > 1 else ""

    title = _enforce_title_length(title, PR_TITLE_MAX, warnings, "PR 제목")

    body = _ensure_pr_sections(body, warnings)

    return PRDraft(title=title, body=body, warnings=warnings)


def _ensure_pr_sections(body: str, warnings: list[str]) -> str:
    """Verify Why/What/How to Test sections exist with ≥1 bullet each.

    Missing sections are appended as placeholders so the output stays
    structurally valid even when the model misses one.
    """
    sections = _split_sections(body)

    out_parts: list[str] = []
    for name in PR_REQUIRED_SECTIONS:
        section_body = sections.get(name.lower())
        if section_body is None:
            warnings.append(f"PR 본문에 `## {name}` 섹션이 없어 자리표시자를 추가했습니다.")
            placeholder = _placeholder_for(name)
            out_parts.append(f"## {name}\n- {placeholder}")
            continue
        bullets = [
            line for line in section_body.splitlines() if line.lstrip().startswith(("-", "*"))
        ]
        if not bullets:
            warnings.append(f"PR `## {name}` 섹션에 불릿이 없어 자리표시자를 추가했습니다.")
            section_body = (section_body.rstrip() + f"\n- {_placeholder_for(name)}").strip()
        out_parts.append(f"## {name}\n{section_body.strip()}")

    # Preserve any extra sections the model produced that aren't required.
    for key, value in sections.items():
        if key in {s.lower() for s in PR_REQUIRED_SECTIONS}:
            continue
        # restore original header casing if possible
        header_match = re.search(r"##\s*" + re.escape(key) + r"\b.*", body, re.IGNORECASE)
        header = header_match.group(0).strip() if header_match else f"## {key.title()}"
        out_parts.append(f"{header}\n{value.strip()}")

    return "\n\n".join(out_parts).strip() + "\n"


def _split_sections(body: str) -> dict[str, str]:
    """Return {lowercase_section_name: body_text} for any `## Heading` blocks."""
    sections: dict[str, str] = {}
    current_name: str | None = None
    current_buf: list[str] = []
    for line in body.splitlines():
        m = re.match(r"^\s*##\s+(.+?)\s*$", line)
        if m:
            if current_name is not None:
                sections[current_name.lower()] = "\n".join(current_buf).strip()
            current_name = m.group(1).strip()
            current_buf = []
        else:
            if current_name is not None:
                current_buf.append(line)
    if current_name is not None:
        sections[current_name.lower()] = "\n".join(current_buf).strip()
    return sections


def _placeholder_for(section: str) -> str:
    return {
        "Why": "(변경 배경을 수동으로 보강하세요)",
        "What": "(핵심 변경 사항을 수동으로 보강하세요)",
        "How to Test": "(검증 절차를 수동으로 보강하세요)",
    }.get(section, "(내용을 수동으로 보강하세요)")
