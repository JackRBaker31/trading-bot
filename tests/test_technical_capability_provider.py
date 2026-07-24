from datetime import date

from app.technical_capability_provider import (
    TechnicalCapabilityProvider,
)
from tests.test_technical_analysis_service import (
    rising_bars,
)


def test_returns_available_assessment(
) -> None:
    provider = (
        TechnicalCapabilityProvider(
            bars_provider=(
                lambda symbol, output_size: (
                    rising_bars(
                        symbol=symbol,
                        count=output_size,
                    )
                )
            ),
            today_provider=(
                lambda: date(
                    2025,
                    9,
                    20,
                )
            ),
        )
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
    assert result.maximum == 20
    assert result.confidence is not None
    assert (
        len(result.evidence) >= 5
    )


def test_provider_failure_is_safe(
) -> None:
    provider = (
        TechnicalCapabilityProvider(
            bars_provider=(
                lambda symbol, output_size: (
                    (_ for _ in ())
                    .throw(
                        RuntimeError(
                            "rate limited"
                        )
                    )
                )
            ),
        )
    )

    result = provider.assess(
        symbol="AAPL",
        opportunity=None,  # type: ignore[arg-type]
        snapshot=None,  # type: ignore[arg-type]
        risk=None,  # type: ignore[arg-type]
        portfolio=None,  # type: ignore[arg-type]
    )

    assert (
        result.status
        == "UNAVAILABLE"
    )
    assert result.score is None
    assert (
        "rate limited"
        in result.blockers[0]
    )
