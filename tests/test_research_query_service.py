import json
from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest

from app.application_errors import DataStoreError
from app.news_signal import NewsSignal
from app.news_signal_outcome import NewsSignalOutcome
from app.news_signal_outcome_store import (
    NewsSignalOutcomeStore,
)
from app.news_signal_store import NewsSignalStore
from app.research_query_service import ResearchQueryService


def create_signal(
    *,
    article_id: str,
    symbol: str,
    sentiment: float,
    published_at: datetime,
    confidence: float = 0.8,
    is_material: bool = True,
) -> NewsSignal:
    return NewsSignal(
        article_id=article_id,
        symbol=symbol,
        headline=f"{symbol} headline",
        sentiment=sentiment,
        relevance=1.0,
        confidence=confidence,
        event_type="STOCK_SHORTTERM_POSITIVE",
        is_material=is_material,
        published_at=published_at,
        expires_at=published_at + timedelta(days=1),
        source="test",
        reasoning_summary="Example.",
    )


def create_service(tmp_path) -> ResearchQueryService:
    return ResearchQueryService(
        report_path=str(tmp_path / "report.json"),
        signals_path=str(tmp_path / "signals.jsonl"),
        outcomes_path=str(tmp_path / "outcomes.jsonl"),
    )


def test_returns_missing_latest_report(tmp_path) -> None:
    assert create_service(tmp_path).get_latest_report() is None


def test_loads_latest_report(tmp_path) -> None:
    path = tmp_path / "report.json"
    path.write_text(
        json.dumps({"verdict": "PROMISING"}),
        encoding="utf-8",
    )

    report = create_service(tmp_path).get_latest_report()

    assert report == {"verdict": "PROMISING"}


def test_rejects_invalid_report(tmp_path) -> None:
    (tmp_path / "report.json").write_text(
        "[]",
        encoding="utf-8",
    )

    with pytest.raises(DataStoreError) as captured:
        create_service(tmp_path).get_latest_report()

    assert captured.value.code == "RESEARCH_REPORT_INVALID"


def test_filters_and_pages_signals(tmp_path) -> None:
    store = NewsSignalStore(
        file_path=str(tmp_path / "signals.jsonl")
    )
    first_time = datetime(
        2026, 7, 19, 10, 0,
        tzinfo=timezone.utc,
    )
    store.append(
        signal=create_signal(
            article_id="old",
            symbol="AAPL",
            sentiment=1.0,
            published_at=first_time,
        )
    )
    store.append(
        signal=create_signal(
            article_id="new",
            symbol="AAPL",
            sentiment=1.0,
            published_at=first_time + timedelta(hours=1),
            confidence=0.95,
        )
    )
    store.append(
        signal=create_signal(
            article_id="other",
            symbol="MSFT",
            sentiment=-1.0,
            published_at=first_time + timedelta(hours=2),
        )
    )

    result = create_service(tmp_path).list_signals(
        symbol="aapl",
        sentiment="positive",
        minimum_confidence=0.9,
        limit=10,
    )

    assert result.total_count == 1
    assert result.items[0]["article_id"] == "new"
    assert result.items[0]["sentiment_name"] == "POSITIVE"


def test_filters_outcomes(tmp_path) -> None:
    store = NewsSignalOutcomeStore(
        file_path=str(tmp_path / "outcomes.jsonl")
    )
    observed_at = datetime(
        2026, 7, 19, 12, 0,
        tzinfo=timezone.utc,
    )
    for symbol, horizon in (
        ("AAPL", "1H"),
        ("AAPL", "1D"),
        ("MSFT", "1H"),
    ):
        store.append(
            outcome=NewsSignalOutcome(
                article_id=f"{symbol}-{horizon}",
                symbol=symbol,
                horizon_name=horizon,
                signal_published_at=(
                    observed_at - timedelta(hours=2)
                ),
                observed_at=observed_at,
                reference_price=100.0,
                observed_price=101.0,
                return_percent=1.0,
            )
        )

    result = create_service(tmp_path).list_outcomes(
        symbol="aapl",
        horizon="1h",
    )

    assert result.total_count == 1
    assert result.items[0]["symbol"] == "AAPL"
    assert result.items[0]["horizon_name"] == "1H"


def test_builds_news_summary(tmp_path) -> None:
    service = create_service(tmp_path)
    published_at = datetime(
        2026, 7, 19, 10, 0,
        tzinfo=timezone.utc,
    )
    NewsSignalStore(
        file_path=str(tmp_path / "signals.jsonl")
    ).append(
        signal=create_signal(
            article_id="article-1",
            symbol="AAPL",
            sentiment=1.0,
            published_at=published_at,
        )
    )
    NewsSignalOutcomeStore(
        file_path=str(tmp_path / "outcomes.jsonl")
    ).append(
        outcome=NewsSignalOutcome(
            article_id="article-1",
            symbol="AAPL",
            horizon_name="1H",
            signal_published_at=published_at,
            observed_at=published_at + timedelta(hours=1),
            reference_price=100.0,
            observed_price=102.0,
            return_percent=2.0,
        )
    )

    summary = service.get_news_summary()

    assert summary["signal_count"] == 1
    assert summary["outcome_count"] == 1
    assert summary["sentiment_groups"][0][
        "directional_success_percent"
    ] == 100.0
