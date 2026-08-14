"""전위, 중위, 후위, 레벨 순회를 제공하는 이진 트리."""

from mini_redis.datastructures.doubly_linked_list import DoublyLinkedList


class BinaryTreeNode:
    """값과 왼쪽·오른쪽 자식 참조를 저장하는 이진 트리 노드."""

    def __init__(self, data):
        """노드 값과 비어 있는 자식 참조를 초기화한다."""
        self.data = data
        self.left = None
        self.right = None


class BinaryTree:
    """명시적으로 연결한 노드의 네 가지 순회를 제공한다."""

    def __init__(self):
        """빈 이진 트리를 만든다."""
        self.root = None

    def set_root(self, data) -> BinaryTreeNode:
        """루트 노드를 만들고 반환한다."""
        self.root = BinaryTreeNode(data)
        return self.root

    def insert_left(self, parent: BinaryTreeNode, data) -> BinaryTreeNode:
        """parent의 왼쪽 자식 노드를 만들고 반환한다."""
        parent.left = BinaryTreeNode(data)
        return parent.left

    def insert_right(self, parent: BinaryTreeNode, data) -> BinaryTreeNode:
        """parent의 오른쪽 자식 노드를 만들고 반환한다."""
        parent.right = BinaryTreeNode(data)
        return parent.right

    def preorder(self):
        """현재, 왼쪽, 오른쪽 순서의 전위 순회 결과를 반환한다."""
        result = []
        self._preorder(self.root, result)
        return result

    def inorder(self):
        """왼쪽, 현재, 오른쪽 순서의 중위 순회 결과를 반환한다."""
        result = []
        self._inorder(self.root, result)
        return result

    def postorder(self):
        """왼쪽, 오른쪽, 현재 순서의 후위 순회 결과를 반환한다."""
        result = []
        self._postorder(self.root, result)
        return result

    def level_order(self):
        """위에서 아래, 왼쪽에서 오른쪽 순서의 레벨 순회 결과를 반환한다."""
        if self.root is None:
            return []

        result = []
        queue = DoublyLinkedList()
        queue.insert_back(self.root)
        node = queue.remove_front()
        while node is not None:
            result.append(node.data)
            if node.left is not None:
                queue.insert_back(node.left)
            if node.right is not None:
                queue.insert_back(node.right)
            node = queue.remove_front()
        return result

    def _preorder(self, node, result) -> None:
        """전위 순회 결과에 node 서브트리를 추가한다."""
        if node is None:
            return
        result.append(node.data)
        self._preorder(node.left, result)
        self._preorder(node.right, result)

    def _inorder(self, node, result) -> None:
        """중위 순회 결과에 node 서브트리를 추가한다."""
        if node is None:
            return
        self._inorder(node.left, result)
        result.append(node.data)
        self._inorder(node.right, result)

    def _postorder(self, node, result) -> None:
        """후위 순회 결과에 node 서브트리를 추가한다."""
        if node is None:
            return
        self._postorder(node.left, result)
        self._postorder(node.right, result)
        result.append(node.data)
