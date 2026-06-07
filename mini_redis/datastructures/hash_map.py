"""체이닝 방식 충돌 해결과 2배 리사이즈를 갖는 해시맵."""

from mini_redis.datastructures.doubly_linked_list import DoublyLinkedList


class Entry:
    """해시맵 버킷 체인에 저장되는 키와 값 쌍."""

    def __init__(self, key: str, value):
        """키와 값을 저장한다."""
        self.key = key
        self.value = value


class HashMap:
    """직접 설계한 해시 함수와 체이닝으로 문자열 키를 저장한다."""

    def __init__(self, initial_capacity: int = 8):
        """버킷 배열과 원소 수를 초기화한다."""
        capacity = 1
        while capacity < initial_capacity:
            capacity *= 2
        self._buckets = self._make_buckets(capacity)
        self._size = 0

    def put(self, key: str, value):
        """키가 있으면 값을 교체하고, 없으면 새 엔트리를 추가한다."""
        if (self._size + 1) / len(self._buckets) > 0.75:
            self._resize(len(self._buckets) * 2)

        bucket = self._bucket_for(key)
        node = bucket.head
        while node is not None:
            if node.data.key == key:
                old_value = node.data.value
                node.data.value = value
                return old_value
            node = node.next

        bucket.insert_back(Entry(key, value))
        self._size += 1
        return None

    def get(self, key: str):
        """키에 해당하는 값을 반환하고 없으면 None을 반환한다."""
        node = self._find_node(key)
        if node is None:
            return None
        return node.data.value

    def remove(self, key: str):
        """키를 제거하고 기존 값을 반환한다. 없으면 None을 반환한다."""
        bucket = self._bucket_for(key)
        node = bucket.head
        while node is not None:
            if node.data.key == key:
                value = node.data.value
                bucket.remove_node(node)
                self._size -= 1
                return value
            node = node.next
        return None

    def contains(self, key: str) -> bool:
        """키 존재 여부를 반환한다."""
        return self._find_node(key) is not None

    def keys(self):
        """전체 키를 배열로 반환한다."""
        result = []
        bucket_index = 0
        while bucket_index < len(self._buckets):
            node = self._buckets[bucket_index].head
            while node is not None:
                result.append(node.data.key)
                node = node.next
            bucket_index += 1
        return result

    def size(self) -> int:
        """저장된 키 개수를 반환한다."""
        return self._size

    def _hash(self, key: str) -> int:
        """문자 코드를 누적하는 다항식 기반 해시 값을 계산한다."""
        value = 2166136261
        index = 0
        while index < len(key):
            value = value ^ ord(key[index])
            value = (value * 16777619) & 0xFFFFFFFF
            index += 1
        return value

    def _bucket_for(self, key: str) -> DoublyLinkedList:
        """키가 속하는 버킷 리스트를 반환한다."""
        return self._buckets[self._hash(key) % len(self._buckets)]

    def _find_node(self, key: str):
        """버킷 체인에서 키와 일치하는 노드를 찾는다."""
        bucket = self._bucket_for(key)
        node = bucket.head
        while node is not None:
            if node.data.key == key:
                return node
            node = node.next
        return None

    def _resize(self, next_capacity: int) -> None:
        """버킷 수를 2배로 늘리고 기존 엔트리를 재배치한다."""
        old_buckets = self._buckets
        self._buckets = self._make_buckets(next_capacity)
        old_size = self._size
        self._size = 0

        bucket_index = 0
        while bucket_index < len(old_buckets):
            node = old_buckets[bucket_index].head
            while node is not None:
                self.put(node.data.key, node.data.value)
                node = node.next
            bucket_index += 1

        self._size = old_size

    def _make_buckets(self, capacity: int):
        """체이닝에 사용할 이중 연결 리스트 버킷 배열을 만든다."""
        buckets = []
        index = 0
        while index < capacity:
            buckets.append(DoublyLinkedList())
            index += 1
        return buckets
