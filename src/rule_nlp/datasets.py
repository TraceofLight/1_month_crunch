"""Small deterministic datasets used by the assignment pipeline."""

from __future__ import annotations


PATTERN_KEYS = ["emails", "phones", "dates", "amounts", "urls"]


def build_extraction_cases() -> list[dict[str, object]]:
    empty = {key: [] for key in PATTERN_KEYS}

    def item(case_id: str, text: str, key: str, values: list[object]) -> dict[str, object]:
        gold = {pattern: list(items) for pattern, items in empty.items()}
        gold[key] = values
        return {"id": case_id, "text": text, "gold": gold}

    return [
        item("email-01", "문의는 user@domain.com 으로 주세요.", "emails", ["user@domain.com"]),
        item(
            "email-02",
            "담당자 메일은 user.name@sub.domain.co.kr입니다.",
            "emails",
            ["user.name@sub.domain.co.kr"],
        ),
        item("email-03", "VIP 주소 help+vip@shop.io 확인.", "emails", ["help+vip@shop.io"]),
        item("email-04", "운영 계정 admin_01@example.co 입니다.", "emails", ["admin_01@example.co"]),
        item("email-05", "지원 first-last@my-domain.net", "emails", ["first-last@my-domain.net"]),
        item("email-06", "보고서 a.b_c+tag@service.org", "emails", ["a.b_c+tag@service.org"]),
        item("email-07", "팀 메일 cs.team@company.co.kr", "emails", ["cs.team@company.co.kr"]),
        item("email-08", "알림 no-reply@alerts.example.com", "emails", ["no-reply@alerts.example.com"]),
        item("email-09", "계정 qa123@test-lab.dev", "emails", ["qa123@test-lab.dev"]),
        item("email-10", "영업 sales.korea@biz.example.kr", "emails", ["sales.korea@biz.example.kr"]),
        item("phone-01", "연락처 010-1234-5678", "phones", ["010-1234-5678"]),
        item("phone-02", "사무실 02-123-4567", "phones", ["02-123-4567"]),
        item("phone-03", "본사 031-1234-5678", "phones", ["031-1234-5678"]),
        item("phone-04", "공백 표기 010 9876 5432", "phones", ["010-9876-5432"]),
        item("phone-05", "점 표기 070.2222.3333", "phones", ["070-2222-3333"]),
        item("phone-06", "괄호 표기 (02) 987-6543", "phones", ["02-987-6543"]),
        item("phone-07", "국제 표기 +82-10-5555-6666", "phones", ["010-5555-6666"]),
        item("phone-08", "부산 지점 051 321 7654", "phones", ["051-321-7654"]),
        item("phone-09", "대구 지점 053-444-5555", "phones", ["053-444-5555"]),
        item("phone-10", "세종 지점 044-1234-0000", "phones", ["044-1234-0000"]),
        item("date-01", "일시는 2024년 1월 15일입니다.", "dates", ["2024-01-15"]),
        item("date-02", "기한 2024/01/15까지.", "dates", ["2024-01-15"]),
        item("date-03", "마감 2024-01-15.", "dates", ["2024-01-15"]),
        item("date-04", "점검일 2024.03.05", "dates", ["2024-03-05"]),
        item("date-05", "예약 2025년 12월 3일", "dates", ["2025-12-03"]),
        item("date-06", "납품 2023/7/9", "dates", ["2023-07-09"]),
        item("date-07", "계약 2026-05-25", "dates", ["2026-05-25"]),
        item("date-08", "행사 2024.11.30", "dates", ["2024-11-30"]),
        item("date-09", "발송 2024년 09월 01일", "dates", ["2024-09-01"]),
        item("date-10", "정산일 2024/12/31", "dates", ["2024-12-31"]),
        item("amount-01", "가격은 10,000원입니다.", "amounts", [10_000]),
        item("amount-02", "총액은 1억 2천만원 예정입니다.", "amounts", [120_000_000]),
        item("amount-03", "보증금 $100 필요.", "amounts", [100]),
        item("amount-04", "배송비 3천원.", "amounts", [3_000]),
        item("amount-05", "할인 후 5만원입니다.", "amounts", [50_000]),
        item("amount-06", "계약금 2,500,000원.", "amounts", [2_500_000]),
        item("amount-07", "예산 1억원.", "amounts", [100_000_000]),
        item("amount-08", "수수료 2천5백원.", "amounts", [2_500]),
        item("amount-09", "출장비 15달러.", "amounts", [15]),
        item("amount-10", "추가금 7백원.", "amounts", [700]),
        item("url-01", "링크 https://www.example.com/path?query=value", "urls", ["https://www.example.com/path?query=value"]),
        item("url-02", "홈페이지 http://example.org", "urls", ["http://example.org"]),
        item("url-03", "문서 www.example.net/docs", "urls", ["https://www.example.net/docs"]),
        item("url-04", "결제 https://shop.example.co.kr/pay?id=10", "urls", ["https://shop.example.co.kr/pay?id=10"]),
        item("url-05", "상태 https://status.example.com/", "urls", ["https://status.example.com/"]),
        item("url-06", "FAQ www.help.example.com/faq.", "urls", ["https://www.help.example.com/faq"]),
        item("url-07", "약관 https://example.com/a-b_c", "urls", ["https://example.com/a-b_c"]),
        item("url-08", "검색 https://example.com/search?q=배송&sort=latest", "urls", ["https://example.com/search?q=배송&sort=latest"]),
        item("url-09", "API http://api.example.io/v1/items", "urls", ["http://api.example.io/v1/items"]),
        item("url-10", "공지 www.company.co.kr/news?no=3", "urls", ["https://www.company.co.kr/news?no=3"]),
    ]


def build_known_failure_cases() -> list[dict[str, str]]:
    return [
        {
            "type": "정보 추출",
            "input": "연락처는 공일공-일이삼사-오육칠팔입니다.",
            "cause": "한글 숫자를 아라비아 숫자로 변환하는 규칙이 없다.",
        },
        {
            "type": "정보 추출",
            "input": "다음 주 금요일 오후에 다시 연락 주세요.",
            "cause": "상대 날짜와 요일 표현은 기준일과 달력 해석이 필요하다.",
        },
        {
            "type": "정보 추출",
            "input": "비용은 약 백만원 정도입니다.",
            "cause": "숫자 없는 한글 금액 단위는 현재 금액 정규식의 범위 밖이다.",
        },
        {
            "type": "감성 분석",
            "input": "가격 대비 품질은 괜찮은데 배송이 너무 느려요.",
            "cause": "제품 품질과 배송이라는 서로 다른 측면 감성을 단일 점수로 합산한다.",
        },
        {
            "type": "감성 분석",
            "input": "정말 빨라서 속이 터지겠네요.",
            "cause": "비꼼과 반어는 표면 단어의 극성과 실제 의도가 반대가 될 수 있다.",
        },
        {
            "type": "감성 분석",
            "input": "나쁘지 않은데 다시 사고 싶지는 않아요.",
            "cause": "긴 문장의 부분 부정 범위를 정확히 나누지 못한다.",
        },
    ]
