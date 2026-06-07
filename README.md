# 실전 Git 협업 워크플로우

## 제출 정보

| 항목 | 값 |
| --- | --- |
| 팀명 | 플로우랩 |
| 저장소 URL | https://github.com/TraceofLight/ai-assignment |
| 팀 구성 | 김민서, 이지현, 박서연, 최준호 |
| 선택한 간단한 결과물 | 팀원별 Python 유틸 함수 모음 |
| 제출 인덱스 | `SUBMISSION.md` |
| 실행 증빙 | `evidence/run-report.txt`, `evidence/unit-test.log`, `evidence/git-log-graph.txt` |

플로우랩은 4인 팀 기준으로 GitHub Flow를 적용한다. 산출물은 협업 규칙 문서, 충돌 해결 기록, 트러블슈팅 기록, Python 유틸 함수, 재현 가능한 실행 스크립트로 구성했다. Python 유틸 함수는 브랜치 이름, 커밋 메시지, PR 본문, 충돌 마커를 검증해 팀 규칙을 코드로 확인하는 작은 결과물이다.

## 산출물 구조

| 경로 | 역할 |
| --- | --- |
| `README.md` | 과제 목표, 설계 이유, 협업 규칙, 증빙, 실행 방법 |
| `SUBMISSION.md` | 팀원별 Issue, PR, 리뷰, 문서, 증빙 링크 인덱스 |
| `docs/CONTRIBUTING.md` | 브랜치, 커밋, PR, 리뷰, 충돌 대응 규칙 |
| `docs/conflict-resolution.md` | 충돌 해결 2회 기록, 비자명 충돌 포함 |
| `docs/troubleshooting-log.md` | `amend`, `reset --soft`, `revert`, `stash` 기록 |
| `src/team_utils.py` | 팀원별 유틸 함수 모음 |
| `tests/test_team_utils.py` | 유틸 함수 동작 검증 |
| `scripts/run.py` | 로드, 전처리, 실행, 평가, 결과 저장 단일 진입점 |
| `Dockerfile` | Ubuntu 24.04 기반 재현 실행 환경 |
| `team/` | 팀원별 역할 소개 |

## 팀원별 기여 인덱스

| 팀원 | 담당 결과물 | Issue | PR | 리뷰 작성 | 리뷰 반영 |
| --- | --- | --- | --- | --- | --- |
| 김민서 | 브랜치 규칙, 커밋 메시지 검증 | #1, #2 | #1, #2 | #3, #4 | PR #2에서 커밋 메시지 검증 기준 반영 |
| 이지현 | PR 본문 규칙, 리뷰 기준 | #3, #4 | #3, #4 | #1, #5 | PR #3에서 리뷰 코멘트 예시 보강 |
| 박서연 | 충돌 해결 기록, 문서 검수 | #5, #6 | #5, #6 | #2, #7 | PR #5에서 충돌 해결 이유 추가 |
| 최준호 | 트러블슈팅 기록, 실행 증빙 | #7, #8 | #7, #8 | #1, #6 | PR #7에서 stash 주의점 추가 |

팀원별 링크는 `SUBMISSION.md`에서 빠르게 확인할 수 있다. PR 본문에는 항상 `Closes #이슈번호`, 변경 사항, 변경 이유, 테스트/검증 방법을 포함한다.

## Git 브랜치의 내부 동작

Git에서 브랜치는 커밋을 가리키는 포인터다. 새 브랜치를 만들면 파일 전체를 복사하는 것이 아니라 특정 커밋을 가리키는 이름이 생긴다. 커밋을 추가하면 현재 브랜치 포인터가 새 커밋으로 이동하고, `HEAD`는 현재 작업 중인 브랜치 또는 커밋을 가리킨다.

브랜치를 나누는 이유는 작업 단위를 격리하기 위해서다. 기능 개발, 문서 수정, 충돌 실습을 같은 `main`에서 동시에 진행하면 검증되지 않은 변경이 기준선을 깨뜨릴 수 있다. `feature/*` 브랜치에서 작업하면 실패한 시도와 리뷰 반영을 분리할 수 있고, PR에서 변경 의도와 검증 결과를 확인한 뒤 `main`에 병합할 수 있다.

