"""저수준 파일 입출력 유틸리티.

이 모듈은 특정 도메인(거래/예산 등)을 알지 못하고, JSONL 파일을 다루는
공통 기능만 제공한다.

핵심 설계:
    iter_lines_forward  : 파일을 한 줄씩(앞→뒤) 스트리밍하는 제너레이터.
    iter_lines_reverse  : 파일을 끝에서부터 블록 단위로 읽어 최신 줄부터
                          스트리밍하는 제너레이터. 목록/검색을 "최신순 +
                          스트리밍"으로 동시에 만족시키기 위한 핵심.
    atomic_write_lines  : 임시 파일에 모두 쓴 뒤 os.replace 로 교체하는
                          원자적 쓰기. 수정/삭제 중 중단되어도 원본이 깨지지
                          않도록 한다(보너스: 저장 원자성).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Iterable, Iterator

ENCODING = "utf-8"


def iter_lines_forward(path: Path) -> Iterator[str]:
    """파일을 앞에서부터 한 줄씩 yield 한다(빈 줄 제외).

    파일 객체 반복은 줄 단위 버퍼링이라 전체를 메모리에 올리지 않는다.
    파일이 없으면 아무것도 내보내지 않는다.
    """
    if not path.exists():
        return
    with path.open("r", encoding=ENCODING) as handle:
        for line in handle:
            stripped = line.strip()
            if stripped:
                yield stripped


def iter_lines_reverse(path: Path, block_size: int = 8192) -> Iterator[str]:
    """파일을 끝에서부터 블록 단위로 읽어 최신 줄부터 yield 한다(빈 줄 제외).

    전체 파일을 메모리에 적재하거나 모든 줄을 리스트로 만들지 않고, 필요한
    만큼만 뒤에서부터 읽는다. 따라서 ``list --limit 5`` 는 파일 크기와
    무관하게 마지막 부근 블록만 읽고 멈출 수 있다.

    Args:
        path: 대상 JSONL 파일 경로.
        block_size: 한 번에 뒤에서 읽어 들일 바이트 수.

    Yields:
        최신(파일 끝)부터 과거(파일 앞) 순서의 각 줄 문자열.
    """
    if not path.exists():
        return
    with path.open("rb") as handle:
        handle.seek(0, os.SEEK_END)
        position = handle.tell()
        carry = b""  # 블록 경계에 걸친 미완성 앞부분 줄
        while position > 0:
            read_size = min(block_size, position)
            position -= read_size
            handle.seek(position)
            chunk = handle.read(read_size)
            carry = chunk + carry
            parts = carry.split(b"\n")
            carry = parts[0]  # 더 앞 블록과 이어질 수 있으므로 보류
            for raw in reversed(parts[1:]):
                text = raw.decode(ENCODING).strip()
                if text:
                    yield text
        text = carry.decode(ENCODING).strip()
        if text:
            yield text


def atomic_write_lines(path: Path, lines: Iterable[str]) -> None:
    """``lines`` 를 임시 파일에 쓰고 원자적으로 ``path`` 로 교체한다.

    같은 디렉터리에 임시 파일을 만들고 fsync 후 os.replace 로 교체하므로,
    쓰기 도중 프로세스가 죽어도 원본 파일은 손상되지 않는다.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding=ENCODING, newline="\n") as handle:
            for line in lines:
                handle.write(line + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise


def append_line(path: Path, line: str) -> None:
    """파일 끝에 한 줄을 추가한다(없으면 부모 디렉터리/파일 생성)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding=ENCODING, newline="\n") as handle:
        handle.write(line + "\n")


def ensure_file(path: Path) -> None:
    """파일이 없으면 빈 파일로 생성한다(초기 실행 대비)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.touch()
