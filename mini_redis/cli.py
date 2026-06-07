"""Mini Redis REPL 실행 모듈."""

from mini_redis.core import MiniRedis


def main() -> None:
    """사용자 입력을 반복해서 읽고 Redis 스타일 결과를 출력한다."""
    store = MiniRedis()
    while True:
        try:
            line = input("mini-redis> ")
        except EOFError:
            print()
            break

        lowered = line.strip().lower()
        if lowered == "exit" or lowered == "quit":
            break
        if line.strip() == "":
            continue

        print(store.execute(line))