## GitHub Flow 선택 이유

`main`은 항상 팀 기준에서 깨지지 않는 상태로 유지한다.
모든 변경은 `feature/*` 브랜치에서 만들고 PR 리뷰 후 병합한다.
브랜치와 PR 흐름이 단순해 4인 팀이 충돌, 리뷰, 이슈 연동을 반복 학습하기에 적합하다.

## 저장소 준비와 보호 규칙

기본 폴더는 `docs/`, `src/`, `team/`, `tests/`, `scripts/`, `evidence/`로 구성했다. GitHub 저장소는 Organization 저장소 또는 개인 저장소에 Collaborator를 초대하는 방식으로 운영할 수 있으며, 이 제출물은 개인 저장소 URL을 기준으로 작성했다.

`main` 브랜치 보호 규칙은 다음 값을 사용한다.

| 항목 | 설정 |
| --- | --- |
| 직접 push | 금지 |
| 병합 방식 | PR을 통한 병합만 허용 |
| 승인 수 | 최소 1명 approve |
| 리뷰 품질 | 실질 코멘트 1개 이상 |
| 히스토리 재작성 | 공유 브랜치에서 금지 |

공유 브랜치에서 무리한 `reset`, `rebase`, 강제 푸시를 금지한다. 이미 원격에 공유된 변경을 되돌릴 때는 새 되돌림 커밋을 만드는 `git revert`를 우선 사용한다.

## 브랜치 네이밍 규칙

브랜치 이름은 `feature/<name>-<topic>` 형식을 사용한다. 이름과 작업 주제는 소문자와 하이픈으로 정규화한다.

예시는 다음과 같다.

```txt
feature/kim-min-seo-math-utils
feature/lee-ji-hyun-review-guide
feature/park-seo-yeon-conflict-log
feature/choi-jun-ho-troubleshooting
```

`src/team_utils.py`의 `branch_name` 함수는 팀원 이름과 작업 주제를 받아 같은 규칙의 브랜치 이름을 만든다.

## 커밋 메시지 규칙

커밋 메시지는 `type: subject` 형식으로 작성한다.

| type | 사용 상황 |
| --- | --- |
| `feat` | 기능 또는 예시 코드 추가 |
| `fix` | 버그 수정 |
| `docs` | 문서 작성 또는 수정 |
| `refactor` | 동작을 유지한 구조 개선 |
| `test` | 테스트 추가 또는 수정 |
| `chore` | 설정, 실행 환경, 유지보수 |

`update`, `fix`, `temp`, `wip`, `final`, `bug fix`, `edit file`처럼 변경 대상을 알 수 없는 메시지는 금지한다. `fix: bug fix`도 무엇을 고쳤는지 드러나지 않으므로 허용하지 않는다. `src/team_utils.py`의 `commit_message_status` 함수가 이 규칙을 검증한다.

## PR과 코드 리뷰 운영

PR은 변경을 병합하기 전에 팀이 의도, 영향, 검증 결과를 확인하는 협업 단위다. PR을 사용하면 이슈와 변경을 연결할 수 있고, 코드 리뷰 코멘트와 작성자의 답변이 기록으로 남는다. 리뷰는 단순 승인 절차가 아니라 결함을 줄이고 팀 규칙을 맞추는 장치다.

PR 본문에는 다음 항목을 포함한다.

```txt
Closes #이슈번호

## 변경 사항(What)
- 무엇을 바꿨는지 작성한다.

## 변경 이유(Why)
- 왜 필요한 변경인지 작성한다.

## 테스트/검증(How)
- 실행한 명령과 확인한 증빙을 작성한다.
```

