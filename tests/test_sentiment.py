from rule_nlp.sentiment import SentimentAnalyzer


def test_scores_positive_sentence_with_intensifier():
    analyzer = SentimentAnalyzer(
        lexicon={"만족": 2, "훌륭": 3},
        intensifiers={"정말": 1.5},
    )

    result = analyzer.analyze("정말 만족스럽고 훌륭해요")

    assert result["label"] == "positive"
    assert result["score"] > 5


def test_negation_flips_positive_sentiment():
    analyzer = SentimentAnalyzer(lexicon={"좋": 2})

    result = analyzer.analyze("응대가 좋지 않다")

    assert result["label"] == "negative"
    assert result["score"] < 0


def test_negation_flips_negative_sentiment_to_positive():
    analyzer = SentimentAnalyzer(lexicon={"나쁘": -2, "불만": -2})

    assert analyzer.analyze("품질이 나쁘지 않다")["label"] == "positive"
    assert analyzer.analyze("불만이 없다")["label"] == "positive"


def test_double_negation_single_pattern_keeps_original_polarity():
    analyzer = SentimentAnalyzer(lexicon={"좋": 2})

    result = analyzer.analyze("서비스가 좋지 않은 것은 아니다")

    assert result["label"] == "positive"
    assert result["negation_events"][0]["negation_count"] == 2


def test_intensifier_is_not_counted_as_sentiment_word_itself():
    analyzer = SentimentAnalyzer(
        lexicon={"정": 1, "좋": 2},
        intensifiers={"정말": 1.5},
    )

    result = analyzer.analyze("정말 좋아요")

    assert result["score"] == 3.0
    assert [match["token"] for match in result["matches"]] == ["좋아요"]


def test_single_character_stems_do_not_overmatch_common_nouns():
    analyzer = SentimentAnalyzer(lexicon={"정": 1, "좋": 2})

    result = analyzer.analyze("정도는 좋아요")

    assert result["score"] == 2.0
    assert [match["token"] for match in result["matches"]] == ["좋아요"]
