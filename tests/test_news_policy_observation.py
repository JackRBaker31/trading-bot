from datetime import (
    datetime,
    timezone,
)

from app.news_analysis import (
    NewsSentiment,
)
from app.news_policy_observation import (
    NewsPolicyObservation,
)
from app.orders import (
    OrderSide,
)


def test_records_shadow_policy_decision() -> None:
    observed_at = datetime(
        2026,
        7,
        17,
        12,
        0,
        tzinfo=timezone.utc,
    )

    expires_at = datetime(
        2026,
        7,
        17,
        12,
        30,
        tzinfo=timezone.utc,
    )

    observation = NewsPolicyObservation(
        symbol="AAPL",
        side=OrderSide.BUY,
        quantity=6,
        analysis_available=True,
        analysis_sentiment=(
            NewsSentiment.NEGATIVE
        ),
        analysis_expires_at=expires_at,
        would_approve=False,
        reason=(
            "Negative stock-specific news "
            "blocks BUY orders."
        ),
        observed_at=observed_at,
    )

    assert observation.symbol == "AAPL"
    assert observation.side is OrderSide.BUY
    assert observation.quantity == 6
    assert observation.analysis_available
    assert (
        observation.analysis_sentiment
        is NewsSentiment.NEGATIVE
    )
    assert (
        observation.analysis_expires_at
        == expires_at
    )
    assert not observation.would_approve
    assert observation.reason == (
        "Negative stock-specific news "
        "blocks BUY orders."
    )
    assert observation.observed_at == observed_at