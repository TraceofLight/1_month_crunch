"""O(1) 삽입, 삭제, 이동을 지원하는 이중 연결 리스트."""


class Node:
    """prev, next, data 필드를 갖는 이중 연결 리스트 노드."""

    def __init__(self, data):
        """노드에 저장할 데이터를 초기화한다."""
        self.prev = None
        self.next = None
        self.data = data


class DoublyLinkedList:
    """머리와 꼬리 포인터로 양끝 연산을 O(1)에 수행한다."""

    def __init__(self):
        """빈 리스트를 만든다."""
        self.head = None
        self.tail = None
        self._size = 0

    def insert_front(self, data) -> Node:
        """새 노드를 리스트 앞에 삽입하고 노드 참조를 반환한다."""
        node = Node(data)
        node.next = self.head
        if self.head is not None:
            self.head.prev = node
        self.head = node
        if self.tail is None:
            self.tail = node
        self._size += 1
        return node

    def insert_back(self, data) -> Node:
        """새 노드를 리스트 뒤에 삽입하고 노드 참조를 반환한다."""
        node = Node(data)
        node.prev = self.tail
        if self.tail is not None:
            self.tail.next = node
        self.tail = node
        if self.head is None:
            self.head = node
        self._size += 1
        return node

    def remove_front(self):
        """첫 노드를 제거하고 데이터를 반환한다."""
        if self.head is None:
            return None
        return self.remove_node(self.head)

    def remove_back(self):
        """마지막 노드를 제거하고 데이터를 반환한다."""
        if self.tail is None:
            return None
        return self.remove_node(self.tail)

    def remove_node(self, node: Node):
        """주어진 노드를 O(1)에 제거하고 데이터를 반환한다."""
        if node.prev is not None:
            node.prev.next = node.next
        else:
            self.head = node.next

        if node.next is not None:
            node.next.prev = node.prev
        else:
            self.tail = node.prev

        node.prev = None
        node.next = None
        self._size -= 1
        return node.data

    def move_to_front(self, node: Node) -> Node:
        """기존 노드를 리스트 앞쪽으로 O(1)에 이동한다."""
        if node is self.head:
            return node
        data = self.remove_node(node)
        return self.insert_front(data)

    def size(self) -> int:
        """현재 노드 수를 반환한다."""
        return self._size
