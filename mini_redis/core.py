"""자료구조를 조합해 Redis 스타일 명령을 실행하는 핵심 모듈."""

import shlex
import time

from mini_redis.datastructures.doubly_linked_list import DoublyLinkedList
from mini_redis.datastructures.hash_map import HashMap
from mini_redis.datastructures.min_heap import MinHeap
from mini_redis.pubsub import PubSubBroker


OOM_ERROR = "(error) OOM command not allowed when used_memory > 'maxmemory'"
INT_ERROR = "(error) ERR value is not an integer or out of range"


class RedisEntry:
    """문자열 값과 메모리 계산용 크기를 함께 저장한다."""

    def __init__(self, key: str, value: str):
        """키, 값, 공식 기준 엔트리 크기를 저장한다."""
        self.key = key
        self.value = value
        self.memory = len(key.encode("utf-8")) + len(value.encode("utf-8"))


class LruEntry:
    """LRU 연결 리스트 노드에 저장되는 키 래퍼."""

    def __init__(self, key: str):
        """LRU 추적 대상 키를 저장한다."""
        self.key = key


class MiniRedis:
    """문자열 명령, LRU 메모리 제한, TTL을 제공하는 Mini Redis."""

    def __init__(self):
        """저장소와 보조 자료구조를 초기화한다."""
        self._data = HashMap()
        self._lru = DoublyLinkedList()
        self._lru_nodes = HashMap()
        self._ttl = HashMap()
        self._ttl_heap = MinHeap()
        self._pubsub = PubSubBroker()
        self.used_memory = 0
        self.maxmemory = 0
        self.evicted_keys = 0

    def execute(self, line: str) -> str:
        """한 줄 명령을 파싱하고 실행 결과 문자열을 반환한다."""
        try:
            parts = shlex.split(line)
        except ValueError:
            return "(error) ERR syntax error"
        if len(parts) == 0:
            return ""

        command = parts[0].upper()
        args = parts[1:]

        if command == "SET":
            return self._cmd_set(args)
        if command == "GET":
            return self._cmd_get(args)
        if command == "DEL":
            return self._cmd_del(args)
        if command == "EXISTS":
            return self._cmd_exists(args)
        if command == "DBSIZE":
            return self._cmd_dbsize(args)
        if command == "KEYS":
            return self._cmd_keys(args)
        if command == "CONFIG":
            return self._cmd_config(args)
        if command == "INFO":
            return self._cmd_info(args)
        if command == "EXPIRE":
            return self._cmd_expire(args)
        if command == "TTL":
            return self._cmd_ttl(args)
        if command == "SUBSCRIBE":
            return self._cmd_subscribe(args)
        if command == "PUBLISH":
            return self._cmd_publish(args)

        return f"(error) ERR unknown command '{command}'"

    def info_memory_lines(self):
        """INFO memory 출력에 들어가는 메모리 항목 배열을 반환한다."""
        return [
            f"used_memory:{self.used_memory}",
            f"maxmemory:{self.maxmemory}",
            f"evicted_keys:{self.evicted_keys}",
        ]

    def _cmd_set(self, args) -> str:
        """SET key value 명령을 처리한다."""
        if len(args) != 2:
            return self._wrong_args("SET")
        key = args[0]
        value = args[1]
        next_entry = RedisEntry(key, value)

        if self.maxmemory > 0 and next_entry.memory > self.maxmemory:
            return OOM_ERROR

        self._delete_if_expired(key)
        old_entry = self._data.get(key)
        old_memory = 0
        if old_entry is not None:
            old_memory = old_entry.memory

        self._data.put(key, next_entry)
        self.used_memory = self.used_memory - old_memory + next_entry.memory
        self._ttl.remove(key)
        self._touch_lru(key)
        self._evict_until_within_limit()
        return "OK"

    def _cmd_get(self, args) -> str:
        """GET key 명령을 처리한다."""
        if len(args) != 1:
            return self._wrong_args("GET")
        key = args[0]
        if self._delete_if_expired(key):
            return "(nil)"

        entry = self._data.get(key)
        if entry is None:
            return "(nil)"
        self._touch_lru(key)
        return f'"{entry.value}"'

    def _cmd_del(self, args) -> str:
        """DEL key 명령을 처리한다."""
        if len(args) != 1:
            return self._wrong_args("DEL")
        key = args[0]
        self._delete_if_expired(key)
        if self._remove_key(key, count_eviction=False):
            return "(integer) 1"
        return "(integer) 0"

    def _cmd_exists(self, args) -> str:
        """EXISTS key 명령을 처리한다."""
        if len(args) != 1:
            return self._wrong_args("EXISTS")
        key = args[0]
        self._delete_if_expired(key)
        if self._data.contains(key):
            return "(integer) 1"
        return "(integer) 0"

    def _cmd_dbsize(self, args) -> str:
        """DBSIZE 명령을 처리한다."""
        if len(args) != 0:
            return self._wrong_args("DBSIZE")
        self._purge_expired()
        return f"(integer) {self._data.size()}"

    def _cmd_keys(self, args) -> str:
        """KEYS 명령을 처리한다."""
        if len(args) != 0:
            return self._wrong_args("KEYS")
        self._purge_expired()
        keys = self._data.keys()
        if len(keys) == 0:
            return "(empty array)"

        lines = []
        index = 0
        while index < len(keys):
            lines.append(f'{index + 1}. "{keys[index]}"')
            index += 1
        return "\n".join(lines)

    def _cmd_config(self, args) -> str:
        """CONFIG SET maxmemory bytes 명령을 처리한다."""
        if len(args) != 3 or args[0].upper() != "SET" or args[1].lower() != "maxmemory":
            return self._wrong_args("CONFIG")
        value = self._parse_non_negative_int(args[2])
        if value is None:
            return INT_ERROR
        self.maxmemory = value
        self._evict_until_within_limit()
        return "OK"

    def _cmd_info(self, args) -> str:
        """INFO memory 명령을 처리한다."""
        if len(args) != 1 or args[0].lower() != "memory":
            return self._wrong_args("INFO")
        self._purge_expired()
        return "\n".join(self.info_memory_lines())

    def _cmd_expire(self, args) -> str:
        """EXPIRE key seconds 명령을 처리한다."""
        if len(args) != 2:
            return self._wrong_args("EXPIRE")
        seconds = self._parse_int(args[1])
        if seconds is None:
            return INT_ERROR

        key = args[0]
        self._delete_if_expired(key)
        if not self._data.contains(key):
            return "(integer) 0"
        if seconds <= 0:
            self._remove_key(key, count_eviction=False)
            return "(integer) 1"

        expire_at = time.time() + seconds
        self._ttl.put(key, expire_at)
        self._ttl_heap.push((expire_at, key))
        return "(integer) 1"

    def _cmd_ttl(self, args) -> str:
        """TTL key 명령을 처리한다."""
        if len(args) != 1:
            return self._wrong_args("TTL")
        key = args[0]
        self._delete_if_expired(key)
        if not self._data.contains(key):
            return "(integer) -2"

        expire_at = self._ttl.get(key)
        if expire_at is None:
            return "(integer) -1"

        remaining = int(expire_at - time.time())
        if remaining < 0:
            remaining = 0
        return f"(integer) {remaining}"

    def _cmd_subscribe(self, args) -> str:
        """SUBSCRIBE channel 명령으로 현재 REPL을 채널에 등록한다."""
        if len(args) != 1:
            return self._wrong_args("SUBSCRIBE")
        self._pubsub.subscribe(args[0], "repl")
        count = self._pubsub.subscription_count("repl")
        return f'1. "subscribe"\n2. "{args[0]}"\n3. (integer) {count}'

    def _cmd_publish(self, args) -> str:
        """PUBLISH channel message 명령을 처리한다."""
        if len(args) != 2:
            return self._wrong_args("PUBLISH")
        delivered = self._pubsub.publish(args[0], args[1])
        return f"(integer) {delivered}"

    def _touch_lru(self, key: str) -> None:
        """키를 LRU 리스트의 가장 최근 위치로 이동한다."""
        node = self._lru_nodes.get(key)
        if node is not None:
            new_node = self._lru.move_to_front(node)
            self._lru_nodes.put(key, new_node)
            return
        self._lru_nodes.put(key, self._lru.insert_front(LruEntry(key)))

    def _evict_until_within_limit(self) -> None:
        """used_memory가 maxmemory 이하가 될 때까지 LRU 키를 제거한다."""
        if self.maxmemory <= 0:
            return
        while self.used_memory > self.maxmemory:
            lru_entry = self._lru.remove_back()
            if lru_entry is None:
                return
            self._remove_key(lru_entry.key, count_eviction=True, lru_already_removed=True)

    def _purge_expired(self) -> None:
        """힙의 최소 만료 시각부터 현재 만료된 키를 제거한다."""
        now = time.time()
        while self._ttl_heap.size() > 0:
            item = self._ttl_heap.peek()
            expire_at = item[0]
            key = item[1]
            if expire_at > now:
                return
            self._ttl_heap.pop()
            current_expire_at = self._ttl.get(key)
            if current_expire_at is not None and current_expire_at == expire_at:
                self._remove_key(key, count_eviction=False)

    def _delete_if_expired(self, key: str) -> bool:
        """키가 만료되었으면 모든 구조에서 제거하고 True를 반환한다."""
        expire_at = self._ttl.get(key)
        if expire_at is None:
            return False
        if expire_at <= time.time():
            self._remove_key(key, count_eviction=False)
            return True
        return False

    def _remove_key(self, key: str, count_eviction: bool, lru_already_removed: bool = False) -> bool:
        """데이터, TTL, LRU 구조에서 키를 함께 제거한다."""
        entry = self._data.remove(key)
        if entry is None:
            return False
        self.used_memory -= entry.memory
        self._ttl.remove(key)

        if not lru_already_removed:
            node = self._lru_nodes.remove(key)
            if node is not None:
                self._lru.remove_node(node)
        else:
            self._lru_nodes.remove(key)

        if count_eviction:
            self.evicted_keys += 1
        return True

    def _parse_int(self, value: str):
        """정수 문자열을 파싱하고 실패하면 None을 반환한다."""
        try:
            return int(value)
        except ValueError:
            return None

    def _parse_non_negative_int(self, value: str):
        """0 이상의 정수 문자열을 파싱하고 실패하면 None을 반환한다."""
        parsed = self._parse_int(value)
        if parsed is None or parsed < 0:
            return None
        return parsed

    def _wrong_args(self, command: str) -> str:
        """Redis 스타일 인자 개수 오류를 반환한다."""
        return f"(error) ERR wrong number of arguments for '{command}' command"
