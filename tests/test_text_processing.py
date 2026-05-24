from src.text_processing import TextPreprocessor


def test_preprocessor_lowercases_strips_special_characters_and_stopwords():
    preprocessor = TextPreprocessor(stopwords={"the", "and", "is"})

    tokens = preprocessor.tokenize("The QUICK, brown-fox is here!!! And NASA.")

    assert tokens == ["quick", "brown", "fox", "here", "nasa"]


def test_preprocessor_removes_short_and_numeric_tokens():
    preprocessor = TextPreprocessor(stopwords=set(), min_token_length=2)

    tokens = preprocessor.tokenize("A B2 model 123 reached v2.")

    assert tokens == ["b2", "model", "reached", "v2"]
