"""Mini Git 시나리오를 실행하고 검증 증거 파일을 생성한다."""

from pathlib import Path
import sys
from typing import Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import MiniGit


class DemoClock:
    """데모 실행에서 커밋 timestamp를 재현 가능하게 만든다."""

    def __init__(self) -> None:
        self.counter = 0

    def now(self) -> str:
        """고정 날짜에서 1분씩 증가하는 timestamp를 반환한다."""

        self.counter += 1
        return f"2026-06-07 09:{self.counter:02d}:00"


def run_demo(output_dir: Path | str = "evidence") -> Path:
    """대표 CLI 명령을 실행하고 전체 입출력 로그 파일 경로를 반환한다."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    evidence_file = output_path / "demo_run.txt"

    repo = MiniGit(clock=DemoClock())
    transcript: List[str] = []

    run_command(repo, transcript, 'init "Alice Kim"')
    run_command(repo, transcript, 'commit "Initial commit"')
    run_command(repo, transcript, "branch feature")
    run_command(repo, transcript, "switch feature")
    run_command(repo, transcript, 'commit "Add login feature"')
    run_command(repo, transcript, "switch main")
    run_command(repo, transcript, 'commit "Add payment feature"')

    feature_hash = "c000002"
    main_hash = "c000003"
    for command in scenario_queries(feature_hash, main_hash):
        run_command(repo, transcript, command)

    evidence_file.write_text("\n".join(transcript) + "\n", encoding="utf-8")
    return evidence_file


def scenario_queries(feature_hash: str, main_hash: str) -> Iterable[str]:
    """커밋 그래프, 탐색, 검색, 정렬을 보여 주는 조회 명령을 제공한다."""

    return [
        "log",
        f"path {feature_hash} {main_hash}",
        f"ancestors {main_hash}",
        "search login",
        'search --author="Alice Kim"',
        "log --sort-by=author",
        "log --sort-by=date",
    ]


def run_command(repo: MiniGit, transcript: List[str], command: str) -> None:
    """명령 프롬프트와 실행 결과를 transcript에 추가한다."""

    transcript.append(f"mini-git> {command}")
    for line in repo.execute(command):
        transcript.append(line)
    transcript.append("")


if __name__ == "__main__":
    path = run_demo()
    print(f"Wrote {path}")
