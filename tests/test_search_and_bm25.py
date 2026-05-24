from src.bm25 import BM25SearchEngine
from src.search import SearchEngine, cosine_similarity
from src.text_processing import TextPreprocessor


def test_cosine_search_returns_ranked_snippets():
    docs = [
        "NASA launched a deep space telescope mission.",
        "The baseball team won the final score.",
        "A graphics card renders image pixels.",
    ]
    preprocessor = TextPreprocessor(stopwords={"a", "the"})
    engine = SearchEngine.from_documents(docs, preprocessor=preprocessor)

    results = engine.search("space telescope", topk=2)

    assert results[0].doc_id == 0
    assert results[0].score > results[1].score
    assert "NASA launched" in results[0].snippet


def test_cosine_similarity_handles_zero_vectors():
    scores = cosine_similarity([[0.0, 0.0]], [[1.0, 0.0], [0.0, 0.0]])

    assert scores.tolist() == [[0.0, 0.0]]


def test_bm25_prioritizes_documents_with_query_terms():
    docs = [
        "space telescope telescope mission nasa",
        "baseball team score final",
        "graphics image render",
    ]
    preprocessor = TextPreprocessor(stopwords=set())
    engine = BM25SearchEngine.from_documents(docs, preprocessor=preprocessor)

    results = engine.search("space telescope", topk=2)

    assert results[0].doc_id == 0
    assert results[0].score > 0
