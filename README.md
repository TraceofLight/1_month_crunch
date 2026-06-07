# Mini Redis 구축

## 개요

이 저장소는 CLI 기반 Mini Redis 구현체다. 네트워크 서버나 영속 저장소 없이 사용자가 `mini-redis>` 프롬프트에 명령을 입력하면 즉시 결과를 반환한다. 지원 명령은 문자열 저장 명령 6개, 메모리 관리 명령 2개, TTL 관리 명령 2개다.

구현 목표는 Redis의 핵심 동작을 작은 범위에서 직접 확인하는 것이다. 키-값 저장소는 Python `dict`, `set`, `collections`로 대체하지 않고 직접 구현한 해시맵을 사용한다. LRU 추적은 이중 연결 리스트와 해시맵을 조합한다. TTL 만료 관리는 최소 힙으로 가장 빠른 만료 후보를 먼저 확인한다.

## 아키텍처와 파일 구성

| 경로 | 역할 |
| --- | --- |
| `mini_redis/core.py` | 명령 실행기, 메모리 계산, LRU 제거, TTL 처리 |
| `mini_redis/cli.py` | `mini-redis>` REPL |
| `mini_redis/datastructures/doubly_linked_list.py` | 이중 연결 리스트 |
| `mini_redis/datastructures/hash_map.py` | 체이닝 해시맵 |
| `mini_redis/datastructures/min_heap.py` | 최소 힙 |
| `mini_redis/datastructures/dynamic_array.py` | 2배 확장 동적 배열 |
| `scripts/run.py` | CLI 실행 진입점 |
| `scripts/demo.py` | 요구사항 시나리오 비대화형 데모 |
| `tests/` | 기능, 자료구조, 제약 조건, 실행 스크립트 테스트 |
| `evidence/` | Docker 빌드, 테스트, 데모 실행 증거 |

`MiniRedis.execute`는 한 줄을 파싱한 뒤 명령어를 대문자로 정규화하고 전용 처리 함수로 보낸다. 잘못된 명령은 `(error) ERR unknown command '<cmd>'` 형식으로 반환한다.

키 기반 명령은 처리 전에 해당 키의 만료 여부를 확인한다. 만료된 키는 데이터, TTL, LRU 구조에서 함께 제거한 뒤 없는 키처럼 처리한다.

`DBSIZE`, `KEYS`, `INFO memory`처럼 전체 상태를 보는 명령은 힙 루트부터 현재 시각 이전에 만료된 키를 정리한 뒤 결과를 만든다.

## 실행 환경과 재현

요구 환경은 Python 3.8 이상이다. 재현 환경은 `ubuntu:24.04` 기반 Docker 이미지로 고정했다. Python 패키지는 `requirements.txt`에 버전을 고정했다.

사용한 외부 Python 패키지는 테스트 실행용 `pytest==8.2.2`뿐이다. Mini Redis 런타임은 Python 표준 라이브러리만 사용한다.

이미지 이름과 컨테이너 이름은 `codyssey-cli-test` 접두사를 사용한다.

PowerShell:

```powershell
docker build -t codyssey-cli-test-mini-redis .
docker run --rm -it --name codyssey-cli-test-mini-redis-repl -v "${PWD}:/app" -w /app codyssey-cli-test-mini-redis python scripts/run.py
```

bash:

```bash
docker build -t codyssey-cli-test-mini-redis .
docker run --rm -it --name codyssey-cli-test-mini-redis-repl -v "$PWD:/app" -w /app codyssey-cli-test-mini-redis python scripts/run.py
```

테스트 실행:

```bash
docker run --rm --name codyssey-cli-test-mini-redis-test -v "$PWD:/app" -w /app codyssey-cli-test-mini-redis python -m pytest -q
```

데모 실행:

```bash
docker run --rm --name codyssey-cli-test-mini-redis-demo -v "$PWD:/app" -w /app codyssey-cli-test-mini-redis python scripts/demo.py
```

## CLI와 명령

REPL은 `mini-redis>` 프롬프트를 출력하고 사용자 입력을 반복해서 파싱, 실행, 출력한다. 종료 명령은 `exit` 또는 `quit`이다.

