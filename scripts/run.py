"""Mini Git 시나리오를 실행하고 검증 증거 파일을 생성한다."""

from pathlib import Path
import sys
from time import perf_counter
from typing import Iterable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from main import MiniGit, compare_text, insertion_sort, merge_sort


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

    run_command(repo, transcript, "merge feature")
    run_command(repo, transcript, "ancestors c000004")
    left_file, right_file = write_demo_diff_files(output_path)
    run_command(repo, transcript, f'diff "{left_file}" "{right_file}"')
    run_disconnected_path_demo(transcript)

    evidence_file.write_text("\n".join(transcript) + "\n", encoding="utf-8")
    return evidence_file


def write_demo_diff_files(output_path: Path) -> Tuple[Path, Path]:
    """데모 diff 명령에 사용할 작은 텍스트 파일 두 개를 생성한다."""

    left_file = output_path / "diff_left.txt"
    right_file = output_path / "diff_right.txt"
    left_file.write_text("same\nold line\nkeep\n", encoding="utf-8")
    right_file.write_text("same\nnew line\nkeep\n", encoding="utf-8")
    return left_file, right_file


def run_sort_benchmark(output_dir: Path | str = "evidence") -> Path:
    """직접 구현한 두 정렬 알고리즘의 실행 시간을 CSV 형식으로 저장한다."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    evidence_file = output_path / "sort_benchmark.txt"
    rows = ["algorithm,size,seconds,first,last"]
    for size in [40, 120, 360]:
        values = benchmark_values(size)
        for algorithm_name, algorithm in [
            ("merge_sort", merge_sort),
            ("insertion_sort", insertion_sort),
        ]:
            started_at = perf_counter()
            ordered = algorithm(values, compare_text)
            elapsed = perf_counter() - started_at
            rows.append(
                f"{algorithm_name},{size},{elapsed:.8f},{ordered[0]},{ordered[-1]}"
            )
    evidence_file.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return evidence_file


def benchmark_values(size: int) -> List[str]:
    """정렬 비교에 사용할 재현 가능한 역순 문자열 데이터를 만든다."""

    values: List[str] = []
    number = size
    while number > 0:
        values.append(f"{number:06d}")
        number -= 1
    return values


def scenario_queries(feature_hash: str, main_hash: str) -> Iterable[str]:
    """커밋 그래프, 탐색, 검색, 정렬을 보여 주는 조회 명령을 제공한다."""

    return [
        "log",
        f"path {feature_hash} {main_hash}",
        f"ancestors {main_hash}",
        "search login",
        'search "login feature"',
        'search --author="Alice Kim"',
        "log --sort-by=author",
        "log --sort-by=date",
    ]


def run_disconnected_path_demo(transcript: List[str]) -> None:
    """서로 연결되지 않은 루트 커밋 사이의 경로 없음 출력을 transcript에 추가한다."""

    repo = MiniGit(clock=DemoClock())
    run_command(repo, transcript, 'init "Bob Lee"')
    run_command(repo, transcript, "branch side")
    run_command(repo, transcript, "switch side")
    run_command(repo, transcript, 'commit "Side root"')
    run_command(repo, transcript, "switch main")
    run_command(repo, transcript, 'commit "Main root"')
    run_command(repo, transcript, "path c000001 c000002")


def run_command(repo: MiniGit, transcript: List[str], command: str) -> None:
    """명령 프롬프트와 실행 결과를 transcript에 추가한다."""

    transcript.append(f"mini-git> {command}")
    for line in repo.execute(command):
        transcript.append(line)
    transcript.append("")


if __name__ == "__main__":
    demo_path = run_demo()
    benchmark_path = run_sort_benchmark()
    print(f"Wrote {demo_path}")
    print(f"Wrote {benchmark_path}")
