"""Mini Redis 요구사항 시나리오를 비대화형으로 실행한다."""

import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from mini_redis.core import MiniRedis


def main() -> None:
    """메모리 제한, LRU, TTL, 오류 처리를 순서대로 출력한다."""
    store = MiniRedis()
    commands = [
        'CONFIG SET maxmemory 30',
        'SET user:1 "Alice"',
        'SET user:2 "Bob"',
        'SET user:3 "Charlie"',
        'GET user:1',
        'INFO memory',
        'KEYS',
        'EXPIRE user:2 1',
        'TTL user:2',
    ]

    for command in commands:
        print(f"mini-redis> {command}")
        print(store.execute(command))

    time.sleep(1.1)
    for command in ["GET user:2", "TTL user:2", "CONFIG SET maxmemory abc", "GET", "HELLO"]:
        print(f"mini-redis> {command}")
        print(store.execute(command))


if __name__ == "__main__":
    main()
