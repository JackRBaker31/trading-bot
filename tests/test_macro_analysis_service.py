from datetime import date, timedelta

from app.backtest_models import HistoricalPriceBar
from app.macro_analysis_service import MacroAnalysisService


def bars(
    *,
    symbol: str,
    slope: float,
    count: int = 260,
    volatility: float = 0.0,
) -> list[HistoricalPriceBar]:
    start = date(2025, 1, 1)
    result = []
    for index in range(count):
        wave = volatility if index % 2 == 0 else -volatility
        close = 100.0 + index * slope + wave
        result.append(
            HistoricalPriceBar(
                symbol=symbol,
                trading_date=start + timedelta(days=index),
                open_price=close - 0.2,
                high_price=close + 0.8,
                low_price=close - 0.8,
                close_price=close,
                volume=1_000_000,
            )
        )
    return result


def test_supportive_macro_regime() -> None:
    analysis = MacroAnalysisService().analyse(
        series={
            "SPY": bars(symbol="SPY", slope=0.20),
            "QQQ": bars(symbol="QQQ", slope=0.28),
            "TLT": bars(symbol="TLT", slope=0.08),
        }
    )
    assert analysis.score >= 7
    assert analysis.maximum == 10
    assert analysis.regime in {"RISK_ON", "CONSTRUCTIVE"}
    assert analysis.confidence > 0.90
    assert len(analysis.metrics) == 5


def test_missing_series_is_rejected() -> None:
    try:
        MacroAnalysisService().analyse(
            series={
                "SPY": bars(symbol="SPY", slope=0.2),
                "QQQ": bars(symbol="QQQ", slope=0.2),
            }
        )
    except ValueError as error:
        assert "TLT" in str(error)
    else:
        raise AssertionError("Expected ValueError.")
