from datetime import date, timedelta

from app.backtest_models import HistoricalPriceBar
from app.bayesian_confidence_service import (
    BayesianConfidenceService,
)
from app.market_regime_service import (
    MarketRegimeService,
)
from app.multi_timeframe_service import (
    MultiTimeframeService,
)


def bars(
    *,
    symbol: str,
    count: int,
    slope: float,
) -> list[HistoricalPriceBar]:
    start = date(2025, 1, 1)

    return [
        HistoricalPriceBar(
            symbol=symbol,
            trading_date=(
                start + timedelta(days=index)
            ),
            open_price=(
                100 + index * slope - 0.2
            ),
            high_price=(
                100 + index * slope + 1.0
            ),
            low_price=(
                100 + index * slope - 1.0
            ),
            close_price=(
                100 + index * slope
            ),
            volume=1_000_000,
        )
        for index in range(count)
    ]


def test_market_regime_detects_constructive_environment(
) -> None:
    result = MarketRegimeService().analyse(
        series={
            "SPY": bars(
                symbol="SPY",
                count=260,
                slope=0.2,
            ),
            "QQQ": bars(
                symbol="QQQ",
                count=260,
                slope=0.3,
            ),
            "TLT": bars(
                symbol="TLT",
                count=260,
                slope=0.05,
            ),
        }
    )

    assert result.regime in {
        "BULL",
        "CONSTRUCTIVE",
    }
    assert result.buy_threshold <= 80


def test_multi_timeframe_detects_alignment(
) -> None:
    result = MultiTimeframeService().analyse(
        symbol="AAPL",
        series={
            "MONTHLY": bars(
                symbol="AAPL",
                count=30,
                slope=1.0,
            ),
            "WEEKLY": bars(
                symbol="AAPL",
                count=60,
                slope=0.7,
            ),
            "DAILY": bars(
                symbol="AAPL",
                count=220,
                slope=0.2,
            ),
            "FOUR_HOUR": bars(
                symbol="AAPL",
                count=140,
                slope=0.1,
            ),
            "ONE_HOUR": bars(
                symbol="AAPL",
                count=140,
                slope=0.05,
            ),
        },
    )

    assert (
        result.alignment
        == "ALIGNED_BULLISH"
    )
    assert result.composite_score >= 60


def test_bayesian_calibration_updates_prior(
) -> None:
    result = (
        BayesianConfidenceService()
        .calibrate(
            outcomes=(
                {
                    "absolute_return": 0.05,
                },
                {
                    "absolute_return": -0.02,
                },
                {
                    "absolute_return": 0.03,
                },
            )
        )
    )

    assert result.successes == 2
    assert result.failures == 1
    assert 0 < result.posterior_mean < 1
