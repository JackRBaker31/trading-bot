from datetime import date, timedelta

from app.backtest_models import (
    HistoricalPriceBar,
)
from app.technical_analysis_service import (
    TechnicalAnalysisService,
)


def rising_bars(
    *,
    symbol: str = "AAPL",
    count: int = 260,
) -> list[HistoricalPriceBar]:
    start = date(
        2025,
        1,
        1,
    )
    bars: list[
        HistoricalPriceBar
    ] = []

    for index in range(count):
        close = (
            100.0
            + index * 0.35
            + (
                1.5
                if index % 7 == 0
                else 0.0
            )
        )

        bars.append(
            HistoricalPriceBar(
                symbol=symbol,
                trading_date=(
                    start
                    + timedelta(
                        days=index
                    )
                ),
                open_price=(
                    close - 0.4
                ),
                high_price=(
                    close + 1.0
                ),
                low_price=(
                    close - 1.0
                ),
                close_price=close,
                volume=(
                    1_000_000
                    + index * 2_000
                ),
            )
        )

    return bars


def test_scores_constructive_rising_market(
) -> None:
    analysis = (
        TechnicalAnalysisService()
        .analyse(
            symbol="AAPL",
            bars=rising_bars(),
        )
    )

    assert (
        analysis.score >= 12
    )
    assert (
        analysis.maximum == 20
    )
    assert (
        analysis.confidence > 0.90
    )
    assert analysis.trend in {
        "STRONG_UPTREND",
        "UPTREND",
    }
    assert (
        len(analysis.metrics) == 5
    )


def test_requires_two_hundred_bars(
) -> None:
    try:
        TechnicalAnalysisService().analyse(
            symbol="AAPL",
            bars=rising_bars(
                count=199
            ),
        )
    except ValueError as error:
        assert (
            "At least 200"
            in str(error)
        )
    else:
        raise AssertionError(
            "Expected ValueError."
        )
