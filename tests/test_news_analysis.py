import pytest

from app.news_analysis import (
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
    parse_news_analysis,
)


def test_parses_valid_news_analysis() -> None:
    result = parse_news_analysis(
        """
        {
          "impact_term": "SHORTTERM",
          "impact_scope": "STOCK",
          "scope_items": ["aapl"],
          "highlights": [
            "Revenue exceeded expectations."
          ],
          "sentiment": "POSITIVE"
        }
        """
    )

    assert (
        result.impact_term
        == NewsImpactTerm.SHORTTERM
    )

    assert (
        result.impact_scope
        == NewsImpactScope.STOCK
    )

    assert result.scope_items == (
        "AAPL",
    )

    assert result.highlights == (
        "Revenue exceeded expectations.",
    )

    assert (
        result.sentiment
        == NewsSentiment.POSITIVE
    )


def test_rejects_invalid_json() -> None:
    with pytest.raises(
        ValueError,
        match="valid JSON",
    ):
        parse_news_analysis(
            "this is not json"
        )


def test_rejects_non_object_json() -> None:
    with pytest.raises(
        ValueError,
        match="JSON object",
    ):
        parse_news_analysis(
            '["not", "an", "object"]'
        )


def test_rejects_unknown_sentiment() -> None:
    with pytest.raises(
        ValueError,
        match="required schema",
    ):
        parse_news_analysis(
            """
            {
              "impact_term": "SHORTTERM",
              "impact_scope": "STOCK",
              "scope_items": ["AAPL"],
              "highlights": ["Example"],
              "sentiment": "VERY_BULLISH"
            }
            """
        )


def test_rejects_missing_required_field() -> None:
    with pytest.raises(
        ValueError,
        match="required schema",
    ):
        parse_news_analysis(
            """
            {
              "impact_term": "SHORTTERM",
              "impact_scope": "STOCK",
              "scope_items": ["AAPL"],
              "sentiment": "POSITIVE"
            }
            """
        )


def test_rejects_non_list_scope_items() -> None:
    with pytest.raises(
        ValueError,
        match="required schema",
    ):
        parse_news_analysis(
            """
            {
              "impact_term": "SHORTTERM",
              "impact_scope": "STOCK",
              "scope_items": "AAPL",
              "highlights": ["Example"],
              "sentiment": "POSITIVE"
            }
            """
        )