값 파싱은 Python 표준 `shlex.split`을 사용한다. 공백 없는 값과 큰따옴표로 감싼 값을 지원한다. 예를 들어 `SET user:1 "Alice"`는 값 `Alice`를 저장한다. 따옴표가 닫히지 않은 입력은 문법 오류로 처리한다.

| 명령 | 동작 |
| --- | --- |
| `SET key value` | 키에 문자열 값을 저장하고 성공 시 `OK` 반환 |
| `GET key` | 값이 있으면 `"value"`, 없거나 만료되었으면 `(nil)` 반환 |
| `DEL key` | 삭제 성공 시 `(integer) 1`, 없으면 `(integer) 0` 반환 |
| `EXISTS key` | 키가 있으면 `(integer) 1`, 없으면 `(integer) 0` 반환 |
| `DBSIZE` | 현재 키 개수를 `(integer) N`으로 반환 |
| `KEYS` | 전체 키 목록을 배열 형태로 반환 |
| `CONFIG SET maxmemory bytes` | 논리 메모리 제한을 바이트 단위로 설정 |
| `INFO memory` | `used_memory`, `maxmemory`, `evicted_keys` 출력 |
| `EXPIRE key seconds` | 키 만료 시간을 초 단위로 설정 |
| `TTL key` | 남은 만료 시간을 Redis 규칙에 맞춰 반환 |

## 자료구조

### 해시맵

`HashMap`은 버킷 배열과 체이닝 방식으로 충돌을 해결한다. 각 버킷은 재사용한 `DoublyLinkedList`다. 엔트리는 `Entry(key, value)`로 저장한다.

해시 함수는 FNV 계열 아이디어를 단순화한 방식이다. 초기값 `2166136261`에서 각 문자의 코드와 XOR을 수행하고 `16777619`를 곱한 뒤 32비트 범위로 줄인다. 최종 해시를 버킷 수로 나눈 나머지가 버킷 인덱스다.

로드 팩터가 0.75를 초과할 예정이면 버킷 수를 2배로 늘리고 기존 엔트리를 다시 배치한다. 평균적으로 `put`, `get`, `remove`, `contains`는 O(1)에 가깝고, 최악의 경우 한 버킷에 몰린 체인을 순회하므로 O(n)이다.

### 이중 연결 리스트와 LRU

`Node`는 `prev`, `next`, `data` 필드를 가진다. `DoublyLinkedList`는 `head`, `tail`, `_size`를 유지한다.

구현한 메서드는 `insert_front`, `insert_back`, `remove_front`, `remove_back`, `remove_node`, `move_to_front`다. 노드 참조를 알고 있는 경우 삽입, 삭제, 이동은 모두 포인터 몇 개만 바꾸므로 O(1)이다.

LRU에서는 리스트 앞쪽이 가장 최근 사용 키, 뒤쪽이 가장 오래 사용되지 않은 키다. 새 키는 LRU 리스트 앞에 삽입한다. 기존 키를 덮어쓰면 이전 노드 참조를 해시맵에서 찾아 리스트 앞쪽으로 이동한다. `GET`도 값 반환에 성공한 경우에만 같은 방식으로 LRU를 갱신한다. 만료로 삭제된 키는 `GET`에서 `(nil)`을 반환하며 LRU를 갱신하지 않는다.

### 최소 힙과 TTL

`MinHeap`은 내부 저장소로 직접 구현한 `DynamicArray`를 사용한다. `push`, `pop`, `peek`, `size`를 제공하고 `_heapify_up`, `_heapify_down`으로 힙 속성을 유지한다.

TTL에는 `(expire_at, key)` 튜플을 넣는다. Python 튜플 비교는 첫 번째 값부터 비교하므로 가장 빠른 만료 시간이 루트에 놓인다. 만료 시간이 갱신되면 이전 튜플을 힙에서 즉시 제거하지 않고 새 튜플을 추가한다. 실제 제거 시점에는 `ttl` 해시맵에 저장된 최신 `expire_at`과 힙에서 꺼낸 `expire_at`이 같은지 확인한다. 이 지연 삭제 전략은 힙 내부 임의 삭제를 피하고, 가장 빠른 만료 후보를 빠르게 확인한다.

