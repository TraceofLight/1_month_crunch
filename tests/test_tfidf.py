import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from src.tfidf import NumpyTfidfVectorizer


def test_numpy_tfidf_matches_sklearn_with_smooth_idf_and_l2_norm():
    docs = [
        ["space", "mission", "space", "nasa"],
        ["baseball", "team", "score"],
        ["space", "telescope", "image"],
        ["team", "wins", "baseball", "score"],
    ]
    joined_docs = [" ".join(doc) for doc in docs]

    vectorizer = NumpyTfidfVectorizer(
        smooth_idf=True,
        sublinear_tf=False,
        norm="l2",
        tf_variant="raw",
    )
    actual = vectorizer.fit_transform(docs)

    sklearn_vectorizer = TfidfVectorizer(
        tokenizer=str.split,
        preprocessor=None,
        lowercase=False,
        token_pattern=None,
        vocabulary=vectorizer.vocabulary_,
        smooth_idf=True,
        sublinear_tf=False,
        norm="l2",
    )
    expected = sklearn_vectorizer.fit_transform(joined_docs).toarray()

    assert actual.shape == expected.shape
    assert np.max(np.abs(actual - expected)) <= 1e-6


def test_transform_uses_existing_vocabulary_and_idf():
    docs = [["deep", "space"], ["baseball", "score"]]
    vectorizer = NumpyTfidfVectorizer().fit(docs)

    transformed = vectorizer.transform([["deep", "unknown", "space"]])

    assert transformed.shape == (1, len(vectorizer.vocabulary_))
    assert transformed[0, vectorizer.vocabulary_["deep"]] > 0
    assert "unknown" not in vectorizer.vocabulary_
    assert np.isclose(np.linalg.norm(transformed[0]), 1.0)
