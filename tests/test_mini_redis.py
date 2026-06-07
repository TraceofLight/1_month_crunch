"""Mini Redis command behavior tests."""

import time

from mini_redis.core import MiniRedis


def test_string_commands_and_redis_style_outputs():
    """Basic string commands return Redis-style responses."""
    store = MiniRedis()

    assert store.execute('SET user:1 "Alice"') == "OK"
    assert store.execute("GET user:1") == '"Alice"'
    assert store.execute("EXISTS user:1") == "(integer) 1"
    assert store.execute("DBSIZE") == "(integer) 1"
    assert store.execute("DEL user:1") == "(integer) 1"
    assert store.execute("GET user:1") == "(nil)"
    assert store.execute("DEL user:1") == "(integer) 0"


def test_lru_eviction_respects_used_memory_and_counts_evictions():
    """SET evicts least recently used keys until used_memory fits maxmemory."""
    store = MiniRedis()

    assert store.execute("CONFIG SET maxmemory 16") == "OK"
    assert store.execute("SET a 12345") == "OK"
    assert store.execute("SET b 12345") == "OK"
    assert store.execute("GET a") == '"12345"'
    assert store.execute("SET c 12345") == "OK"

    assert store.execute("GET b") == "(nil)"
    assert store.execute("GET a") == '"12345"'
    assert store.execute("GET c") == '"12345"'
    assert store.info_memory_lines() == [
        "used_memory:12",
        "maxmemory:16",
        "evicted_keys:1",
    ]


def test_single_entry_larger_than_maxmemory_is_rejected():
    """A single oversized entry is not stored and returns OOM."""
    store = MiniRedis()

    assert store.execute("CONFIG SET maxmemory 3") == "OK"
    assert (
        store.execute("SET abc de")
        == "(error) OOM command not allowed when used_memory > 'maxmemory'"
    )
    assert store.execute("EXISTS abc") == "(integer) 0"
    assert store.execute("INFO memory").splitlines() == [
        "used_memory:0",
        "maxmemory:3",
        "evicted_keys:0",
    ]


def test_ttl_expiration_and_overwrite_rules():
    """TTL uses expiration semantics compatible with the assignment."""
    store = MiniRedis()

    assert store.execute("SET session token") == "OK"
    assert store.execute("TTL session") == "(integer) -1"
    assert store.execute("EXPIRE session 1") == "(integer) 1"
    ttl = int(store.execute("TTL session").split()[1].rstrip(")"))
    assert 0 <= ttl <= 1

    time.sleep(1.1)
    assert store.execute("GET session") == "(nil)"
    assert store.execute("TTL session") == "(integer) -2"

    assert store.execute("SET session token") == "OK"
    assert store.execute("EXPIRE session 10") == "(integer) 1"
    assert store.execute("SET session fresh") == "OK"
    assert store.execute("TTL session") == "(integer) -1"


def test_error_handling_and_keys_format():
    """Invalid input and KEYS follow the required output conventions."""
    store = MiniRedis()

    assert store.execute("GET") == "(error) ERR wrong number of arguments for 'GET' command"
    assert store.execute("HELLO") == "(error) ERR unknown command 'HELLO'"
    assert (
        store.execute("CONFIG SET maxmemory abc")
        == "(error) ERR value is not an integer or out of range"
    )
    assert store.execute("KEYS") == "(empty array)"
    assert store.execute("SET user:2 Bob") == "OK"
    assert store.execute("KEYS") == '1. "user:2"'
