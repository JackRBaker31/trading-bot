from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from app.news_trading_policy import (
    NewsTradingPolicy,
)
from app.orders import (
    Order,
    OrderSide,
)


def create_buy_order(
    symbol: str = "AAPL",
) -> Order:
    return Order(
        symbol=symbol,
        side=OrderSide.BUY,
        quantity=1,
        price=100.00,
    )


def test_blocks_buy_for_matching_negative_stock_news() -> None:
    policy = NewsTradingPolicy()

    analysis = NewsAnalysis(
        impact_term=(
            NewsImpactTerm.SHORTTERM
        ),
        impact_scope=(
            NewsImpactScope.STOCK
        ),
        scope_items=("AAPL",),
        highlights=(
            "Apple received a regulatory penalty",
        ),
        sentiment=(
            NewsSentiment.NEGATIVE
        ),
    )

    approved = policy.approve_order(
        order=create_buy_order(),
        analysis=analysis,
    )

    assert not approved


def test_allows_buy_for_different_stock() -> None:
    policy = NewsTradingPolicy()

    analysis = NewsAnalysis(
        impact_term=(
            NewsImpactTerm.SHORTTERM
        ),
        impact_scope=(
            NewsImpactScope.STOCK
        ),
        scope_items=("MSFT",),
        highlights=(
            "Microsoft received a regulatory penalty",
        ),
        sentiment=(
            NewsSentiment.NEGATIVE
        ),
    )

    approved = policy.approve_order(
        order=create_buy_order(
            symbol="AAPL"
        ),
        analysis=analysis,
    )

    assert approved


def test_allows_buy_for_positive_matching_news() -> None:
    policy = NewsTradingPolicy()

    analysis = NewsAnalysis(
        impact_term=(
            NewsImpactTerm.SHORTTERM
        ),
        impact_scope=(
            NewsImpactScope.STOCK
        ),
        scope_items=("AAPL",),
        highlights=(
            "Apple reported stronger revenue",
        ),
        sentiment=(
            NewsSentiment.POSITIVE
        ),
    )

    approved = policy.approve_order(
        order=create_buy_order(),
        analysis=analysis,
    )

    assert approved