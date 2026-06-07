"""TTL 만료 순서를 관리하는 최소 힙."""

from mini_redis.datastructures.dynamic_array import DynamicArray


class MinHeap:
    """(expire_at, key) 같은 비교 가능한 값을 최소값 우선으로 저장한다."""

    def __init__(self):
        """빈 힙 저장소를 준비한다."""
        self._items = DynamicArray()

    def push(self, value) -> None:
        """값을 추가한 뒤 위로 올리며 힙 속성을 회복한다."""
        self._items.append(value)
        self._heapify_up(self._items.size() - 1)

    def pop(self):
        """최소값을 제거해서 반환한다."""
        if self._items.size() == 0:
            return None
        root = self._items.get(0)
        last = self._items.pop()
        if self._items.size() > 0:
            self._items.set(0, last)
            self._heapify_down(0)
        return root

    def peek(self):
        """최소값을 제거하지 않고 반환한다."""
        if self._items.size() == 0:
            return None
        return self._items.get(0)

    def size(self) -> int:
        """힙에 저장된 원소 수를 반환한다."""
        return self._items.size()

    def _heapify_up(self, index: int) -> None:
        """부모보다 작은 값을 위로 올린다."""
        while index > 0:
            parent = (index - 1) // 2
            if self._items.get(parent) <= self._items.get(index):
                break
            self._swap(parent, index)
            index = parent

    def _heapify_down(self, index: int) -> None:
        """자식보다 큰 값을 아래로 내린다."""
        while True:
            left = index * 2 + 1
            right = index * 2 + 2
            smallest = index

            if left < self._items.size() and self._items.get(left) < self._items.get(smallest):
                smallest = left
            if right < self._items.size() and self._items.get(right) < self._items.get(smallest):
                smallest = right
            if smallest == index:
                break

            self._swap(index, smallest)
            index = smallest

    def _swap(self, left: int, right: int) -> None:
        """두 인덱스의 값을 교환한다."""
        temp = self._items.get(left)
        self._items.set(left, self._items.get(right))
        self._items.set(right, temp)
