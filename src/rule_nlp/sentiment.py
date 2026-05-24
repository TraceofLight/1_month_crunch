"""Lexicon based Korean sentiment analysis with simple rule handling."""

from __future__ import annotations

from pathlib import Path
import json
import re
from typing import Mapping


TOKEN_RE = re.compile(r"[A-Za-z0-9]+|[가-힣]+")
DEFAULT_KNU_PATH = Path("data/KnuSentiLex/SentiWord_info.json")
BLOCKED_SINGLE_CHAR_STEMS = {"정"}


DOMAIN_SENTIMENT_LEXICON: dict[str, int] = {
    "친절": 2,
    "빠르": 2,
    "정확": 2,
    "만족": 2,
    "추천": 2,
    "재구매": 2,
    "해결": 2,
    "깔끔": 1,
    "편리": 2,
    "안정": 2,
    "가성비": 2,
    "신뢰": 2,
    "감동": 3,
    "최고": 3,
    "훌륭": 3,
    "좋": 2,
    "싫": -2,
    "맛있": 2,
    "재밌": 2,
    "재미있": 2,
    "명작": 3,
    "편안": 1,
    "불만": -2,
    "실망": -2,
    "느리": -2,
    "지연": -2,
    "환불": -1,
    "오류": -2,
    "고장": -2,
    "불친절": -2,
    "비싸": -2,
    "최악": -3,
    "나쁘": -2,
    "별로": -1,
    "짜증": -2,
    "불편": -2,
    "문제": -1,
    "누락": -2,
    "파손": -2,
    "취소": -1,
    "답답": -2,
    "끊김": -2,
    "노잼": -3,
    "지루": -2,
    "아쉽": -1,
}


DEFAULT_INTENSIFIERS: dict[str, float] = {
    "매우": 1.5,
    "정말": 1.5,
    "너무": 1.4,
    "아주": 1.4,
    "완전": 1.6,
    "굉장히": 1.5,
    "진짜": 1.4,
    "대단히": 1.5,
    "엄청": 1.6,
    "몹시": 1.5,
}


NEGATION_PREFIXES = ("안", "못")
NEGATION_STARTS = ("않", "없", "아니", "못하")
NEGATION_EXACT = {"안", "못"}
STRIP_SUFFIXES = (
    "스럽고",
    "스럽다",
    "스럽",
    "했습니다",
    "합니다",
    "했어요",
    "해요",
    "네요",
    "어요",
    "아요",
    "습니다",
    "지만",
    "는데",
    "으며",
    "면서",
    "고",
    "게",
    "지",
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "도",
    "만",
    "다",
)


class SentimentAnalyzer:
    """Calculate sentiment by summing lexicon scores and applying local rules."""

    def __init__(
        self,
        lexicon: Mapping[str, int] | None = None,
        intensifiers: Mapping[str, float] | None = None,
        lexicon_path: str | Path | None = None,
    ) -> None:
        if lexicon is None:
            lexicon = load_sentiment_lexicon(lexicon_path)
        self.lexicon = dict(lexicon)
        self.intensifiers = dict(DEFAULT_INTENSIFIERS)
        if intensifiers:
            self.intensifiers.update(intensifiers)
        self.stem_lexicon = self._build_stem_lexicon(self.lexicon)

    def analyze(self, text: str, use_rules: bool = True) -> dict[str, object]:
        tokens = self.tokenize(text)
        total = 0.0
        matches: list[dict[str, object]] = []
        negation_events: list[dict[str, object]] = []

        for index, token in enumerate(tokens):
            hit = self._lookup_score(token)
            if hit is None:
                continue
            lexicon_key, base_score = hit
            multiplier = self._intensity_multiplier(tokens, index) if use_rules else 1.0
            negation_count = self._nearby_negation_count(tokens, index) if use_rules else 0
            sign = -1 if negation_count % 2 else 1
            contribution = base_score * multiplier * sign
            total += contribution

            match_info = {
                "token": token,
                "lexicon_key": lexicon_key,
                "base_score": base_score,
                "multiplier": multiplier,
                "negation_count": negation_count,
                "contribution": round(contribution, 4),
            }
            matches.append(match_info)
            if negation_count:
                negation_events.append(match_info)

        rounded = round(total, 4)
        return {
            "tokens": tokens,
            "score": rounded,
            "label": self._label(rounded),
            "matches": matches,
            "negation_events": negation_events,
        }

    @staticmethod
    def tokenize(text: str) -> list[str]:
        spaced = re.sub(r"(?<![가-힣])(안|못)(?=[가-힣]{2,})", r"\1 ", text)
        return TOKEN_RE.findall(spaced)

    @classmethod
    def _build_stem_lexicon(cls, lexicon: Mapping[str, int]) -> dict[str, tuple[str, int]]:
        stems: dict[str, tuple[str, int]] = {}
        for word, score in lexicon.items():
            candidates = {word, cls._strip_suffix(word)}
            if word.endswith("하다"):
                candidates.add(word[:-2])
            if word.endswith("다"):
                candidates.add(word[:-1])
            for candidate in candidates:
                if candidate:
                    stems.setdefault(candidate, (word, int(score)))
        return dict(sorted(stems.items(), key=lambda item: len(item[0]), reverse=True))

    def _lookup_score(self, token: str) -> tuple[str, int] | None:
        if token in self.intensifiers or self._is_negator(token):
            return None
        candidates = [token, self._strip_suffix(token)]
        for candidate in candidates:
            if len(candidate) == 1 and candidate in BLOCKED_SINGLE_CHAR_STEMS:
                continue
            if candidate in self.stem_lexicon:
                return self.stem_lexicon[candidate]

        for stem, hit in self.stem_lexicon.items():
            if len(stem) >= 2 and token.startswith(stem):
                return hit
        return None

    @staticmethod
    def _strip_suffix(token: str) -> str:
        stripped = token
        changed = True
        while changed:
            changed = False
            for suffix in STRIP_SUFFIXES:
                if len(stripped) > len(suffix) and stripped.endswith(suffix):
                    stripped = stripped[: -len(suffix)]
                    changed = True
                    break
        return stripped

    def _intensity_multiplier(self, tokens: list[str], index: int) -> float:
        window = tokens[max(0, index - 2) : index]
        multiplier = 1.0
        for token in window:
            multiplier *= self.intensifiers.get(token, 1.0)
        return multiplier

    def _nearby_negation_count(self, tokens: list[str], index: int) -> int:
        start = max(0, index - 2)
        end = min(len(tokens), index + 4)
        context = tokens[start:index] + tokens[index + 1 : end]
        return sum(1 for token in context if self._is_negator(token))

    @staticmethod
    def _is_negator(token: str) -> bool:
        if token in NEGATION_EXACT:
            return True
        return token.startswith(NEGATION_STARTS)

    @staticmethod
    def _label(score: float) -> str:
        if score > 0:
            return "positive"
        if score < 0:
            return "negative"
        return "neutral"


def load_sentiment_lexicon(path: str | Path | None = None) -> dict[str, int]:
    lexicon = dict(DOMAIN_SENTIMENT_LEXICON)
    source_path = Path(path) if path else DEFAULT_KNU_PATH
    if not source_path.exists():
        return lexicon

    with source_path.open("r", encoding="utf-8") as file:
        rows = json.load(file)

    for row in rows:
        word = str(row.get("word", "")).strip()
        polarity = row.get("polarity", 0)
        try:
            score = int(polarity)
        except (TypeError, ValueError):
            continue
        if word and score:
            lexicon[word] = score
    lexicon.update(DOMAIN_SENTIMENT_LEXICON)
    return lexicon