`EXPIRE key seconds`는 키가 없으면 `(integer) 0`을 반환한다. `seconds`가 0 이하이면 즉시 만료로 처리해 키를 삭제하고 `(integer) 1`을 반환한다. 정상 설정 시 현재 시각에 초를 더한 `expire_at`을 TTL 해시맵에 저장하고 최소 힙에도 `(expire_at, key)`를 추가한다.

`TTL key`는 키가 없으면 `(integer) -2`, 키는 있지만 만료 시간이 없으면 `(integer) -1`, 만료 시간이 있으면 남은 초를 `(integer) N`으로 반환한다.

`SET`이 기존 키를 덮어쓰면 TTL은 초기화된다. `DEL`은 데이터, TTL, LRU 구조의 엔트리를 함께 제거한다.

### 동적 배열

보너스 범위인 동적 배열도 구현했다. `DynamicArray`는 `append`, `get`, `set`, `remove`, `pop`, `capacity`를 제공한다. 공간이 가득 차면 내부 고정 배열을 2배로 늘린다. 최소 힙의 내부 저장소에 이 배열을 적용했다.

## 메모리 관리와 제거 정책

논리 메모리 공식은 다음과 같다.

```text
used_memory = Σ( len(utf8(key)) + len(utf8(value)) )
```

노드, 포인터, 버킷 배열 같은 자료구조 오버헤드는 계산하지 않는다.

`maxmemory`가 0이면 제한이 없다. `maxmemory > 0`이고 `SET` 이후 `used_memory`가 제한을 넘으면 LRU 리스트 뒤쪽부터 키를 제거한다. 제거할 때 데이터 해시맵, TTL 해시맵, LRU 노드 해시맵을 함께 정리하고 `evicted_keys`를 1씩 증가시킨다. `used_memory <= maxmemory`가 될 때까지 이 과정을 반복한다.

단일 엔트리의 `len(utf8(key)) + len(utf8(value))`가 `maxmemory`보다 크면 저장하지 않고 다음 오류를 반환한다.

```text
(error) OOM command not allowed when used_memory > 'maxmemory'
```

`INFO memory`는 최소한 `used_memory`, `maxmemory`, `evicted_keys`를 출력한다. `used_memory`는 전체 재계산이 아니라 명령 처리 중 증감분으로 관리한다.

## 에러 처리

출력은 Redis 스타일을 따른다. 정상 저장은 `OK`, 없는 값은 `(nil)`, 정수 결과는 `(integer) N`, 오류는 `(error) ...` 형식이다.

| 상황 | 출력 |
| --- | --- |
| 알 수 없는 명령 | `(error) ERR unknown command '<cmd>'` |
| 인자 개수 오류 | `(error) ERR wrong number of arguments for '<cmd>' command` |
| 정수 파싱 실패 | `(error) ERR value is not an integer or out of range` |
| 메모리 초과 | `(error) OOM command not allowed when used_memory > 'maxmemory'` |
| 따옴표 파싱 오류 | `(error) ERR syntax error` |

## 모니터링과 검증

검증은 모두 Docker 컨테이너 안에서 실행했다.

| 파일 | 내용 |
| --- | --- |
| `evidence/docker-build.log` | `docker build -t codyssey-cli-test-mini-redis .` 실행 로그 |
| `evidence/pytest.log` | `python -m pytest -q` 실행 로그 |
| `evidence/demo.log` | `python scripts/demo.py` 실행 로그 |

최종 테스트 결과:

```text
11 passed
```

데모 로그에는 메모리 제한 30바이트에서 `user:1`이 LRU로 제거되고, `user:2`가 TTL 만료 후 `(nil)`과 `(integer) -2`로 처리되는 흐름이 포함되어 있다. 오류 출력 예시인 정수 파싱 실패, 인자 개수 오류, 알 수 없는 명령도 같은 로그에 포함되어 있다.

`tests/test_constraints.py`는 프로덕션 코드의 AST를 검사해 `dict`, `set`, `collections`가 저장소 대체 수단으로 들어오지 않았는지 확인한다.

## 보안과 범위

