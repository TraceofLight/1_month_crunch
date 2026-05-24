from rule_nlp.extraction import InformationExtractor


def test_extracts_and_normalizes_required_patterns_from_mixed_text():
    text = (
        "문의: user.name+vip@sub.domain.co.kr, 전화 (02) 123-4567, "
        "예약일 2024년 1월 5일, 예산 1억 2천만원, "
        "링크 https://www.example.com/path?query=value."
    )

    result = InformationExtractor().extract(text)

    assert result["emails"][0]["normalized"] == "user.name+vip@sub.domain.co.kr"
    assert result["phones"][0]["normalized"] == "02-123-4567"
    assert result["dates"][0]["normalized"] == "2024-01-05"
    assert result["amounts"][0]["normalized"] == 120_000_000
    assert result["urls"][0]["normalized"] == "https://www.example.com/path?query=value"


def test_handles_multiple_variants_per_required_pattern():
    extractor = InformationExtractor()
    text = (
        "a_b@example.com first-last@service.io "
        "010 1234 5678 031.9876.5432 "
        "2024/03/15 2024-04-16 2024.05.17 "
        "10,000원 5만원 $100 "
        "www.example.org https://shop.example.co.kr/a?b=1"
    )

    result = extractor.extract(text)

    assert [item["normalized"] for item in result["emails"]] == [
        "a_b@example.com",
        "first-last@service.io",
    ]
    assert [item["normalized"] for item in result["phones"]] == [
        "010-1234-5678",
        "031-9876-5432",
    ]
    assert [item["normalized"] for item in result["dates"]] == [
        "2024-03-15",
        "2024-04-16",
        "2024-05-17",
    ]
    assert [item["normalized"] for item in result["amounts"]] == [10_000, 50_000, 100]
    assert [item["normalized"] for item in result["urls"]] == [
        "https://www.example.org",
        "https://shop.example.co.kr/a?b=1",
    ]


def test_masks_bonus_personal_information_patterns():
    text = "주민번호 900101-1234567, 카드 1234-5678-9012-3456, 전화 010-1234-5678"

    masked = InformationExtractor().mask_personal_info(text)

    assert "900101-1******" in masked
    assert "1234-****-****-3456" in masked
    assert "010-****-5678" in masked


def test_email_boundary_allows_korean_sentence_suffix():
    result = InformationExtractor().extract("담당자 메일은 user.name@sub.domain.co.kr입니다.")

    assert result["emails"][0]["normalized"] == "user.name@sub.domain.co.kr"
