"""Assignment constraint checks for forbidden built-in collections."""

import ast
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[1] / "mini_redis"


def test_source_does_not_use_forbidden_key_value_collections():
    """Production code avoids dict, set, and collections as storage shortcuts."""
    for path in SOURCE_ROOT.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            assert not isinstance(node, (ast.Dict, ast.Set, ast.DictComp, ast.SetComp)), path
            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name != "collections", path
            if isinstance(node, ast.ImportFrom):
                assert node.module != "collections", path
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in ("dict", "set"), path
