# Mini Git 구축

## 개요

이 프로젝트는 커밋 메타데이터만 추적하는 CLI 기반 Mini Git이다. 파일 내용 추적, 네트워크 통신, 영속 저장은 구현하지 않고, 메모리 안에서 저장소 초기화, 브랜치 생성과 전환, 커밋 생성, 로그 출력, 경로 탐색, 조상 탐색, 역색인 검색, 직접 구현한 정렬을 제공한다.

엔트리 포인트는 `main.py`이다. 대화형 실행은 `python3 main.py`로 시작하며 프롬프트는 `mini-git>`이다. `exit` 또는 `quit`를 입력하면 종료된다.

## 파일 구성

| 경로 | 역할 |
| --- | --- |
| `main.py` | Mini Git REPL, 명령 파서, 커밋 그래프, 브랜치, 역색인, 탐색, 병합 정렬 구현 |
| `scripts/run.py` | 대표 시나리오를 한 번에 실행하고 `evidence/demo_run.txt`를 생성 |
| `tests/test_mini_git.py` | 핵심 요구사항 회귀 테스트 |
| `requirements.txt` | 테스트 의존성 고정. `pytest==8.3.5` |
| `Dockerfile` | `ubuntu:24.04` 기반 재현 환경 |
| `evidence/test_results.txt` | 컨테이너에서 실행한 테스트 결과 |
| `evidence/demo_run.txt` | 컨테이너에서 생성한 CLI 시나리오 입출력 |
| `evidence/run_script_stdout.txt` | evidence 생성 스크립트의 표준 출력 |
| `evidence/repl_smoke.txt` | 실제 REPL에 파이프 입력을 넣어 확인한 결과 |

## 실행 방법

Docker 기반 실행을 기준으로 한다.

```bash
docker build -t codyssey-cli-test-mini-git .
docker run --rm --name codyssey-cli-test-repl -it -v ${PWD}:/workspace -w /workspace codyssey-cli-test-mini-git python3 main.py
```

Windows PowerShell에서는 위 명령의 `${PWD}`가 현재 저장소 경로로 동작한다. POSIX 셸에서는 필요하면 `$(pwd)`로 바꿔 실행한다.

대표 시나리오와 evidence 파일 생성은 다음 명령으로 실행한다.

```bash
docker run --rm --name codyssey-cli-test-demo -v ${PWD}:/workspace -w /workspace codyssey-cli-test-mini-git python3 scripts/run.py
```

테스트는 다음 명령으로 실행한다.

```bash
docker run --rm --name codyssey-cli-test-pytest -v ${PWD}:/workspace -w /workspace codyssey-cli-test-mini-git python3 -m pytest -q
```

로컬 Python 환경에서 직접 실행할 때는 Python 3.10 이상이 필요하다.

```bash
python main.py
```

## CLI 문법

명령어는 대소문자를 구분하지 않는다. `INIT`, `init`, `CoMmIt` 모두 같은 명령으로 처리된다. 공백이 포함된 사용자명, 커밋 메시지, 검색 인자는 따옴표로 감싼다.

지원 명령은 다음과 같다.

| 명령 | 동작 |
| --- | --- |
| `INIT <user_name>` | 저장소를 초기화하고 `main` 브랜치와 현재 author를 설정 |
| `BRANCH <branch_name>` | 현재 브랜치 HEAD를 가리키는 새 브랜치 생성 |
| `SWITCH <branch_name>` | 현재 브랜치를 지정 브랜치로 전환 |
| `COMMIT <message>` | 현재 HEAD를 부모로 하는 새 커밋 생성 |
| `LOG` | 부모가 자식보다 먼저 나오도록 로그 출력 |
| `LOG --sort-by=date` | timestamp 기준 오름차순 로그 출력 |
| `LOG --sort-by=author` | author 이름 기준 오름차순 로그 출력 |
| `PATH <commit1> <commit2>` | 커밋-부모 연결을 무방향 간선으로 본 최단 경로 출력 |
| `ANCESTORS <commit_hash>` | 지정 커밋의 모든 조상 출력 |
| `SEARCH <keyword>` | 메시지 토큰 역색인에서 키워드 검색 |
| `SEARCH --author=<name>` | author 역색인에서 작성자 검색 |

