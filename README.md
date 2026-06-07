# 실전 Git 협업 워크플로우

## 제출 정보

| 항목 | 값 |
| --- | --- |
| 팀명 | 플로우랩 |
| 저장소 URL | https://github.com/TraceofLight/ai-assignment |
| 팀 구성 | 김민서, 이지현, 박서연, 최준호 |
| 선택한 간단한 결과물 | 팀원별 Python 유틸 함수 모음 |
| 제출 인덱스 | `SUBMISSION.md` |
| 실행 증빙 | `evidence/run-report.txt`, `evidence/unit-test.log`, `evidence/git-log-graph.txt`, `evidence/github-branch-protection.json` |

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
| 김민서 | 브랜치 규칙, 커밋 메시지 검증 | https://github.com/TraceofLight/ai-assignment/issues/1, https://github.com/TraceofLight/ai-assignment/issues/2 | https://github.com/TraceofLight/ai-assignment/pull/1, https://github.com/TraceofLight/ai-assignment/pull/2 | PR #3, PR #4 | PR #2에서 커밋 메시지 검증 기준 반영 |
| 이지현 | PR 본문 규칙, 리뷰 기준 | https://github.com/TraceofLight/ai-assignment/issues/3, https://github.com/TraceofLight/ai-assignment/issues/4 | https://github.com/TraceofLight/ai-assignment/pull/3, https://github.com/TraceofLight/ai-assignment/pull/4 | PR #1, PR #5 | PR #3에서 리뷰 코멘트 예시 보강 |
| 박서연 | 충돌 해결 기록, 문서 검수 | https://github.com/TraceofLight/ai-assignment/issues/5, https://github.com/TraceofLight/ai-assignment/issues/6 | https://github.com/TraceofLight/ai-assignment/pull/5, https://github.com/TraceofLight/ai-assignment/pull/6 | PR #2, PR #7 | PR #5에서 충돌 해결 이유 추가 |
| 최준호 | 트러블슈팅 기록, 실행 증빙 | https://github.com/TraceofLight/ai-assignment/issues/7, https://github.com/TraceofLight/ai-assignment/issues/8 | https://github.com/TraceofLight/ai-assignment/pull/7, https://github.com/TraceofLight/ai-assignment/pull/8 | PR #1, PR #6 | PR #7에서 stash 주의점 추가 |

팀원별 링크는 `SUBMISSION.md`에서 빠르게 확인할 수 있다. PR 본문에는 항상 `Closes #이슈번호`, 변경 사항, 변경 이유, 테스트/검증 방법을 포함한다.

## GitHub 저장소 운영 증빙

저장소 URL은 https://github.com/TraceofLight/ai-assignment 이다. 저장소 확인 결과와 보호 규칙 확인 결과는 다음 evidence 파일에 저장했다.

| 증빙 | 확인 내용 |
| --- | --- |
| `evidence/github-repository.json` | 저장소 이름, 공개 여부, URL, 관리자 권한 |
| `evidence/github-branch-protection.json` | `main` 브랜치 보호 규칙, 관리자 강제 적용, PR 승인 1명, 대화 해결 필수, 강제 푸시 금지, 브랜치 삭제 금지 |

팀 저장소는 개인 저장소에 Collaborator를 초대하는 옵션 B 기준으로 운영한다. 팀원은 각자 feature 브랜치에서 작업하고, PR에서 최소 1명의 승인을 받은 뒤 병합한다. 저장소 관리자 권한으로 `main` 브랜치 보호 규칙을 확인하고, 설정 값은 `evidence/github-branch-protection.json`에 남겼다.

## Git 브랜치의 내부 동작

Git에서 브랜치는 커밋을 가리키는 포인터다. 새 브랜치를 만들면 파일 전체를 복사하는 것이 아니라 특정 커밋을 가리키는 이름이 생긴다. 커밋을 추가하면 현재 브랜치 포인터가 새 커밋으로 이동하고, `HEAD`는 현재 작업 중인 브랜치 또는 커밋을 가리킨다.

브랜치를 나누는 이유는 작업 단위를 격리하기 위해서다. 기능 개발, 문서 수정, 충돌 실습을 같은 `main`에서 동시에 진행하면 검증되지 않은 변경이 기준선을 깨뜨릴 수 있다. `feature/*` 브랜치에서 작업하면 실패한 시도와 리뷰 반영을 분리할 수 있고, PR에서 변경 의도와 검증 결과를 확인한 뒤 `main`에 병합할 수 있다.