리뷰어는 파일, 라인, 동작, 문서 근거 중 하나를 들어 실질 코멘트를 남긴다. 작성자는 코멘트에 답하거나 수정 커밋으로 반영한다. 각 팀원은 본인 PR이 아닌 PR에 최소 2회 리뷰를 작성하고, 본인 PR에서 최소 1회 리뷰 반영 기록을 남긴다.

## 충돌이 발생하는 이유와 충돌 마커

충돌은 Git이 두 변경을 자동으로 합칠 수 없을 때 발생한다. 대표적으로 같은 파일의 같은 hunk를 서로 다르게 수정하거나, 한쪽은 파일을 이동 또는 삭제하고 다른 한쪽은 내용을 수정할 때 충돌이 생긴다.

충돌 마커의 의미는 다음과 같다.

```txt
<<<<<<< HEAD
현재 브랜치의 내용
=======
병합하려는 브랜치의 내용
>>>>>>> feature/example
```

`<<<<<<<`부터 `=======` 전까지는 현재 브랜치의 내용이다. `=======`부터 `>>>>>>>` 전까지는 병합 대상 브랜치의 내용이다. 해결자는 두 영역을 비교해 하나를 선택하거나, 둘을 합치거나, 새 구조로 리팩터링한 뒤 마커를 모두 제거해야 한다.

충돌 해결 기록은 `docs/conflict-resolution.md`에 남겼다. 기록 1은 같은 파일의 같은 hunk를 다르게 수정한 비자명 충돌이고, 기록 2는 파일 이동과 내용 수정이 겹친 modify/delete 유형이다.

## `reset`, `revert`, `stash` 차이

| 명령 | 용도 | 공유 브랜치 영향 | 사용 기준 |
| --- | --- | --- | --- |
| `git reset --soft HEAD~1` | 최근 로컬 커밋을 취소하고 변경은 유지 | push 전 로컬에서만 안전 | 커밋을 다시 나누거나 메시지 흐름을 정리할 때 |
| `git revert <SHA>` | 기존 커밋의 반대 변경을 새 커밋으로 생성 | 원격 히스토리를 유지 | 이미 push 또는 병합된 변경을 취소할 때 |
| `git stash push` | 커밋하지 않은 변경을 임시 보관 | 공유되지 않음 | 브랜치 전환 전 작업 트리를 비워야 할 때 |
| `git stash pop` | 임시 보관한 변경을 복원 | 충돌 가능 | 복원 후 반드시 `git status`와 테스트 확인 |

최근 커밋 메시지만 수정할 때는 `git commit --amend`를 사용한다. 단, 이미 원격에 공유된 커밋을 `amend`한 뒤 강제 푸시하면 다른 팀원의 히스토리와 어긋날 수 있으므로 push 전 로컬 커밋에만 사용한다.

트러블슈팅 4종 기록은 `docs/troubleshooting-log.md`에 있다. 각 기록은 참여자, 상황, 명령, 결과, 선택 이유를 포함한다.

## 간단한 결과물

선택한 결과물은 팀원별 Python 유틸 함수 모음이다.

| 팀원 | 함수 | 역할 |
| --- | --- | --- |
| 김민서 | `branch_name` | 팀원 이름과 작업 주제로 feature 브랜치 이름 생성 |
| 이지현 | `commit_message_status` | 커밋 메시지 형식과 의미 있는 subject 검증 |
| 박서연 | `pr_body_status` | PR 본문 필수 항목 검증 |
| 최준호 | `conflict_marker_report` | 충돌 마커가 남은 파일과 라인 번호 탐지 |

사용 예시는 다음과 같다.

```python
from pathlib import Path

from src.team_utils import branch_name, commit_message_status, conflict_marker_report

print(branch_name("Kim Min Seo", "Add Math Utils"))
print(commit_message_status("docs: add conflict runbook").valid)
print(conflict_marker_report(Path("src")).total_markers)
```

## 재현 실행 방법

모든 실행은 Ubuntu 24.04 기반 Docker 컨테이너에서 수행했다. 외부 Python 패키지는 사용하지 않으며, `pyproject.toml`의 `dependencies = []`로 의존성이 고정되어 있다. Docker 이미지는 `ubuntu:24.04`를 기반으로 하고 Python은 Ubuntu 24.04 패키지의 Python 3.12 계열을 사용한다.

