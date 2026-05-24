from __future__ import annotations

import os
import time
from dataclasses import dataclass


# 환경변수 우선순위: AI_API_KEY (요구사항 명세) → ANTHROPIC_API_KEY (제공자 표준)
_ENV_VARS = ("AI_API_KEY", "ANTHROPIC_API_KEY")

DEFAULT_MODEL = "claude-haiku-4-5-20251001"


class AIClientError(RuntimeError):
    """Wraps all AI-side failures so the CLI layer can format a single message."""


class MissingAPIKeyError(AIClientError):
    pass


@dataclass
class AIResponse:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int


def load_api_key() -> str:
    for name in _ENV_VARS:
        value = os.environ.get(name)
        if value and value.strip():
            return value.strip()
    raise MissingAPIKeyError(
        "AI_API_KEY (또는 ANTHROPIC_API_KEY) 환경변수가 설정되지 않았습니다.\n"
        '  예) Windows PowerShell: $env:AI_API_KEY = "YOUR_KEY"\n'
        '       Bash:               export AI_API_KEY="YOUR_KEY"'
    )


def call_anthropic(
    system: str,
    user: str,
    *,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.3,
    max_tokens: int = 1024,
) -> AIResponse:
    api_key = load_api_key()

    try:
        import anthropic
    except ImportError as exc:
        raise AIClientError(
            "anthropic 패키지가 설치되어 있지 않습니다. `pip install -r requirements.txt` 로 설치하세요."
        ) from exc

    client = anthropic.Anthropic(api_key=api_key)
    started = time.monotonic()

    try:
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
    except anthropic.AuthenticationError as exc:
        raise AIClientError(f"AI API 인증 실패: API Key 가 올바른지 확인하세요. ({exc})") from exc
    except anthropic.RateLimitError as exc:
        raise AIClientError(f"AI API 호출이 속도 제한에 걸렸습니다. ({exc})") from exc
    except anthropic.APIConnectionError as exc:
        raise AIClientError(f"AI API 서버에 접속할 수 없습니다. 네트워크 상태를 확인하세요. ({exc})") from exc
    except anthropic.APIStatusError as exc:
        raise AIClientError(f"AI API 오류 (status={exc.status_code}): {exc.message}") from exc
    except anthropic.APIError as exc:
        raise AIClientError(f"AI API 호출 실패: {exc}") from exc

    elapsed_ms = int((time.monotonic() - started) * 1000)

    pieces: list[str] = []
    for block in response.content:
        if getattr(block, "type", None) == "text":
            pieces.append(block.text)
    text = "".join(pieces).strip()
    if not text:
        raise AIClientError("AI API 응답이 비어 있습니다. max_tokens 를 늘리거나 프롬프트를 점검하세요.")

    usage = getattr(response, "usage", None)
    input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
    output_tokens = getattr(usage, "output_tokens", 0) if usage else 0

    return AIResponse(
        text=text,
        model=response.model or model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=elapsed_ms,
    )