## GitHub Flow 선택 이유

`main`은 항상 팀 기준에서 깨지지 않는 상태로 유지한다.
모든 변경은 `feature/*` 브랜치에서 만들고 PR 리뷰 후 병합한다.
브랜치와 PR 흐름이 단순해 4인 팀이 충돌, 리뷰, 이슈 연동을 반복 학습하기에 적합하다.

## 긴급 핫픽스 처리 순서

긴급 수정이 필요해도 `main`에 직접 push하지 않는다. 기준선이 깨진 상태에서 바로 수정하면 원인 커밋, 검증 결과, 리뷰 판단이 기록으로 남지 않기 때문이다.

처리 순서는 다음과 같다.

1. 이슈를 만들고 장애 증상, 영향 범위, 재현 절차를 적는다.
2. `main`의 최신 상태에서 `feature/<name>-hotfix-<topic>` 브랜치를 만든다.
3. 수정 범위를 장애 원인에 필요한 파일로 제한한다.
4. 로컬 또는 Docker 컨테이너에서 실패 증상 재현과 수정 후 검증을 실행한다.
5. PR 본문에 `Closes #이슈번호`, 변경 사항, 변경 이유, 테스트/검증 방법을 적는다.
6. 최소 1명 리뷰어가 원인과 부작용 가능성을 확인하고 approve한다.
7. PR로 `main`에 병합한 뒤 팀 기준 배포 또는 제출 상태를 다시 확인한다.
8. 핫픽스에서 임시 대응을 했으면 후속 이슈를 만들어 정리 작업을 분리한다.

핫픽스는 빠르게 처리하지만 리뷰와 기록을 생략하지 않는다. 속도 때문에 보호 규칙을 끄거나 강제 푸시를 사용하면 이후 팀원이 같은 기준선을 신뢰할 수 없다.

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

`main` 보호 규칙의 실제 확인 결과는 `evidence/github-branch-protection.json`에 저장했다. 확인된 값은 관리자에게도 보호 규칙 적용, PR 리뷰 1명 이상, 대화 해결 필수, 강제 푸시 금지, 브랜치 삭제 금지다.

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

팀원별 PR과 리뷰 상호작용은 다음 기준으로 확인한다.

| 팀원 | 병합 PR 1 | 병합 PR 2 | 본인이 작성한 리뷰 | 본인 PR에서 반영한 리뷰 |
| --- | --- | --- | --- | --- |
| 김민서 | https://github.com/TraceofLight/ai-assignment/pull/1 | https://github.com/TraceofLight/ai-assignment/pull/2 | PR #3에서 PR 본문 검증 누락 질문, PR #4에서 리뷰 규칙 예시 개선 제안 | PR #2에서 `fix: bug fix`를 거부하도록 커밋 메시지 검증 기준 보강 |
| 이지현 | https://github.com/TraceofLight/ai-assignment/pull/3 | https://github.com/TraceofLight/ai-assignment/pull/4 | PR #1에서 브랜치 이름 예시의 소문자 정규화 질문, PR #5에서 충돌 기록의 선택 이유 보강 요청 | PR #3에서 리뷰 코멘트가 파일 또는 동작 근거를 포함하도록 예시 추가 |
| 박서연 | https://github.com/TraceofLight/ai-assignment/pull/5 | https://github.com/TraceofLight/ai-assignment/pull/6 | PR #2에서 금지 커밋 메시지 목록 확대 제안, PR #7에서 revert와 reset 구분 설명 요청 | PR #5에서 충돌 해결 전략을 keep both로 선택한 이유 추가 |
| 최준호 | https://github.com/TraceofLight/ai-assignment/pull/7 | https://github.com/TraceofLight/ai-assignment/pull/8 | PR #1에서 테스트 증빙 파일 경로 추가 요청, PR #6에서 modify/delete 충돌의 요구 파일명 근거 확인 | PR #7에서 `git stash pop` 이후 충돌과 테스트 확인 주의점 추가 |

리뷰가 반영되었는지는 PR의 대화 스레드, 추가 커밋, 작성자 답글 세 가지 중 하나로 확인한다. `SUBMISSION.md`는 같은 링크를 팀원별로 다시 모아 제출 확인 시간을 줄인다.

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

충돌 기록 1의 참여자는 김민서, 이지현, 박서연이다. 김민서의 `feature/kim-min-seo-math-utils`와 이지현의 `feature/lee-ji-hyun-review-guide`가 `README.md`의 결과물 설명 문단을 서로 다르게 바꿨다.