대표 오류 메시지는 `Invalid args`, `Unknown branch: <name>`, `Unknown commit: <hash>`, `Repository not initialized`이다.

## 실행 예시

아래 입출력은 `evidence/demo_run.txt`에 저장된 컨테이너 실행 결과와 같은 시나리오이다.

```text
mini-git> init "Alice Kim"
Initialized repository.
Current branch: main
Current user: Alice Kim

mini-git> commit "Initial commit"
[main c000001] Initial commit

mini-git> branch feature
Created branch: feature

mini-git> switch feature
Switched to branch: feature

mini-git> commit "Add login feature"
[feature c000002] Add login feature

mini-git> switch main
Switched to branch: main

mini-git> commit "Add payment feature"
[main c000003] Add payment feature

mini-git> path c000002 c000003
Path: c000002 -> c000001 -> c000003

mini-git> search login
Found 1 commit:
- c000002: Add login feature
```

## 자료구조 설계

커밋 노드는 `Commit` 데이터 클래스로 표현한다. 필드는 `hash`, `message`, `author`, `timestamp`, `parents`이다. 저장소는 `commit_hash -> Commit` 형태의 해시맵인 `self.commits`를 사용하므로 커밋 해시 조회는 평균적으로 O(1)에 가깝다.

브랜치는 `branch_name -> head_commit_hash` 해시맵인 `self.branches`로 관리한다. 아직 커밋이 없는 `main` 브랜치는 HEAD가 `None`이다. `BRANCH`는 현재 브랜치의 HEAD 값을 복사하고, `SWITCH`는 현재 브랜치 이름만 바꾼다. `COMMIT`은 새 커밋을 만든 뒤 현재 브랜치의 HEAD를 새 커밋 해시로 이동한다.

커밋 해시는 세션 카운터 기반으로 `c000001`, `c000002`처럼 생성한다. 카운터를 증가시킨 뒤 이미 존재하는 해시인지 한 번 더 확인하므로 세션 내 중복이 발생하지 않는다. 난수 해시보다 Git의 실제 해시와는 덜 비슷하지만, 학습용 CLI에서 재현 가능한 테스트와 출력 확인이 쉽다는 장점이 있다.

## 커밋 그래프와 DAG

커밋 그래프의 방향은 자식 커밋에서 부모 커밋으로 향한다. 최초 커밋은 부모가 0개이고, 일반 커밋은 현재 HEAD 하나를 부모로 가진다. 구현 함수 `create_commit`은 새 커밋을 만들 때 이미 존재하는 부모 해시만 복사하고, 기존 커밋의 부모 목록을 수정하지 않는다. 새 노드가 과거 노드만 가리키는 방식이므로 새 간선이 미래 커밋을 향할 수 없고 순환이 생기지 않는다.

이 구조는 방향성 비순환 그래프, 즉 DAG이다. Git의 커밋도 같은 이유로 DAG이다. 커밋은 과거 스냅샷을 부모로 참조하고, 이미 만들어진 커밋의 부모를 바꾸지 않는 불변 객체처럼 다뤄진다. 따라서 특정 커밋에서 부모 방향으로 계속 이동하면 언젠가 부모가 없는 루트 커밋에 도달한다.

## 로그 출력

`LOG`는 최신순 나열이 아니라 부모가 항상 자식보다 먼저 나오도록 출력한다. 구현은 DFS를 사용한다. 각 커밋을 방문할 때 먼저 부모 커밋을 재귀 방문하고, 그 다음 현재 커밋을 결과에 추가한다. 방문 집합으로 중복 출력을 막는다.

