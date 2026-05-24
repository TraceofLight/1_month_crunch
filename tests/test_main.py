from types import SimpleNamespace

import main


def test_search_accepts_topk_and_returns_tuple_results(monkeypatch):
    class FakeEngine:
        def search(self, query, topk=5):
            assert query == "space mission"
            assert topk == 2
            return [
                SimpleNamespace(score=0.9, doc_id=10, snippet="first"),
                SimpleNamespace(score=0.7, doc_id=20, snippet="second"),
            ]

    monkeypatch.setattr(main, "_default_engine", lambda: FakeEngine())

    assert main.search("space mission", topk=2) == [
        (0.9, 10, "first"),
        (0.7, 20, "second"),
    ]
