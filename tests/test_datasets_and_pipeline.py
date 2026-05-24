from rule_nlp.datasets import build_extraction_cases, build_known_failure_cases
from rule_nlp.pipeline import evaluate_extraction_cases


def test_extraction_cases_cover_required_volume_and_patterns():
    cases = build_extraction_cases()
    pattern_counts = {key: 0 for key in ["emails", "phones", "dates", "amounts", "urls"]}

    for case in cases:
        for key, values in case["gold"].items():
            if values:
                pattern_counts[key] += 1

    assert len(cases) >= 50
    assert pattern_counts == {
        "emails": 10,
        "phones": 10,
        "dates": 10,
        "amounts": 10,
        "urls": 10,
    }


def test_failure_cases_have_at_least_five_classified_examples():
    failures = build_known_failure_cases()

    assert len(failures) >= 5
    assert {case["type"] for case in failures} >= {"정보 추출", "감성 분석"}
    assert all(case["cause"] for case in failures)


def test_evaluate_extraction_cases_returns_metrics_for_each_pattern():
    summary = evaluate_extraction_cases(build_extraction_cases()[:5])

    assert set(summary["metrics"]) == {"emails", "phones", "dates", "amounts", "urls"}
    assert summary["case_count"] == 5
