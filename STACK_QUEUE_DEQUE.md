# 스택, 큐, 덱 이해와 활용

## 목적

스택(Stack), 큐(Queue), 덱(Deque)은 원소를 넣고 빼는 위치가 다른 선형 자료구조다. 이 프로젝트는 직접 구현한 `DoublyLinkedList`의 양끝 연산을 사용해 세 구조를 설명하고, Pub/Sub 메시지 버퍼에 큐를 적용한다.

## 비교

| 자료구조 | 처리 순서 | 삽입 위치 | 제거 위치 | 대표 활용 |
| --- | --- | --- | --- | --- |
| 스택 | LIFO | 한쪽 끝 | 같은 끝 | 실행 취소, 함수 호출, 괄호 검사 |
| 큐 | FIFO | 뒤 | 앞 | 메시지 버퍼, 작업 대기열, 명령 처리 |
| 덱 | 양방향 | 앞 또는 뒤 | 앞 또는 뒤 | 슬라이딩 윈도우, 앞뒤 탐색 |

## 스택

스택은 마지막에 넣은 원소를 먼저 꺼내는 LIFO(Last In, First Out) 구조다.

- `push`: 스택 맨 위에 원소 추가
- `pop`: 스택 맨 위 원소 제거·반환
- `peek`: 스택 맨 위 원소 조회

이중 연결 리스트에서는 앞쪽을 스택 맨 위로 정하면 `insert_front`, `remove_front`로 `push`, `pop`을 각각 O(1)에 처리한다.

```text
push(A) → push(B) → push(C)
top [C, B, A] bottom
pop() = C
```

커맨드 히스토리를 추가한다면 최근 명령을 스택에 `push`하고, 실행 취소가 필요할 때 `pop`하는 방식으로 확장할 수 있다. 현재 Mini Redis에는 커맨드 히스토리를 구현하지 않았다.

## 큐

큐는 먼저 넣은 원소를 먼저 꺼내는 FIFO(First In, First Out) 구조다.

- `enqueue`: 큐 뒤에 원소 추가
- `dequeue`: 큐 앞 원소 제거·반환
- `peek`: 큐 앞 원소 조회

이중 연결 리스트에서는 `insert_back`으로 뒤에 넣고 `remove_front`로 앞에서 꺼낸다. 두 연산은 head와 tail 포인터만 변경하므로 O(1)이다.

```text
enqueue(A) → enqueue(B) → enqueue(C)
front [A, B, C] back
dequeue() = A
```

### Pub/Sub 적용

`mini_redis/pubsub.py`의 `Subscriber.messages`는 `DoublyLinkedList` 기반 큐다.

1. `PUBLISH channel message` 처리 시 `insert_back(message)`로 구독자 버퍼 뒤에 메시지 추가
2. `drain_messages` 처리 시 `remove_front()`로 앞의 메시지부터 제거·반환
3. 따라서 같은 채널에서 발행된 메시지는 발행 순서대로 구독자에게 전달됨

이 버퍼는 네트워크 통신이 없는 단일 프로세스 학습용 구현에서 메시지 전달 순서를 검증하는 용도다. Redis 원본은 네트워크 연결에 메시지를 비동기 push한다.

## 덱

덱(Deque, Double-Ended Queue)은 앞과 뒤 양쪽에서 삽입·삭제 가능한 구조다.

- 앞 삽입: `insert_front`
- 뒤 삽입: `insert_back`
- 앞 제거: `remove_front`
- 뒤 제거: `remove_back`

현재 `DoublyLinkedList`는 네 연산을 모두 O(1)에 제공하므로 덱의 기반 구조로 사용할 수 있다. 스택은 덱의 한쪽 끝만 사용한 경우고, 큐는 덱의 서로 다른 양끝을 사용한 경우다.

## 시간 복잡도

| 연산 | 스택 | 큐 | 덱 |
| --- | --- | --- | --- |
| 앞 삽입 | O(1) | 사용 안 함 | O(1) |
| 뒤 삽입 | 사용 안 함 | O(1) | O(1) |
| 앞 제거 | 사용 안 함 | O(1) | O(1) |
| 뒤 제거 | O(1) | 사용 안 함 | O(1) |

배열 앞쪽에서 원소를 제거하면 뒤 원소들을 이동해야 해 O(n)이 될 수 있다. 이중 연결 리스트는 노드 포인터만 연결·해제하므로 양끝 연산에 원소 이동이 없다.

## 프로젝트 제약과 연결

이 과제는 `dict`, `set`, `collections` 사용을 금지한다. 따라서 Pub/Sub 구독자 버퍼는 Python `collections.deque`가 아니라 직접 구현한 `DoublyLinkedList`를 사용한다. 채널과 구독자 조회는 직접 구현한 체이닝 `HashMap`을 사용한다.
