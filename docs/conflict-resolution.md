# 충돌 해결 기록

## 충돌 기록 1

### 참여자

- 작성자: 김민서
- 상대: 이지현
- 리뷰어: 박서연

### 상황

김민서의 `feature/kim-min-seo-math-utils` 브랜치와 이지현의 `feature/lee-ji-hyun-review-guide` 브랜치가 `README.md`의 결과물 설명 hunk를 서로 다르게 수정했다. 두 브랜치가 같은 문단의 인접 라인을 바꿨기 때문에 머지 중 비자명 충돌이 발생했다.

### 충돌 내용

```txt
<<<<<<< HEAD
간단한 결과물은 팀원별 유틸 함수 모음으로 구성한다.
=======
간단한 결과물은 협업 규칙 검증에 사용할 Python 유틸 함수 모음으로 구성한다.
>>>>>>> feature/lee-ji-hyun-review-guide
```

### 해결 과정

두 변경 모두 의미가 있었으므로 한쪽을 버리지 않고 문장을 합쳤다. 결과 문장은 선택한 산출물이 유틸 함수 모음이며, 해당 함수가 협업 규칙 검증에도 쓰인다는 점을 함께 담았다.

실행 절차는 다음과 같다.

```bash
git status
git diff
python3 -m unittest discover -s tests
git add README.md
git commit -m "docs: resolve utility deliverable wording conflict"
```

### 결과

최종 문구는 “간단한 결과물은 팀원별 Python 유틸 함수 모음이며, 브랜치 이름, 커밋 메시지, PR 본문, 충돌 마커 검증에 사용한다.”로 정리했다. 테스트를 다시 실행해 문서 변경이 코드 검증 흐름을 깨지 않는지 확인했다.

### 배운 점

README의 핵심 설명은 여러 PR이 동시에 수정하기 쉬운 영역이다. 문서 PR도 코드 PR처럼 작업 범위를 작게 나누고, 병합 전 최신 `main` 기준으로 다시 확인해야 한다.

## 충돌 기록 2

### 참여자

- 작성자: 박서연
- 상대: 최준호
- 리뷰어: 김민서

### 상황

박서연은 트러블슈팅 기록 파일 이름을 `docs/troubleshooting-log.md`로 유지하며 내용을 수정했다. 최준호는 같은 시점에 문서 구조를 정리하면서 파일을 `docs/git-troubleshooting.md`로 이동하려고 했다. 한쪽은 파일 이동, 다른 한쪽은 내용 수정을 수행했기 때문에 머지 과정에서 위치와 내용이 동시에 충돌했다.

### 충돌 내용

```txt
CONFLICT (modify/delete): docs/troubleshooting-log.md deleted in feature/choi-jun-ho-doc-rename and modified in HEAD.
```

### 해결 과정

과제 요구 파일명이 `docs/troubleshooting-log.md`이므로 파일 이동은 취소하고 요구 파일명을 유지했다. 최준호의 구조 개선 문구 중 필요한 부분만 기존 파일에 반영했다.

실행 절차는 다음과 같다.

```bash
git status
git checkout --ours docs/troubleshooting-log.md
git diff
python3 -m unittest discover -s tests
git add docs/troubleshooting-log.md
git commit -m "docs: keep required troubleshooting log path"
```

### 결과

요구 파일명은 유지했고, 트러블슈팅 시나리오 4개와 팀원 참여 기록을 한 파일에서 확인할 수 있게 정리했다.

### 배운 점

과제나 운영에서 파일 경로가 외부 계약인 경우 임의 이동은 충돌보다 큰 검증 실패를 만들 수 있다. 경로 변경 PR은 작성 전에 팀 합의와 요구사항 확인이 필요하다.
