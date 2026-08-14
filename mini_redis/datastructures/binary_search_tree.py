"""삽입, 탐색, 삭제, 중위 순회를 제공하는 이진 탐색 트리."""


class BinarySearchTreeNode:
    """키, 값, 왼쪽·오른쪽 자식 참조를 저장하는 BST 노드."""

    def __init__(self, key: str, value):
        """노드의 키와 값을 초기화한다."""
        self.key = key
        self.value = value
        self.left = None
        self.right = None


class BinarySearchTree:
    """문자열 키를 정렬 순서로 저장하는 이진 탐색 트리."""

    def __init__(self):
        """빈 트리를 만든다."""
        self._root = None

    def insert(self, key: str, value):
        """키를 삽입하거나 이미 있으면 값을 교체한다."""
        if self._root is None:
            self._root = BinarySearchTreeNode(key, value)
            return None

        node = self._root
        while True:
            if key == node.key:
                old_value = node.value
                node.value = value
                return old_value
            if key < node.key:
                if node.left is None:
                    node.left = BinarySearchTreeNode(key, value)
                    return None
                node = node.left
            else:
                if node.right is None:
                    node.right = BinarySearchTreeNode(key, value)
                    return None
                node = node.right

    def get(self, key: str):
        """키의 값을 반환하고 없으면 None을 반환한다."""
        node = self._root
        while node is not None:
            if key == node.key:
                return node.value
            if key < node.key:
                node = node.left
            else:
                node = node.right
        return None

    def remove(self, key: str):
        """키를 삭제하고 기존 값을 반환한다. 없으면 None을 반환한다."""
        parent = None
        node = self._root
        while node is not None and node.key != key:
            parent = node
            if key < node.key:
                node = node.left
            else:
                node = node.right
        if node is None:
            return None

        removed_value = node.value
        if node.left is not None and node.right is not None:
            successor_parent = node
            successor = node.right
            while successor.left is not None:
                successor_parent = successor
                successor = successor.left
            node.key = successor.key
            node.value = successor.value
            parent = successor_parent
            node = successor

        child = node.left if node.left is not None else node.right
        if parent is None:
            self._root = child
        elif parent.left is node:
            parent.left = child
        else:
            parent.right = child
        return removed_value

    def inorder_items(self):
        """키 오름차순의 (키, 값) 목록을 반환한다."""
        items = []
        stack = []
        node = self._root
        while node is not None or len(stack) > 0:
            while node is not None:
                stack.append(node)
                node = node.left
            node = stack.pop()
            items.append((node.key, node.value))
            node = node.right
        return items
