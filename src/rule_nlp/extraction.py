"""Regular expression based information extraction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Callable, Iterable


TRAILING_URL_PUNCTUATION = ".,!?;:)]}>'\""


@dataclass(frozen=True)
class PatternSpec:
    key: str
    regex: re.Pattern[str]
    normalizer: Callable[[str, re.Match[str]], object | None]


class InformationExtractor:
    """Extract and normalize common customer inquiry fields."""

    # 이메일: 로컬 파트의 점/밑줄/퍼센트/플러스/하이픈과 2단계 이상 도메인을 허용한다.
    # 한글/공백은 제외하여 user.name+tag@sub.domain.co.kr 같은 실무형 주소까지 잡는다.
    EMAIL_RE = re.compile(
        r"""
        (?<![A-Za-z0-9._%+-])
        [A-Za-z0-9._%+-]+
        @
        (?:[A-Za-z0-9-]+\.)+
        [A-Za-z]{2,}
        (?![A-Za-z0-9.-])
        """,
        re.VERBOSE,
    )

    # 전화번호: 국내 휴대전화/지역번호와 +82 국제 표기를 대상으로 한다.
    # 하이픈, 점, 공백, 괄호 구분자를 허용하고 정규화 단계에서 0XX-XXXX-XXXX 형태로 통일한다.
    PHONE_RE = re.compile(
        r"""
        (?<!\d)
        (?:\+82[-.\s]?)?
        \(?
        0?
        (?:2|10|11|16|17|18|19|31|32|33|41|42|43|44|51|52|53|54|55|61|62|63|64|70)
        \)?
        [-.\s]*
        \d{3,4}
        [-.\s]*
        \d{4}
        (?!\d)
        """,
        re.VERBOSE,
    )

    # 날짜: "YYYY년 M월 D일", "YYYY/MM/DD", "YYYY-MM-DD", "YYYY.MM.DD"를 처리한다.
    # 유효하지 않은 월/일은 datetime.date 검증에서 제외된다.
    DATE_RE = re.compile(
        r"""
        (?:
            (?P<ko_year>\d{4})\s*년\s*
            (?P<ko_month>\d{1,2})\s*월\s*
            (?P<ko_day>\d{1,2})\s*일
        )
        |
        (?:
            (?P<num_year>\d{4})
            (?P<num_sep>[-/.])
            (?P<num_month>\d{1,2})
            (?P=num_sep)
            (?P<num_day>\d{1,2})
        )
        """,
        re.VERBOSE,
    )

    # 금액: 원화 숫자 표기(10,000원), 한국어 단위 조합(1억 2천만원), 달러 표기($100)를 잡는다.
    # 날짜/전화번호와 섞이지 않도록 통화 기호 또는 원/만원/달러 같은 통화 단위가 있는 경우만 매칭한다.
    AMOUNT_RE = re.compile(
        r"""
        (?<![\w])
        (?:
            \$\s*\d[\d,]*(?:\.\d+)?
            |
            \d[\d,]*(?:\s*(?:억|천만|백만|십만|만|천|백|십)\s*\d[\d,]*)*
            \s*(?:억원|천만원|백만원|십만원|만원|천원|백원|십원|원|달러|불)
        )
        """,
        re.VERBOSE,
    )

    # URL: http/https와 www로 시작하는 웹 주소를 잡는다.
    # 공백, 따옴표, 꺾쇠괄호 전까지 매칭하고 문장부호는 정규화 단계에서 제거한다.
    URL_RE = re.compile(
        r"""
        (?<![@\w])
        (?:
            https?://
            |
            www\.
        )
        [A-Za-z0-9.-]+\.[A-Za-z]{2,}
        (?:/[^\s<>"']*)?
        """,
        re.VERBOSE,
    )

    # 보너스 개인정보 마스킹: 주민등록번호와 카드번호를 별도 정규식으로 감지한다.
    RRN_RE = re.compile(r"(?<!\d)(\d{6})-([1-4])(\d{6})(?!\d)")
    CARD_RE = re.compile(r"(?<!\d)(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})[-\s]?(\d{4})(?!\d)")

    def __init__(self) -> None:
        self.patterns: tuple[PatternSpec, ...] = (
            PatternSpec("emails", self.EMAIL_RE, self._normalize_email),
            PatternSpec("phones", self.PHONE_RE, self._normalize_phone),
            PatternSpec("dates", self.DATE_RE, self._normalize_date),
            PatternSpec("amounts", self.AMOUNT_RE, self._normalize_amount),
            PatternSpec("urls", self.URL_RE, self._normalize_url),
        )

    def extract(self, text: str) -> dict[str, list[dict[str, object]]]:
        results: dict[str, list[dict[str, object]]] = {spec.key: [] for spec in self.patterns}
        occupied_spans: set[tuple[int, int, str]] = set()

        for spec in self.patterns:
            for match in spec.regex.finditer(text):
                raw = match.group(0).strip()
                normalized = spec.normalizer(raw, match)
                if normalized is None:
                    continue
                span = match.span()
                dedupe_key = (span[0], span[1], spec.key)
                if dedupe_key in occupied_spans:
                    continue
                occupied_spans.add(dedupe_key)
                results[spec.key].append(
                    {
                        "text": raw,
                        "normalized": normalized,
                        "span": span,
                    }
                )

        return results

    def mask_personal_info(self, text: str) -> str:
        masked = self.RRN_RE.sub(r"\1-\2******", text)
        masked = self.CARD_RE.sub(r"\1-****-****-\4", masked)

        def mask_phone(match: re.Match[str]) -> str:
            normalized = self._normalize_phone(match.group(0), match)
            if not isinstance(normalized, str):
                return match.group(0)
            first, _, last = normalized.rpartition("-")
            area = first.split("-")[0]
            return f"{area}-****-{last}"

        return self.PHONE_RE.sub(mask_phone, masked)

    @staticmethod
    def _normalize_email(raw: str, _: re.Match[str]) -> str:
        return raw.lower()

    @staticmethod
    def _normalize_phone(raw: str, _: re.Match[str]) -> str | None:
        digits = re.sub(r"\D", "", raw)
        if digits.startswith("82"):
            digits = "0" + digits[2:]

        area_codes = (
            "010",
            "011",
            "016",
            "017",
            "018",
            "019",
            "031",
            "032",
            "033",
            "041",
            "042",
            "043",
            "044",
            "051",
            "052",
            "053",
            "054",
            "055",
            "061",
            "062",
            "063",
            "064",
            "070",
        )
        if digits.startswith("02"):
            area, rest = "02", digits[2:]
        else:
            area = next((code for code in area_codes if digits.startswith(code)), "")
            rest = digits[len(area) :] if area else ""

        if not area or len(rest) not in (7, 8):
            return None
        middle, last = rest[:-4], rest[-4:]
        return f"{area}-{middle}-{last}"

    @staticmethod
    def _normalize_date(_: str, match: re.Match[str]) -> str | None:
        if match.group("ko_year"):
            year = int(match.group("ko_year"))
            month = int(match.group("ko_month"))
            day = int(match.group("ko_day"))
        else:
            year = int(match.group("num_year"))
            month = int(match.group("num_month"))
            day = int(match.group("num_day"))
        try:
            return date(year, month, day).isoformat()
        except ValueError:
            return None

    @staticmethod
    def _normalize_amount(raw: str, _: re.Match[str]) -> int | None:
        text = raw.strip()
        if text.startswith("$"):
            number = re.sub(r"[^\d.]", "", text)
            return int(float(number)) if number else None

        if "달러" in text or "불" in text:
            number = re.sub(r"[^\d.]", "", text)
            return int(float(number)) if number else None

        compact = re.sub(r"[\s,]", "", text)
        compact = compact.replace("원", "")
        if not compact:
            return None
        if compact.isdigit():
            return int(compact)

        units = {
            "억": 100_000_000,
            "천만": 10_000_000,
            "백만": 1_000_000,
            "십만": 100_000,
            "만": 10_000,
            "천": 1_000,
            "백": 100,
            "십": 10,
        }
        total = 0
        consumed = ""
        for number, unit in re.findall(r"(\d+)(억|천만|백만|십만|만|천|백|십)?", compact):
            multiplier = units.get(unit or "", 1)
            total += int(number) * multiplier
            consumed += f"{number}{unit or ''}"
        if consumed != compact:
            return None
        return total

    @staticmethod
    def _normalize_url(raw: str, _: re.Match[str]) -> str:
        url = raw.rstrip(TRAILING_URL_PUNCTUATION)
        if url.startswith("www."):
            return f"https://{url}"
        return url


def extract_information(text: str) -> dict[str, list[dict[str, object]]]:
    return InformationExtractor().extract(text)


def flatten_normalized(items: Iterable[dict[str, object]]) -> list[object]:
    return [item["normalized"] for item in items]
