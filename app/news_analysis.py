import json
from dataclasses import dataclass
from enum import Enum


class NewsSentiment(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"
    NEUTRAL = "NEUTRAL"


class NewsImpactTerm(str, Enum):
    SHORTTERM = "SHORTTERM"
    LONGTERM = "LONGTERM"


class NewsImpactScope(str, Enum):
    GLOBAL = "GLOBAL"
    INDUSTRY = "INDUSTRY"
    STOCK = "STOCK"


@dataclass(frozen=True)
class NewsAnalysis:
    impact_term: NewsImpactTerm
    impact_scope: NewsImpactScope
    scope_items: tuple[str, ...]
    highlights: tuple[str, ...]
    sentiment: NewsSentiment


def parse_news_analysis(
    raw_output: str,
) -> NewsAnalysis:
    try:
        data = json.loads(raw_output)
    except json.JSONDecodeError as error:
        raise ValueError(
            "News-model output was not valid JSON."
        ) from error

    if not isinstance(data, dict):
        raise ValueError(
            "News-model output must be a JSON object."
        )

    try:
        scope_items = data["scope_items"]
        highlights = data["highlights"]

        if not isinstance(scope_items, list):
            raise TypeError(
                "scope_items must be a list."
            )

        if not isinstance(highlights, list):
            raise TypeError(
                "highlights must be a list."
            )

        return NewsAnalysis(
            impact_term=NewsImpactTerm(
                data["impact_term"]
            ),
            impact_scope=NewsImpactScope(
                data["impact_scope"]
            ),
            scope_items=tuple(
                str(item).upper().strip()
                for item in scope_items
                if str(item).strip()
            ),
            highlights=tuple(
                str(item).strip()
                for item in highlights
                if str(item).strip()
            ),
            sentiment=NewsSentiment(
                data["sentiment"]
            ),
        )

    except (
        KeyError,
        TypeError,
        ValueError,
    ) as error:
        raise ValueError(
            "News-model output did not match "
            "the required schema."
        ) from error