이 구현은 로컬 학습용 CLI다. 네트워크 포트를 열지 않고, 외부 요청을 받지 않으며, 파일에 데이터를 저장하지 않는다. 따라서 원격 공격, 인증, 권한 분리, TLS, 데이터 영속성 보안은 범위 밖이다.

입력은 같은 터미널 사용자가 직접 제공한다고 가정한다. 값은 문자열로 저장되며 명령 파싱에는 `shlex.split`을 사용한다.

`maxmemory`는 과제 공식에 따른 논리 메모리 제한이다. Python 객체 자체의 실제 프로세스 메모리 사용량을 제한하지 않는다. 매우 큰 한 줄 입력은 파싱 과정에서 실제 메모리를 사용할 수 있으므로 운영용 Redis 대체재로 사용할 수 없다.

멀티스레딩과 락은 구현하지 않았다. 한 REPL에서 명령을 순차 실행하는 모델만 지원한다.

## 성능과 확장

LRU 대신 LFU 정책을 구현하려면 사용 시각 중심의 단일 이중 연결 리스트만으로는 부족하다. 각 키마다 사용 횟수 `frequency`를 저장하고, 같은 사용 횟수를 가진 키들을 별도의 이중 연결 리스트로 묶어야 한다. 전체 구조는 키에서 값, 사용 횟수, 현재 리스트 노드를 찾는 해시맵과, 사용 횟수에서 해당 빈도 버킷의 이중 연결 리스트를 찾는 해시맵으로 나눌 수 있다. `GET`이 성공하거나 `SET`이 기존 키를 갱신하면 현재 빈도 리스트에서 노드를 O(1)로 제거하고 `frequency + 1` 리스트의 앞쪽에 삽입한다. 제거 대상은 가장 작은 빈도 `min_frequency`의 리스트 뒤쪽에 있는 키다. 이 방식은 빈도 증가, 노드 이동, LFU 제거를 평균 O(1)에 처리한다. 메모리 제한, TTL 삭제, `DEL`은 기존 LRU 구현과 마찬가지로 데이터 해시맵, TTL 해시맵, 빈도 해시맵의 노드를 함께 정리해야 한다.

데이터가 10만 건으로 늘어나면 병목은 네 지점에서 먼저 나타난다. 첫째, 해시 충돌이 늘면 특정 버킷의 체인이 길어져 평균 O(1) 조회가 O(k) 체인 순회로 악화된다. 초기 버킷 수를 예상 키 수에 맞게 크게 잡거나, 체인 길이 관측값을 기준으로 리사이즈를 더 일찍 수행하면 완화할 수 있다. 둘째, 리사이즈는 모든 엔트리를 새 버킷에 다시 배치하므로 한 번의 `SET`에서 O(n) 지연이 생긴다. 운영형 구현이라면 점진적 리해싱으로 여러 명령에 재배치 비용을 나눠야 한다. 셋째, `KEYS`는 전체 키를 순회하므로 10만 건에서는 결과 생성과 출력 자체가 병목이다. 실제 서비스에서는 `SCAN`처럼 커서 기반으로 일부만 반환하는 명령이 필요하다. 넷째, TTL 힙의 지연 삭제는 만료 시간이 여러 번 갱신된 키의 오래된 튜플을 힙에 남긴다. 힙 크기가 실제 TTL 키 수보다 지나치게 커지면 무효 튜플 제거 비용이 증가하므로, 무효 튜플 비율이 일정 수준을 넘을 때 최신 TTL 해시맵 기준으로 힙을 재구성하는 보정이 필요하다. 이 구현은 학습용 CLI라 단순성을 우선했지만, `used_memory`를 매번 전체 재계산하지 않고 증감분으로 관리하는 방식은 이미 10만 건에서도 중요한 기본 최적화다.