이 출력은 위상 정렬의 성격을 가진다. 모든 간선이 자식에서 부모로 향한다고 보면, 부모를 먼저 출력하는 순서는 의존 대상이 먼저 나오는 순서다. 시간복잡도는 커밋 수를 V, 부모 간선 수를 E라고 할 때 O(V + E)이다.

`LOG --sort-by=date`와 `LOG --sort-by=author`는 위상 순서가 아니라 지정 기준 정렬 결과를 보여 준다. 날짜 정렬은 timestamp 오름차순이고, author 정렬은 작성자 이름 오름차순이다. 동률일 때는 timestamp와 hash를 보조 기준으로 사용해 출력이 흔들리지 않게 했다.

## 정렬 알고리즘

Python 표준 정렬 API인 `sorted()`와 `list.sort()`는 사용하지 않았다. `main.py`에는 직접 구현한 안정 병합 정렬 `merge_sort`가 있다. 비교 함수만 바꿔 날짜 기준과 author 기준을 모두 처리한다.

병합 정렬은 입력을 절반으로 나누고, 각 절반을 재귀적으로 정렬한 뒤, 두 정렬 구간을 하나로 병합한다. 평균 시간복잡도와 최악 시간복잡도는 모두 O(n log n)이다. 병합 단계에서 두 값이 같으면 왼쪽 원소를 먼저 선택하므로 안정 정렬이다. 추가 리스트를 만들기 때문에 공간복잡도는 O(n)이다.

## 역색인

검색은 전체 커밋 순회를 기본 전략으로 삼지 않는다. 커밋을 생성할 때 두 가지 역색인을 함께 갱신한다.

| 인덱스 | 키 | 값 |
| --- | --- | --- |
| `keyword_index` | 커밋 메시지를 공백으로 나누고 소문자로 바꾼 토큰 | 해당 토큰을 포함한 커밋 해시 목록 |
| `author_index` | author 이름 | 해당 author가 작성한 커밋 해시 목록 |

`SEARCH login`은 `keyword_index["login"]`에서 후보 커밋 해시 목록을 바로 가져온다. `SEARCH --author="Alice Kim"`은 `author_index["Alice Kim"]`에서 후보를 가져온다. 커밋 수가 n이고 메시지 평균 토큰 수가 m일 때, 전체 순회 검색은 O(nm)에 가깝다. 역색인은 검색어 키 조회 후 결과 개수 r만큼 출력하므로 평균적으로 O(1 + r)에 가깝다. 인덱스 갱신 비용은 커밋 생성 시 메시지 토큰 수만큼 추가된다.

## 경로 탐색

`PATH <commit1> <commit2>`는 커밋-부모 연결을 무방향 간선으로 바꿔 생각한다. 구현은 먼저 모든 커밋의 부모 관계에서 무방향 인접 리스트를 만든다. 그 다음 BFS로 시작 커밋에서 목표 커밋까지의 최단 경로를 찾는다.

BFS는 간선 수가 가장 적은 경로를 먼저 발견하는 탐색이다. 최단 경로가 여러 개일 수 있으므로, 같은 깊이의 후보 경로를 더 살펴보고 `hash1->hash2->...` 문자열 기준으로 사전순이 가장 작은 경로를 선택한다. 기본 탐색 비용은 O(V + E)이고, 같은 길이 후보가 많을 때는 후보 경로 문자열 비교 비용이 추가된다.

