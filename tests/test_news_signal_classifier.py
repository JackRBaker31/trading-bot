from datetime import (
    datetime,
    timezone,
)

from app.news_signal_classifier import (
    FixedNewsSignalClassifier,
    NewsArticleInput,
)


def test_fixed_classifier_creates_signal() -> None:
    article = NewsArticleInput(
        article_id="article-1",
        symbol="AAPL",
        headline="Apple raises guidance",
        summary="Guidance increased.",
        source="Example News",
        published_at=datetime(
            2026,
            7,
            18,
            12,
            0,
            tzinfo=timezone.utc,
        ),
    )

    signal = FixedNewsSignalClassifier(
        sentiment=0.7,
        relevance=0.9,
        confidence=0.8,
        event_type="GUIDANCE_RAISED",
        is_material=True,
        expiry_hours=12,
    ).classify(
        article=article
    )

    assert signal.symbol == "AAPL"
    assert signal.sentiment == 0.7
    assert signal.is_material is True
    assert (
        signal.expires_at
        > signal.published_at
    )