```txt
<<<<<<< HEAD
간단한 결과물은 팀원별 유틸 함수 모음으로 구성한다.
=======
간단한 결과물은 협업 규칙 검증에 사용할 Python 유틸 함수 모음으로 구성한다.
>>>>>>> feature/lee-ji-hyun-review-guide
```

두 문장이 모두 필요한 정보를 담고 있었으므로 하나를 버리지 않고 합쳤다. 최종 문장은 결과물이 팀원별 Python 유틸 함수 모음이며 브랜치 이름, 커밋 메시지, PR 본문, 충돌 마커 검증에 쓰인다는 내용을 담도록 정리했다. 해결 중 확인한 명령은 `git status`, `git diff`, `python3 -m unittest discover -s tests`, `git add README.md`, `git commit -m "docs: resolve utility deliverable wording conflict"`이다.

충돌 기록 2의 참여자는 박서연, 최준호, 김민서다. 박서연은 `docs/troubleshooting-log.md` 내용을 수정했고, 최준호는 같은 파일을 `docs/git-troubleshooting.md`로 이동하려고 했다. 한쪽은 파일 이동, 다른 한쪽은 내용 수정이어서 다음 충돌이 발생했다.

```txt
CONFLICT (modify/delete): docs/troubleshooting-log.md deleted in feature/choi-jun-ho-doc-rename and modified in HEAD.
```

과제 요구 파일명이 `docs/troubleshooting-log.md`이므로 파일 이동은 취소하고 요구 파일명을 유지했다. 최준호의 구조 개선 문구 중 필요한 부분만 기존 파일에 반영했다. 해결 중 확인한 명령은 `git status`, `git checkout --ours docs/troubleshooting-log.md`, `git diff`, `python3 -m unittest discover -s tests`, `git add docs/troubleshooting-log.md`, `git commit -m "docs: keep required troubleshooting log path"`이다.

반복적으로 충돌이 발생하면 충돌 파일, 충돌 hunk, 최근 병합 순서, 같은 문단을 수정한 PR 수를 먼저 확인한다. 원인이 작업 범위 중복이면 한 명이 기준 문장을 먼저 병합하고 나머지 PR은 최신 `main` 기준으로 다시 확인한다. 원인이 파일 이동과 내용 수정의 병행이면 파일 경로 변경 PR을 먼저 분리하고, 경로가 과제 요구나 외부 링크와 연결되어 있는지 확인한 뒤 내용 수정 PR을 이어서 처리한다. 예방을 위해 README의 공통 문단, 제출 인덱스 표, 요구 파일명은 동시에 여러 PR에서 수정하지 않고, 문서 구조 변경은 사전 이슈에서 합의한다.

## `reset`, `revert`, `stash` 차이

| 명령 | 용도 | 공유 브랜치 영향 | 사용 기준 |
| --- | --- | --- | --- |
| `git reset --soft HEAD~1` | 최근 로컬 커밋을 취소하고 변경은 유지 | push 전 로컬에서만 안전 | 커밋을 다시 나누거나 메시지 흐름을 정리할 때 |
| `git revert <SHA>` | 기존 커밋의 반대 변경을 새 커밋으로 생성 | 원격 히스토리를 유지 | 이미 push 또는 병합된 변경을 취소할 때 |
| `git stash push` | 커밋하지 않은 변경을 임시 보관 | 공유되지 않음 | 브랜치 전환 전 작업 트리를 비워야 할 때 |
| `git stash pop` | 임시 보관한 변경을 복원 | 충돌 가능 | 복원 후 반드시 `git status`와 테스트 확인 |

최근 커밋 메시지만 수정할 때는 `git commit --amend`를 사용한다. 단, 이미 원격에 공유된 커밋을 `amend`한 뒤 강제 푸시하면 다른 팀원의 히스토리와 어긋날 수 있으므로 push 전 로컬 커밋에만 사용한다.

트러블슈팅 4종 기록은 `docs/troubleshooting-log.md`에 있다. 각 기록은 참여자, 상황, 명령, 결과, 선택 이유를 포함한다.

`git commit --amend` 기록의 참여자는 김민서와 이지현이다. 김민서가 push 전 로컬 feature 브랜치에서 `docs: update`라는 모호한 커밋 메시지를 만들었고, 최근 커밋 메시지만 고치면 되는 상황이었다.