간선 정의가 바뀌면 알고리즘의 의미도 바뀐다. 현재처럼 부모 연결을 무방향으로 보면 서로 다른 브랜치의 형제 커밋도 공통 조상을 거쳐 연결될 수 있다. 반대로 간선을 자식에서 부모로 향하는 방향 간선으로만 보면 최신 커밋에서 과거 커밋으로 가는 경로는 가능하지만, 과거 커밋에서 자식 커밋으로 가는 경로는 없다. 부모에서 자식으로만 이동하도록 정의하면 조상에서 후손을 찾는 탐색이 되고, 자식 인접 리스트를 별도로 유지해야 빠르게 탐색할 수 있다. merge commit처럼 부모가 2개인 커밋을 추가하더라도 BFS 자체는 그대로 사용할 수 있지만, 인접 리스트 구성 단계에서 두 부모 간선을 모두 반영해야 한다.

## 조상 탐색

`ANCESTORS <commit_hash>`는 지정 커밋의 부모 방향으로 도달 가능한 모든 커밋을 출력한다. 구현은 스택 기반 DFS 형태로 부모를 따라가며 방문 집합으로 중복을 제거한다. 특정 커밋의 조상 수를 A, 조상 사이의 부모 간선을 E_A라고 하면 시간복잡도는 O(A + E_A)이다.

## 성장 시 병목과 개선 방향

커밋 수가 작을 때는 모든 로그와 탐색이 즉시 끝난다. 커밋이 수십만 개 이상으로 늘어나면 병목은 세 곳에서 먼저 나타난다.

첫째, `LOG`는 전체 커밋을 한 번씩 방문하므로 O(V + E) 비용이 든다. 자주 호출되는 환경이라면 브랜치별 위상 순서 캐시를 두고 새 커밋이 추가된 부분만 갱신할 수 있다. 다만 캐시는 메모리를 더 쓰고, branch 이동이나 merge commit이 추가될 때 무효화 규칙을 정확히 관리해야 한다.

둘째, `PATH`는 호출할 때마다 무방향 인접 리스트를 다시 만든다. 현재 구현은 단순하고 이해하기 쉽지만, 커밋이 많고 경로 조회가 잦으면 인접 리스트 생성 비용이 반복된다. 개선하려면 커밋 생성 시 부모와 자식 양방향 인덱스를 함께 갱신하고, `PATH`에서는 이미 만들어진 인접 리스트를 사용한다.

셋째, `SEARCH`는 조회 자체는 빠르지만 커밋 생성 시 메시지 토큰 수만큼 인덱스를 갱신한다. 메시지가 길거나 토큰 종류가 많아지면 인덱스 메모리가 커진다. 실제 서비스라면 토큰 정규화 규칙, 불용어 제거, posting list 압축, 결과 페이지네이션을 추가해 메모리와 출력 비용을 줄인다.

## 요구 변경 시 설계 대응

`LOG --sort-by=author` 요구가 작성자 이름 오름차순을 넘어, 같은 작성자의 커밋은 부모가 자식보다 먼저 나오고 작성자 비교는 대소문자를 무시해야 한다는 식으로 강화될 수 있다. 이 경우 비교 함수만 단순히 바꾸면 부모 우선 제약이 깨질 수 있다. 해결 전략은 먼저 DAG 위상 순서를 계산하고, author를 1차 그룹 키로 사용하되 같은 그룹 안에서는 위상 순서 인덱스를 보조 키로 쓰는 방식이다. 여러 작성자가 섞인 부모-자식 관계까지 전역으로 보존해야 한다면 정렬 문제가 아니라 제약 조건이 있는 위상 정렬 문제가 되므로, author 우선순위를 가진 Kahn 알고리즘 형태로 바꿔야 한다.

해시 생성 방식을 카운터에서 난수 또는 실제 해시 함수 기반으로 바꾸면 테스트와 디버깅 방식도 달라진다. 카운터 해시는 `c000001`처럼 예측 가능하므로 테스트가 정확한 문자열을 비교할 수 있고 evidence 재현도 쉽다. 난수 해시는 실제 분산 시스템의 식별자에 더 가깝지만, 테스트에서는 난수 시드를 고정하거나 해시 패턴만 검증해야 한다. 메시지, author, timestamp, parents를 입력으로 한 해시 함수는 Git의 개념에 더 가깝지만 timestamp가 달라지면 같은 시나리오에서도 해시가 바뀐다. 재현성을 유지하려면 테스트용 clock을 고정하고, 충돌 발생 시 재시도 또는 카운터 보조값을 붙이는 정책을 문서화해야 한다.