현재 메모리 모델은 과제 공식에 맞춰 키와 값의 UTF-8 길이만 센다. 자료구조 오버헤드까지 포함하는 모델로 바꾸면 `RedisEntry`, `Entry`, 이중 연결 리스트 `Node`, TTL 힙 슬롯, 버킷 배열, 비어 있는 버킷 리스트, 문자열 객체의 런타임 오버헤드도 `used_memory`에 들어간다. 차이점은 단순히 숫자가 커지는 데 그치지 않는다. 해시맵 리사이즈가 발생하면 저장된 키와 값은 그대로여도 버킷 배열과 체인 리스트 수가 늘어 `used_memory`가 증가한다. TTL을 설정하면 값은 바뀌지 않아도 TTL 해시맵 엔트리와 힙 슬롯 때문에 메모리가 증가한다. LRU 또는 LFU 추적 노드도 키마다 추가 비용을 만든다.

오버헤드를 포함하려면 메모리 갱신 지점을 더 촘촘히 나눠야 한다. `SET`은 키와 값 길이뿐 아니라 데이터 엔트리, LRU 노드, 해시맵 체인 노드의 예상 비용을 더한 뒤 저장 가능 여부를 판단해야 한다. `EXPIRE`는 TTL 엔트리와 힙 슬롯 비용을 추가하고, TTL 갱신으로 생기는 지연 삭제 튜플도 별도 비용으로 잡아야 한다. `DEL`, 만료 삭제, 자동 제거는 관련 구조의 비용을 모두 차감해야 한다. Python에서는 `sys.getsizeof`가 참조 대상의 깊은 크기까지 자동 합산하지 않으므로, 운영 재현성을 위해 클래스별 고정 보정값을 정하거나 샘플 객체로 측정한 값을 상수화하는 편이 낫다. `INFO memory`에는 과제 공식의 논리 메모리와 오버헤드 포함 추정 메모리를 분리해 표시하면 학습 목적과 실제 프로세스 메모리 추정치를 동시에 확인할 수 있다.

## 실행 예시

```text
mini-redis> CONFIG SET maxmemory 30
OK
mini-redis> SET user:1 "Alice"
OK
mini-redis> SET user:2 "Bob"
OK
mini-redis> SET user:3 "Charlie"
OK
mini-redis> GET user:1
(nil)
mini-redis> INFO memory
used_memory:22
maxmemory:30
evicted_keys:1
mini-redis> KEYS
1. "user:3"
2. "user:2"
mini-redis> EXPIRE user:2 1
(integer) 1
mini-redis> TTL user:2
(integer) 0
mini-redis> GET user:2
(nil)
mini-redis> TTL user:2
(integer) -2
```

`KEYS`의 순서는 해시 버킷 순회 결과이므로 정렬을 보장하지 않는다.

## 문제 해결

### Docker 빌드가 실패할 때

Docker가 실행 중인지 확인한다. 그다음 저장소 루트에서 아래 명령을 다시 실행한다.

```bash
docker build -t codyssey-cli-test-mini-redis .
```

이미지 이름을 바꿔야 한다면 `codyssey-cli-test` 접두사를 유지한다.

### 테스트에서 `ModuleNotFoundError: No module named 'mini_redis'`가 나올 때

저장소 루트를 컨테이너 작업 디렉터리로 마운트해야 한다.

```bash
docker run --rm --name codyssey-cli-test-mini-redis-test -v "$PWD:/app" -w /app codyssey-cli-test-mini-redis python -m pytest -q
```

`pytest` 콘솔 스크립트 대신 `python -m pytest`를 사용하면 현재 작업 디렉터리가 import 경로에 포함된다.

### REPL이 종료되지 않을 때

프롬프트에 `exit` 또는 `quit`을 입력한다. 표준 입력이 닫힌 경우에는 `EOFError`를 처리하고 종료한다.

### `SET`이 OOM을 반환할 때

`INFO memory`로 현재 `used_memory`와 `maxmemory`를 확인한다. 단일 엔트리가 제한보다 크면 LRU로 다른 키를 제거해도 저장할 수 없다. 제한을 늘리거나 `CONFIG SET maxmemory 0`으로 무제한 모드로 바꾼다.

### TTL이 바로 0으로 보일 때

`TTL`은 남은 초를 정수로 반환한다. `EXPIRE key 1` 직후에도 실행 시점 차이 때문에 `(integer) 0`이 나올 수 있다. 만료 시각이 지나면 다음 키 기반 명령이나 전체 상태 명령에서 키가 정리된다.
