import pytest

from app.news_analysis import (
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from app.news_analysis_service import (
    NewsAnalysisService,
)


class FakeModelClient:
    def __init__(
        self,
        output: str,
    ) -> None:
        self.output = output
        self.articles: list[str] = []

    def analyse(
        self,
        article_text: str,
    ) -> str:
        self.articles.append(
            article_text
        )

        return self.output


def test_returns_parsed_news_analysis() -> None:
    model_client = FakeModelClient(
        output="""
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

    service = NewsAnalysisService(
        model_client=model_client  # type: ignore[arg-type]
    )

    result = service.analyse(
        "Apple reported stronger revenue."
    )

    assert model_client.articles == [
        "Apple reported stronger revenue."
    ]

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

    assert (
        result.sentiment
        == NewsSentiment.POSITIVE
    )


def test_rejects_invalid_model_output() -> None:
    service = NewsAnalysisService(
        model_client=FakeModelClient(
            output="not json"
        )  # type: ignore[arg-type]
    )

    with pytest.raises(
        ValueError,
        match="valid JSON",
    ):
        service.analyse(
            "Example article."
        )