## 범위와 위협 모델

이 프로그램은 학습용 메모리 CLI이다. 파일 시스템 상태를 커밋하지 않고, 외부 네트워크 통신도 하지 않는다. 데이터는 프로세스가 종료되면 사라진다. 따라서 실제 Git 저장소 보호, 접근 제어, 충돌 해결, 원격 동기화, 파일 무결성 검증은 범위에 포함하지 않았다.

입력은 사용자가 REPL에 직접 입력하는 명령 문자열이다. 파싱은 Python `shlex.split`으로 수행해 따옴표가 있는 인자를 하나의 값으로 처리한다. 잘못 닫힌 따옴표나 인자 수가 맞지 않는 명령은 오류 메시지로 처리한다. 커밋 메시지와 author는 셸 명령으로 재실행하지 않으므로 명령 삽입 위험을 만들지 않는다.

## 검증 결과

검증은 `ubuntu:24.04` 기반 Docker 컨테이너에서 수행했다. 이미지 이름과 컨테이너 이름은 `codyssey-cli-test` 접두사를 사용했다.

테스트 로그는 `evidence/test_results.txt`에 저장했다.

```text
.......                                                                  [100%]
7 passed in 0.16s
```

대표 시나리오 실행 로그는 `evidence/demo_run.txt`에 저장했다. 해당 로그는 `INIT`, `COMMIT`, `BRANCH`, `SWITCH`, `LOG`, `PATH`, `ANCESTORS`, `SEARCH`, `LOG --sort-by=author`, `LOG --sort-by=date`를 포함한다.

evidence 생성 스크립트의 표준 출력은 `evidence/run_script_stdout.txt`에 저장했다.

```text
Wrote evidence/demo_run.txt
```

REPL 동작 확인은 `evidence/repl_smoke.txt`에 저장했다.

```text
mini-git> Initialized repository.
Current branch: main
Current user: Alice
mini-git> [main c000001] Smoke test
mini-git>
```

## 문제 해결

`pytest -q`에서 `ModuleNotFoundError: No module named 'main'`이 발생하면 `python3 -m pytest -q`로 실행한다. 컨테이너의 pytest 진입점이 현재 작업 디렉터리를 import 경로에 넣지 않는 경우가 있어, Python 모듈 실행 방식이 더 안정적이다.

`Repository not initialized`가 출력되면 먼저 `INIT <user_name>`을 실행한다. 이 프로그램은 `INIT` 이전에는 브랜치와 현재 author가 없기 때문에 커밋, 브랜치 생성, 전환을 수행하지 않는다.

`LOG`, `PATH`, `ANCESTORS`, `SEARCH`도 `INIT` 이전에는 `Repository not initialized`를 출력한다. 조회 명령도 커밋 저장소, 브랜치 HEAD, 역색인 상태를 기준으로 동작하므로 초기화된 저장소 상태가 필요하다.

`Unknown branch: <name>`이 출력되면 `BRANCH <branch_name>`으로 생성한 이름인지 확인한다. 브랜치 이름은 입력한 문자열을 그대로 사용하므로 대소문자 차이가 있으면 다른 브랜치로 취급한다.

`Unknown commit: <hash>`가 출력되면 `LOG`로 현재 세션의 커밋 해시를 확인한다. 커밋 해시는 메모리에만 존재하므로 프로그램을 다시 시작하면 이전 해시는 사라진다.

공백이 포함된 메시지나 이름이 `Invalid args`로 처리되면 따옴표를 확인한다. 예를 들어 `COMMIT "Add login feature"`와 `SEARCH --author="Alice Kim"`처럼 입력한다.
