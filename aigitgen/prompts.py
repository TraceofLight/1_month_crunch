from __future__ import annotations

from dataclasses import dataclass


COMMIT_SYSTEM = """\
당신은 한국어로 작성되는 Git 커밋 메시지를 만드는 시니어 엔지니어입니다.
입력으로 `git status` 와 `git diff` 결과를 받습니다. 변경의 의도와 영향
범위를 파악한 뒤, Conventional Commits 규칙을 따르는 메시지를 1개 생성하세요.

엄격하게 지켜야 할 출력 규칙:
1. 첫 줄은 커밋 제목입니다. 형식: `<type>: <한국어 요약>`
   - type ∈ {feat, fix, docs, refactor, chore, test, style, perf, build, ci}
   - 50자 이내 권장, 절대 72자를 넘기지 마십시오.
   - 마침표로 끝내지 않습니다.
2. 제목 다음에 빈 줄 1개.
3. 본문은 `- ` 로 시작하는 불릿 2~4개. 각 불릿은 90자 이내.
   - 최소 1개의 불릿에 변경된 파일 또는 모듈명을 명시하세요.
   - 최소 1개의 불릿에 "왜" 또는 "무엇이 달라지는지" 한 문장으로 설명하세요.
4. 출력에 코드 블록(```), 인용부호, 머리말/꼬리말, 추가 설명을 포함하지 마십시오.
5. 한국어로 작성합니다. 영어 식별자(파일명, 함수명)는 그대로 둡니다.
"""


PR_SYSTEM = """\
당신은 한국어로 Pull Request 초안을 작성하는 시니어 엔지니어입니다.
입력으로 현재 브랜치, base 브랜치, 그리고 두 브랜치 사이의 `git diff` 를 받습니다.
변경의 배경과 영향 범위를 파악한 뒤, 아래 형식을 그대로 따르는 초안을 생성하세요.

출력 형식(이 형식을 글자 그대로 지키세요):
TITLE: <PR 제목 한 줄>
---
## Why
- 불릿 1
- 불릿 2 (선택)

## What
- 불릿 1
- 불릿 2
- 불릿 3 (선택)

## How to Test
- 불릿 1
- 불릿 2 (선택)

엄격하게 지켜야 할 규칙:
1. `TITLE:` 다음에는 한 줄 제목만 옵니다. 80자 이내. 마침표로 끝내지 않습니다.
   - Conventional Commits 스타일 prefix(feat/fix/docs 등)를 권장합니다.
2. 구분선 `---` 다음에 본문이 옵니다.
3. 본문 3개 섹션(`## Why`, `## What`, `## How to Test`)은 헤더 텍스트까지 동일하게 작성합니다.
4. 각 섹션은 `- ` 로 시작하는 불릿을 최소 1개 포함해야 합니다.
5. Why 섹션: 변경의 배경/문제 정의를 1~2개 불릿으로.
6. What 섹션: 핵심 변경 사항을 파일/모듈 단위로 2~4개 불릿. 가능한 한 파일명을 포함합니다.
7. How to Test 섹션: 재현 가능한 검증 절차(명령어/체크포인트)를 1~3개 불릿.
8. 코드 블록, 추가 머리말/꼬리말, "참고로", "이상입니다" 같은 문장은 넣지 마십시오.
9. 한국어로 작성합니다. 명령어/파일명/식별자는 그대로 둡니다.
"""


@dataclass
class PromptBundle:
    system: str
    user: str


def _truncate_for_prompt(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    head = text[:max_chars]
    return head + f"\n\n[... {len(text) - max_chars}자 생략 (프롬프트 길이 한도) ...]\n"


def build_commit_prompt(
    status: str,
    diff: str,
    changed_files: list[str],
    *,
    max_diff_chars: int = 12000,
) -> PromptBundle:
    files_block = "\n".join(f"- {f}" for f in changed_files) or "(없음)"
    diff_block = _truncate_for_prompt(diff, max_diff_chars) or "(diff 비어 있음 - 신규 파일이거나 바이너리일 수 있음)"
    user = f"""\
[변경된 파일 목록]
{files_block}

[git status]
```
{status.strip() or "(비어 있음)"}
```

[git diff]
```diff
{diff_block}
```

위 변경을 가장 잘 설명하는 커밋 메시지를 생성하세요.
"""
    return PromptBundle(system=COMMIT_SYSTEM, user=user)


def build_pr_prompt(
    branch: str,
    base: str,
    status: str,
    diff: str,
    changed_files: list[str],
    *,
    max_diff_chars: int = 14000,
) -> PromptBundle:
    files_block = "\n".join(f"- {f}" for f in changed_files) or "(없음)"
    diff_block = _truncate_for_prompt(diff, max_diff_chars) or "(diff 비어 있음)"
    user = f"""\
[현재 브랜치] {branch}
[Base 브랜치] {base}

[변경된 파일 목록]
{files_block}

[git status]
```
{status.strip() or "(비어 있음)"}
```

[브랜치 간 diff]
```diff
{diff_block}
```

위 변경 사항으로 Pull Request 초안을 작성하세요.
"""
    return PromptBundle(system=PR_SYSTEM, user=user)
