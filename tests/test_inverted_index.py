from src.search import InvertedIndex


def test_inverted_index_returns_candidate_documents_for_query_tokens():
    index = InvertedIndex()
    index.add_document(0, ["space", "mission"])
    index.add_document(1, ["baseball", "score"])
    index.add_document(2, ["space", "telescope"])

    assert index.lookup(["space"]) == {0, 2}
    assert index.lookup(["space", "score"]) == {0, 1, 2}
