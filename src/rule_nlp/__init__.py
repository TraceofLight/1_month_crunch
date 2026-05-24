"""Rule-based information extraction and sentiment analysis package."""

from .extraction import InformationExtractor
from .sentiment import SentimentAnalyzer

__all__ = ["InformationExtractor", "SentimentAnalyzer"]