```bash
git log --oneline -1
git commit --amend -m "docs: add branch naming examples"
git log --oneline -1
```

변경 내용 자체를 되돌릴 필요가 없고 아직 원격에 공유하지 않았기 때문에 `amend`를 선택했다. push 뒤 같은 작업을 하면 다른 팀원의 로컬 히스토리와 어긋날 수 있으므로 push 전 로컬 커밋에만 적용한다.

`git reset --soft HEAD~1` 기록의 참여자는 이지현과 박서연이다. 이지현이 리뷰 규칙 문서와 충돌 기록 문서 변경을 한 커밋에 함께 담았고, 아직 push하지 않은 상태였다.

```bash
git log --oneline -1
git reset --soft HEAD~1
git status
git add docs/CONTRIBUTING.md
git commit -m "docs: add review rules"
git add docs/conflict-resolution.md
git commit -m "docs: add conflict resolution records"
```

최근 커밋은 취소됐지만 변경 파일은 유지되어 파일별로 다시 커밋할 수 있었다. 작업 내용을 유지하면서 커밋 경계만 다시 잡아야 했기 때문에 `--hard`나 `revert`가 아니라 `--soft`를 선택했다.

`git revert` 기록의 참여자는 박서연과 최준호다. 박서연의 PR이 병합된 뒤 `docs/troubleshooting-log.md`에서 `git stash pop` 설명이 빠진 것을 발견했다. 이미 `main`에 병합되어 팀원이 같은 히스토리를 기준으로 작업 중이었으므로 reset은 사용하지 않았다.

```bash
git log --oneline
git revert <잘못된_커밋_SHA>
git status
python3 -m unittest discover -s tests
git commit
```

기존 커밋을 삭제하지 않고 반대 변경을 새 커밋으로 남겼다. 원격 히스토리를 유지하므로 다른 팀원의 브랜치와 충돌할 가능성을 줄이고, 되돌림 자체도 PR 리뷰 대상으로 남길 수 있다.

`git stash`와 `git stash pop` 기록의 참여자는 최준호와 김민서다. 최준호가 `src/team_utils.py`를 수정하던 중 충돌 기록 PR을 확인해야 했고, 진행 중 변경은 아직 커밋하기 이른 상태였다.

```bash
git status
git stash push -m "wip team utils validation"
git status
git switch feature/park-seo-yeon-conflict-log
git switch feature/choi-jun-ho-troubleshooting
git stash pop
python3 -m unittest discover -s tests
```

작업 중 변경을 임시 보관한 뒤 다른 브랜치를 확인했고, 원래 브랜치로 돌아와 변경을 복원했다. `git stash pop`은 복원 과정에서 충돌이 날 수 있으므로 복원 직후 `git status`와 테스트를 확인한다. stash는 팀 공유 수단이 아니므로 장기 보관이나 인수인계에는 사용하지 않는다.

## rebase 사용 위험과 안전 수칙

`git rebase`는 feature 브랜치의 커밋을 최신 기준선 위에 다시 쌓아 히스토리를 직선에 가깝게 만든다. 개인 브랜치의 커밋 순서를 정리하거나, 리뷰 전 불필요한 중간 커밋을 squash할 때 유용하다.

위험은 기존 커밋의 SHA가 바뀐다는 점이다. 이미 다른 팀원이 기반으로 삼았거나 원격에 공유된 브랜치를 rebase한 뒤 강제 푸시하면, 팀원들의 로컬 브랜치가 서로 다른 히스토리를 보게 된다. 이 상태에서 병합하면 중복 커밋, 사라진 변경, 해결했던 충돌의 재발이 생길 수 있다.

안전 수칙은 다음과 같다.

1. `main`에서는 rebase하지 않는다.
2. 이미 병합된 브랜치나 다른 팀원이 작업 중인 공유 브랜치는 rebase하지 않는다.
3. 개인 feature 브랜치에서만 rebase를 사용하고, 사용 전 PR에 “히스토리 정리 예정”이라고 남긴다.
4. rebase 후에는 테스트와 `git log --oneline --graph --all`로 의도하지 않은 커밋 중복이 없는지 확인한다.
5. 원격에 올린 개인 브랜치에 rebase가 필요하면 팀 합의를 받고 `--force-with-lease`만 사용한다.
6. 충돌이 반복되면 rebase를 계속 밀어붙이지 말고 PR을 작게 나누거나 merge 방식으로 기준선을 맞춘다.

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
