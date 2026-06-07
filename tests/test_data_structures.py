"""Direct data structure tests for Mini Redis."""

from mini_redis.datastructures.doubly_linked_list import DoublyLinkedList
from mini_redis.datastructures.hash_map import HashMap
from mini_redis.datastructures.min_heap import MinHeap


def test_doubly_linked_list_moves_and_removes_nodes_in_constant_shape():
    """The list keeps node links valid while moving and removing nodes."""
    linked = DoublyLinkedList()

    first = linked.insert_back("old")
    linked.insert_front("new")
    linked.move_to_front(first)

    assert linked.remove_front() == "old"
    assert linked.remove_back() == "new"
    assert linked.remove_front() is None


def test_hash_map_handles_collisions_resize_and_removal():
    """The hash map stores colliding keys and resizes past load factor."""
    mapping = HashMap(initial_capacity=2)

    for index in range(20):
        mapping.put(f"key:{index}", f"value:{index}")

    assert mapping.size() == 20
    assert mapping.get("key:0") == "value:0"
    assert mapping.get("key:19") == "value:19"
    assert mapping.contains("key:9") is True
    assert mapping.remove("key:9") == "value:9"
    assert mapping.contains("key:9") is False
    assert mapping.size() == 19


def test_min_heap_orders_expiration_tuples():
    """The minimum heap pops the earliest expiration tuple first."""
    heap = MinHeap()

    heap.push((30.0, "late"))
    heap.push((10.0, "early"))
    heap.push((20.0, "middle"))

    assert heap.peek() == (10.0, "early")
    assert heap.pop() == (10.0, "early")
    assert heap.pop() == (20.0, "middle")
    assert heap.pop() == (30.0, "late")
    assert heap.pop() is None
