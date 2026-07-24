from datetime import date

from app.macro_capability_provider import MacroCapabilityProvider
from tests.test_macro_analysis_service import bars


def test_returns_available_macro_assessment() -> None:
    slopes = {"SPY": 0.20, "QQQ": 0.28, "TLT": 0.08}
    provider = MacroCapabilityProvider(
        bars_provider=lambda symbol, output_size: bars(
            symbol=symbol,
            slope=slopes[symbol],
            count=output_size,
        ),
        today_provider=lambda: date(2025, 9, 20),
    )
    result = provider.assess(
        symbol="AAPL",
        opportunity=None,  # type: ignore[arg-type]
        snapshot=None,  # type: ignore[arg-type]
        risk=None,  # type: ignore[arg-type]
        portfolio=None,  # type: ignore[arg-type]
    )
    assert result.status == "AVAILABLE"
    assert result.score is not None
    assert result.maximum == 10
    assert result.confidence is not None
    assert len(result.evidence) >= 5


def test_provider_failure_is_safe() -> None:
    def fail(symbol: str, output_size: int):
        del symbol, output_size
        raise RuntimeError("provider timeout")

    provider = MacroCapabilityProvider(bars_provider=fail)
    result = provider.assess(
        symbol="AAPL",
        opportunity=None,  # type: ignore[arg-type]
        snapshot=None,  # type: ignore[arg-type]
        risk=None,  # type: ignore[arg-type]
        portfolio=None,  # type: ignore[arg-type]
    )
    assert result.status == "UNAVAILABLE"
    assert result.score is None
    assert "provider timeout" in result.blockers[0]
