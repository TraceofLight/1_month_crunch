from __future__ import annotations

from pathlib import Path
import argparse
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rule_nlp.datasets import build_extraction_cases, build_known_failure_cases
from rule_nlp.extraction import InformationExtractor
from rule_nlp.pipeline import (
    collect_sentiment_errors,
    ensure_data_files,
    evaluate_extraction_cases,
    evaluate_sentiment_cases,
    load_nsmc_sample,
    write_json,
)
from rule_nlp.sentiment import SentimentAnalyzer


DEFAULT_TEXT = (
    "문의: support@company.co.kr, 전화 02-1234-5678, "
    "일시: 2024년 3월 15일, 참가비: 50,000원. "
    "링크 https://www.example.com/path?q=1 서비스가 정말 좋지 않았어요."
)


def main() -> None:
    parser = argparse.ArgumentParser(description="규칙 기반 정보 추출 및 감성 분석 파이프라인")
    parser.add_argument("--text", default=DEFAULT_TEXT, help="단일 문장 분석 입력")
    parser.add_argument("--data-dir", default="data", help="외부 데이터 저장 경로")
    parser.add_argument("--evidence-dir", default="evidence", help="평가 산출물 저장 경로")
    parser.add_argument("--sample-size", type=int, default=200, help="NSMC 균형 평가 샘플 수")
    args = parser.parse_args()

    data_paths = ensure_data_files(args.data_dir)
    evidence_dir = Path(args.evidence_dir)
    evidence_dir.mkdir(parents=True, exist_ok=True)

    extractor = InformationExtractor()
    analyzer = SentimentAnalyzer(lexicon_path=data_paths["knu"])

    extraction_summary = evaluate_extraction_cases(build_extraction_cases(), extractor)
    sentiment_cases = load_nsmc_sample(data_paths["nsmc_test"], sample_size=args.sample_size)
    sentiment_summary = evaluate_sentiment_cases(sentiment_cases, analyzer)
    sentiment_errors = collect_sentiment_errors(sentiment_cases, analyzer, limit=10)
    known_failures = build_known_failure_cases()

    sample_extraction = extractor.extract(args.text)
    sample_sentiment = analyzer.analyze(args.text)
    sample_masked = extractor.mask_personal_info(args.text)

    write_json(evidence_dir / "extraction_metrics.json", extraction_summary)
    write_json(evidence_dir / "sentiment_metrics.json", sentiment_summary)
    write_json(evidence_dir / "sentiment_errors.json", sentiment_errors)
    write_json(evidence_dir / "known_failure_cases.json", known_failures)
    write_json(
        evidence_dir / "sample_run.json",
        {
            "input": args.text,
            "extraction": sample_extraction,
            "sentiment": sample_sentiment,
            "masked": sample_masked,
        },
    )

    summary_text = _format_summary(
        extraction_summary,
        sentiment_summary,
        sentiment_errors,
        data_paths,
        analyzer,
    )
    (evidence_dir / "run_summary.txt").write_text(summary_text, encoding="utf-8")
    print(summary_text)


def _format_summary(
    extraction_summary: dict[str, object],
    sentiment_summary: dict[str, object],
    sentiment_errors: list[dict[str, object]],
    data_paths: dict[str, Path],
    analyzer: SentimentAnalyzer,
) -> str:
    lines = [
        "=== 규칙 기반 정보 추출 및 감성 분석 실행 요약 ===",
        f"KNU 감성사전: {data_paths['knu']}",
        f"NSMC 평가 데이터: {data_paths['nsmc_test']}",
        f"감성 사전 단어 수: {len(analyzer.lexicon)}",
        "",
        "[정보 추출 평가]",
        f"케이스 수: {extraction_summary['case_count']}",
    ]
    metrics = extraction_summary["metrics"]
    assert isinstance(metrics, dict)
    for key, value in metrics.items():
        lines.append(
            f"- {key}: precision={value['precision']}, recall={value['recall']}, "
            f"f1={value['f1']}, tp={value['tp']}, fp={value['fp']}, fn={value['fn']}"
        )

    lines.extend(["", "[감성 분석 평가]"])
    results = sentiment_summary["results"]
    assert isinstance(results, dict)
    for key, payload in results.items():
        metric = payload["metrics"]
        lines.append(
            f"- {key}: accuracy={metric['accuracy']}, precision={metric['precision']}, "
            f"recall={metric['recall']}, f1={metric['f1']}, support={metric['support']}"
        )
    lines.append(f"오분류 저장 건수: {len(sentiment_errors)}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