이미지를 빌드한다.

```bash
docker build -t codyssey-cli-test-ai-assignment .
```

유닛 테스트를 실행한다.

```bash
docker run --rm --name codyssey-cli-test-unit -v "${PWD}:/workspace" -w /workspace codyssey-cli-test-ai-assignment python3 -m unittest discover -s tests
```

전체 파이프라인을 실행한다.

```bash
docker run --rm --name codyssey-cli-test-run -v "${PWD}:/workspace" -w /workspace codyssey-cli-test-ai-assignment python3 scripts/run.py
```

명령 옵션 선택 이유는 다음과 같다.

| 옵션 | 이유 |
| --- | --- |
| `--rm` | 실행 후 컨테이너를 남기지 않아 반복 검증 환경을 깨끗하게 유지 |
| `--name codyssey-cli-test-*` | 검증 컨테이너를 식별하고 과제 실행 컨테이너와 이름 규칙 일치 |
| `-v "${PWD}:/workspace"` | 호스트 저장소의 변경 파일과 컨테이너 실행 결과를 같은 작업 트리에 반영 |
| `-w /workspace` | 상대 경로 기반 스크립트와 테스트가 저장소 루트에서 실행되도록 고정 |

`scripts/run.py`는 저장소 구조를 로드하고, 필수 경로 존재 여부를 전처리하고, 유틸 함수와 테스트를 실행하고, 결과를 평가한 뒤 `evidence/run-report.json`과 `evidence/run-report.txt`를 저장한다.

## 검증 증빙

| 증빙 | 내용 |
| --- | --- |
| `evidence/red-test.log` | 구현 전 테스트 실패 기록. `src.team_utils` 모듈이 없어 실패한 TDD red 단계 |
| `evidence/unit-test.log` | `python3 -m unittest discover -s tests` 실행 결과 |
| `evidence/run-report.txt` | 단일 진입점 `scripts/run.py` 실행 결과 |
| `evidence/run-report.json` | 실행 결과의 JSON 원본 |
| `evidence/git-log-graph.txt` | `git log --oneline --graph --all` 결과 |

검증에서 확인한 항목은 필수 파일 존재, 브랜치 이름 생성, 커밋 메시지 검증, PR 본문 검증, `src/` 충돌 마커 0개, 유닛 테스트 통과 여부다.

## 운영 안정성과 위험 대응

주요 위험은 공유 브랜치 히스토리 훼손, 의미 없는 커밋 메시지, 형식만 있는 리뷰, 충돌 해결 기록 누락, 로컬에서만 되는 실행 환경이다. 대응은 다음과 같다.

| 위험 | 대응 |
| --- | --- |
| `main` 직접 push | Branch Protection Rule로 PR 병합만 허용 |
| 공유 히스토리 재작성 | `main`과 병합된 브랜치에서 강제 푸시 금지 |
| 모호한 커밋 메시지 | `type: subject` 규칙과 금지어 목록 운영 |
| 형식적 리뷰 | 파일, 라인, 동작, 문서 근거가 있는 코멘트 요구 |
| 충돌 해결 구두 처리 | `docs/conflict-resolution.md`에 상황, 마커, 명령, 결과 기록 |
| 로컬 환경 의존 | Ubuntu 24.04 Docker 실행과 증빙 파일 보존 |

문제가 생기면 먼저 `git status`로 작업 트리 상태를 확인한다. 그다음 문제가 로컬 커밋인지, 이미 공유된 커밋인지, 미커밋 변경인지 구분한다. 로컬 커밋 정리는 `amend` 또는 `reset --soft`, 공유된 커밋 취소는 `revert`, 미커밋 변경 보관은 `stash`를 사용한다. 해결 뒤에는 테스트를 실행하고 관련 문서와 evidence 파일에 결과를 남긴다.
