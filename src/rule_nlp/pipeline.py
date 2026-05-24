"""End-to-end pipeline functions for data loading, evaluation, and evidence."""

from __future__ import annotations

from pathlib import Path
import csv
import json
import random
import urllib.request

from .datasets import PATTERN_KEYS, build_extraction_cases
from .evaluation import compute_binary_metrics, compute_extraction_metrics
from .extraction import InformationExtractor, flatten_normalized
from .sentiment import SentimentAnalyzer


KNU_URL = "https://raw.githubusercontent.com/park1200656/KnuSentiLex/master/data/SentiWord_info.json"
NSMC_TEST_URL = "https://raw.githubusercontent.com/e9t/nsmc/master/ratings_test.txt"


def ensure_data_files(data_dir: str | Path = "data") -> dict[str, Path]:
    data_path = Path(data_dir)
    knu_path = data_path / "KnuSentiLex" / "SentiWord_info.json"
    nsmc_path = data_path / "nsmc" / "ratings_test.txt"
    _download_if_missing(KNU_URL, knu_path)
    _download_if_missing(NSMC_TEST_URL, nsmc_path)
    return {"knu": knu_path, "nsmc_test": nsmc_path}


def evaluate_extraction_cases(
    cases: list[dict[str, object]] | None = None,
    extractor: InformationExtractor | None = None,
) -> dict[str, object]:
    extractor = extractor or InformationExtractor()
    cases = cases or build_extraction_cases()
    gold_by_pattern = {key: [] for key in PATTERN_KEYS}
    pred_by_pattern = {key: [] for key in PATTERN_KEYS}
    predictions: list[dict[str, object]] = []

    for case in cases:
        extracted = extractor.extract(str(case["text"]))
        predictions.append({"id": case["id"], "text": case["text"], "predicted": extracted})
        gold = case["gold"]
        assert isinstance(gold, dict)
        for key in PATTERN_KEYS:
            gold_by_pattern[key].extend(gold[key])
            pred_by_pattern[key].extend(flatten_normalized(extracted[key]))

    return {
        "case_count": len(cases),
        "metrics": {
            key: compute_extraction_metrics(gold_by_pattern[key], pred_by_pattern[key])
            for key in PATTERN_KEYS
        },
        "predictions": predictions,
    }


def load_nsmc_sample(
    path: str | Path,
    sample_size: int = 200,
    seed: int = 42,
) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    with Path(path).open("r", encoding="utf-8") as file:
        reader = csv.DictReader(file, delimiter="\t")
        for row in reader:
            text = (row.get("document") or "").strip()
            label = row.get("label")
            if not text or label not in {"0", "1"}:
                continue
            rows.append({"text": text, "label": "positive" if label == "1" else "negative"})

    positives = [row for row in rows if row["label"] == "positive"]
    negatives = [row for row in rows if row["label"] == "negative"]
    rng = random.Random(seed)
    rng.shuffle(positives)
    rng.shuffle(negatives)
    per_class = sample_size // 2
    sample = positives[:per_class] + negatives[:per_class]
    rng.shuffle(sample)
    return sample


def evaluate_sentiment_cases(
    cases: list[dict[str, str]],
    analyzer: SentimentAnalyzer,
) -> dict[str, object]:
    y_true = [case["label"] for case in cases]
    predictions = {}
    for name, use_rules in {"lexicon_only": False, "with_rules": True}.items():
        y_pred = [_to_binary(analyzer.analyze(case["text"], use_rules=use_rules)["label"]) for case in cases]
        predictions[name] = {
            "metrics": compute_binary_metrics(y_true, y_pred),
            "labels": y_pred,
        }
    return {
        "sample_count": len(cases),
        "label_distribution": {
            "positive": sum(1 for label in y_true if label == "positive"),
            "negative": sum(1 for label in y_true if label == "negative"),
        },
        "results": predictions,
    }


def collect_sentiment_errors(
    cases: list[dict[str, str]],
    analyzer: SentimentAnalyzer,
    limit: int = 10,
) -> list[dict[str, object]]:
    errors: list[dict[str, object]] = []
    for case in cases:
        analysis = analyzer.analyze(case["text"], use_rules=True)
        predicted = _to_binary(analysis["label"])
        if predicted == case["label"]:
            continue
        errors.append(
            {
                "text": case["text"],
                "gold": case["label"],
                "predicted": predicted,
                "score": analysis["score"],
                "matches": analysis["matches"],
            }
        )
        if len(errors) >= limit:
            break
    return errors


def write_json(path: str | Path, payload: object) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def _download_if_missing(url: str, path: Path) -> None:
    if path.exists() and path.stat().st_size > 0:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(url, headers={"User-Agent": "ai-assignment-rule-nlp/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        path.write_bytes(response.read())


def _to_binary(label: object) -> str:
    return "positive" if label == "positive" else "negative"
