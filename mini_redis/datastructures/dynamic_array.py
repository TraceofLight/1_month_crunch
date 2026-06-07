"""고정 배열을 확장하며 사용하는 동적 배열 구현."""


class DynamicArray:
    """append/get/set/remove와 2배 확장을 제공하는 배열이다."""

    def __init__(self, capacity: int = 4):
        """초기 용량을 최소 1 이상으로 보정해 배열을 만든다."""
        if capacity < 1:
            capacity = 1
        self._capacity = capacity
        self._size = 0
        self._items = [None] * self._capacity

    def append(self, value):
        """배열 끝에 값을 추가하고 필요하면 용량을 2배로 늘린다."""
        if self._size == self._capacity:
            self._resize(self._capacity * 2)
        self._items[self._size] = value
        self._size += 1

    def get(self, index: int):
        """index 위치의 값을 반환한다."""
        self._validate_index(index)
        return self._items[index]

    def set(self, index: int, value) -> None:
        """index 위치의 값을 교체한다."""
        self._validate_index(index)
        self._items[index] = value

    def remove(self, index: int):
        """index 위치의 값을 제거하고 뒤쪽 값을 한 칸씩 당긴다."""
        self._validate_index(index)
        value = self._items[index]
        cursor = index
        while cursor < self._size - 1:
            self._items[cursor] = self._items[cursor + 1]
            cursor += 1
        self._size -= 1
        self._items[self._size] = None
        return value

    def pop(self):
        """마지막 값을 제거해서 반환한다."""
        if self._size == 0:
            return None
        self._size -= 1
        value = self._items[self._size]
        self._items[self._size] = None
        return value

    def size(self) -> int:
        """현재 저장된 원소 수를 반환한다."""
        return self._size

    def capacity(self) -> int:
        """현재 내부 배열 용량을 반환한다."""
        return self._capacity

    def _resize(self, next_capacity: int) -> None:
        """새 용량의 배열로 기존 원소를 복사한다."""
        next_items = [None] * next_capacity
        index = 0
        while index < self._size:
            next_items[index] = self._items[index]
            index += 1
        self._items = next_items
        self._capacity = next_capacity

    def _validate_index(self, index: int) -> None:
        """배열 범위를 벗어난 접근을 차단한다."""
        if index < 0 or index >= self._size:
            raise IndexError("array index out of range")
