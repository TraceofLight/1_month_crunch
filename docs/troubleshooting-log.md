# 트러블슈팅 기록

## 시나리오 1: `git commit --amend`

### 참여자

- 김민서: 최근 커밋 메시지 수정
- 이지현: 수정 전후 로그 확인

### 상황

김민서가 로컬 feature 브랜치에서 `docs: update`라는 모호한 커밋 메시지를 만들었다. 아직 원격에 push하지 않은 커밋이어서 히스토리 변경이 다른 팀원에게 영향을 주지 않는 상태였다.

### 시도한 명령

```bash
git log --oneline -1
git commit --amend -m "docs: add branch naming examples"
git log --oneline -1
```

### 결과

최근 커밋 메시지를 구체적인 subject로 수정했다. push 전 로컬 커밋에만 적용했기 때문에 공유 브랜치 히스토리는 바뀌지 않았다.

### 왜 이 방법을 선택했는가

최근 커밋 하나의 메시지만 고치면 되는 상황이었다. 변경 내용 자체를 되돌릴 필요가 없으므로 `reset`이나 `revert`보다 `amend`가 적합했다.

## 시나리오 2: `git reset --soft HEAD~1`

### 참여자

- 이지현: 잘못 묶인 로컬 커밋 취소
- 박서연: 변경 파일 분리 기준 검토

### 상황

이지현이 리뷰 규칙 문서와 충돌 기록 문서 변경을 한 커밋에 함께 담았다. 아직 원격에 push하지 않았고, 두 변경은 서로 다른 PR로 나누는 편이 리뷰하기 쉬웠다.

### 시도한 명령

```bash
git log --oneline -1
git reset --soft HEAD~1
git status
git add docs/CONTRIBUTING.md
git commit -m "docs: add review rules"
git add docs/conflict-resolution.md
git commit -m "docs: add conflict resolution records"
```

### 결과

최근 커밋은 취소됐지만 변경 파일은 staged 상태로 유지됐다. 이후 파일을 나누어 두 개의 의미 있는 커밋으로 다시 만들었다.

### 왜 이 방법을 선택했는가

작업 내용은 유지하면서 커밋 경계만 다시 잡아야 했다. `--hard`는 변경을 잃을 위험이 있고, `revert`는 이미 공유된 커밋을 취소할 때 쓰는 방법이므로 이 상황에는 맞지 않았다.

## 시나리오 3: `git revert`

### 참여자

- 박서연: 원격에 push된 잘못된 변경 되돌리기
- 최준호: 되돌림 PR 리뷰

### 상황

박서연의 PR이 병합된 뒤 `docs/troubleshooting-log.md`에서 요구 명령 중 `git stash pop` 설명이 빠진 것을 발견했다. 이미 `main`에 병합되고 팀원이 해당 커밋을 기준으로 작업 중이어서 히스토리 재작성은 위험했다.

### 시도한 명령

```bash
git log --oneline
git revert <잘못된_커밋_SHA>
git status
python3 -m unittest discover -s tests
git commit
```

### 결과

기존 커밋을 삭제하지 않고 반대 변경을 담은 새 커밋으로 되돌렸다. 원격 히스토리는 유지되어 다른 팀원의 로컬 브랜치와 충돌 가능성을 줄였다.

### 왜 이 방법을 선택했는가

이미 공유된 커밋을 취소해야 했으므로 `reset` 대신 `revert`를 선택했다. 공유 브랜치 안정성을 우선했고, 되돌림 자체도 PR 리뷰 대상으로 남길 수 있었다.

## 시나리오 4: `git stash`와 `git stash pop`

### 참여자

- 최준호: 진행 중 작업 임시 보관
- 김민서: stash 복원 후 테스트 확인

### 상황

최준호가 `src/team_utils.py`를 수정하던 중 급하게 충돌 기록 PR을 확인해야 했다. 작업 중인 변경은 아직 커밋하기 이르렀고, 브랜치를 전환하려면 작업 트리를 깨끗하게 만들어야 했다.

### 시도한 명령

```bash
git status
git stash push -m "wip team utils validation"
git status
git switch feature/park-seo-yeon-conflict-log
git switch feature/choi-jun-ho-troubleshooting
git stash pop
python3 -m unittest discover -s tests
```

### 결과

작업 중 변경을 임시 보관한 뒤 다른 브랜치를 확인했고, 원래 브랜치로 돌아와 변경을 복원했다. `git stash pop` 후에는 충돌 여부와 테스트 결과를 반드시 확인했다.

### 왜 이 방법을 선택했는가

미완성 변경을 커밋으로 남기지 않고도 브랜치를 전환해야 했다. stash는 임시 보관에 적합하지만, 팀 공유 수단이 아니므로 장기 보관이나 다른 팀원 전달에는 사용하지 않는다.
