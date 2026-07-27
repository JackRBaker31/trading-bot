from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import threading
import time

import pytest

from app.backtest_models import HistoricalPriceBar
from app.market_data import (
    MarketDataProviderError,
    MarketDataUnavailableError,
)
from app.market_data_resilience import (
    HistoricalDataCache,
    ResilientHistoricalDataClient,
)


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 7, 27, 12, 0, tzinfo=timezone.utc)

    def now(self) -> datetime:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += timedelta(seconds=seconds)


def bars(symbol: str = "AAPL", count: int = 5) -> list[HistoricalPriceBar]:
    return [
        HistoricalPriceBar(
            symbol=symbol,
            trading_date=date(2026, 7, 1) + timedelta(days=index),
            open_price=100.0 + index,
            high_price=102.0 + index,
            low_price=99.0 + index,
            close_price=101.0 + index,
            volume=1000 + index,
        )
        for index in range(count)
    ]


class Provider:
    def __init__(self, result: list[HistoricalPriceBar] | Exception) -> None:
        self.result = result
        self.calls = 0

    def get_daily_bars(self, *, symbol: str, output_size: int):
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return list(self.result[-output_size:])


def client(
    *,
    provider: Provider,
    cache_dir: Path,
    clock: Clock,
    fresh_ttl: float = 60.0,
    max_per_minute: int = 6,
    failure_threshold: int = 2,
) -> ResilientHistoricalDataClient:
    return ResilientHistoricalDataClient(
        provider=provider,
        cache=HistoricalDataCache(directory=cache_dir),
        fresh_ttl_seconds=fresh_ttl,
        stale_max_age_seconds=3600.0,
        max_requests_per_minute=max_per_minute,
        max_requests_per_day=100,
        circuit_failure_threshold=failure_threshold,
        circuit_cooldown_seconds=120.0,
        now_provider=clock.now,
    )


def test_successful_response_is_cached_and_reused(tmp_path: Path) -> None:
    clock = Clock()
    provider = Provider(bars(count=8))
    service = client(provider=provider, cache_dir=tmp_path, clock=clock)

    first = service.get_daily_bars_result(symbol="AAPL", output_size=5)
    second = service.get_daily_bars_result(symbol="AAPL", output_size=5)

    assert provider.calls == 1
    assert first.data_source == "LIVE"
    assert second.data_source == "CACHE_FRESH"
    assert len(second.bars) == 5
    assert service.health_snapshot()["cache_hits"] == 1


def test_rate_limit_uses_stale_cache_and_opens_circuit(tmp_path: Path) -> None:
    clock = Clock()
    cache = HistoricalDataCache(directory=tmp_path)
    cache.save(symbol="AAPL", bars=bars(count=8), fetched_at=clock.now())
    clock.advance(120.0)
    provider = Provider(
        MarketDataProviderError(
            "rate limited",
            provider="TWELVE_DATA",
            status_code=429,
            retry_after_seconds=30.0,
        )
    )
    service = client(
        provider=provider,
        cache_dir=tmp_path,
        clock=clock,
        fresh_ttl=60.0,
    )

    result = service.get_daily_bars_result(symbol="AAPL", output_size=5)
    health = service.health_snapshot()

    assert result.data_source == "CACHE_STALE"
    assert result.is_stale is True
    assert "rate limit" in (result.warning or "").lower()
    assert provider.calls == 1
    assert health["rate_limit_events"] == 1
    assert health["circuit_state"] == "OPEN"


def test_open_circuit_does_not_call_provider_again(tmp_path: Path) -> None:
    clock = Clock()
    cache = HistoricalDataCache(directory=tmp_path)
    cache.save(symbol="AAPL", bars=bars(count=8), fetched_at=clock.now())
    clock.advance(120.0)
    provider = Provider(
        MarketDataProviderError(
            "rate limited",
            provider="TWELVE_DATA",
            status_code=429,
        )
    )
    service = client(provider=provider, cache_dir=tmp_path, clock=clock)

    service.get_daily_bars_result(symbol="AAPL", output_size=5)
    second = service.get_daily_bars_result(symbol="AAPL", output_size=6)

    assert provider.calls == 1
    assert second.data_source == "CACHE_STALE"
    assert "circuit breaker" in (second.warning or "").lower()


def test_no_cache_returns_structured_unavailable_error(tmp_path: Path) -> None:
    clock = Clock()
    provider = Provider(
        MarketDataProviderError(
            "rate limited",
            provider="TWELVE_DATA",
            status_code=429,
            retry_after_seconds=45.0,
        )
    )
    service = client(provider=provider, cache_dir=tmp_path, clock=clock)

    with pytest.raises(MarketDataUnavailableError) as captured:
        service.get_daily_bars(symbol="MSFT", output_size=5)

    payload = captured.value.to_dictionary()
    assert payload["status"] == "degraded"
    assert payload["code"] == "MARKET_DATA_RATE_LIMITED"
    assert payload["retry_after_seconds"] == 45.0


def test_request_budget_defers_to_cache(tmp_path: Path) -> None:
    clock = Clock()
    cache = HistoricalDataCache(directory=tmp_path)
    cache.save(symbol="AAPL", bars=bars(count=8), fetched_at=clock.now())
    clock.advance(120.0)
    provider = Provider(bars(count=8))
    service = client(
        provider=provider,
        cache_dir=tmp_path,
        clock=clock,
        max_per_minute=1,
    )

    live = service.get_daily_bars_result(symbol="MSFT", output_size=5)
    deferred = service.get_daily_bars_result(symbol="AAPL", output_size=5)

    assert live.data_source == "LIVE"
    assert deferred.data_source == "CACHE_STALE"
    assert provider.calls == 1
    assert service.health_snapshot()["budget_deferrals"] == 1


def test_cache_survives_client_restart(tmp_path: Path) -> None:
    clock = Clock()
    first_provider = Provider(bars(count=8))
    first = client(provider=first_provider, cache_dir=tmp_path, clock=clock)
    first.get_daily_bars(symbol="AAPL", output_size=5)

    second_provider = Provider(RuntimeError("provider should not be called"))
    second = client(provider=second_provider, cache_dir=tmp_path, clock=clock)
    result = second.get_daily_bars_result(symbol="AAPL", output_size=5)

    assert result.data_source == "CACHE_FRESH"
    assert second_provider.calls == 0


def test_simultaneous_identical_requests_are_deduplicated(tmp_path: Path) -> None:
    clock = Clock()
    started = threading.Event()
    release = threading.Event()

    class SlowProvider:
        def __init__(self) -> None:
            self.calls = 0

        def get_daily_bars(self, *, symbol: str, output_size: int):
            self.calls += 1
            started.set()
            release.wait(timeout=2.0)
            return bars(symbol=symbol, count=8)[-output_size:]

    provider = SlowProvider()
    service = ResilientHistoricalDataClient(
        provider=provider,
        cache=HistoricalDataCache(directory=tmp_path),
        fresh_ttl_seconds=60.0,
        stale_max_age_seconds=3600.0,
        max_requests_per_minute=6,
        max_requests_per_day=100,
        circuit_failure_threshold=2,
        circuit_cooldown_seconds=120.0,
        now_provider=clock.now,
    )
    results: list[str] = []

    def request() -> None:
        result = service.get_daily_bars_result(symbol="AAPL", output_size=5)
        results.append(result.data_source)

    leader = threading.Thread(target=request)
    follower = threading.Thread(target=request)
    leader.start()
    assert started.wait(timeout=1.0)
    follower.start()
    time.sleep(0.05)
    release.set()
    leader.join(timeout=2.0)
    follower.join(timeout=2.0)

    assert provider.calls == 1
    assert sorted(results) == ["CACHE_FRESH", "LIVE"]
    assert service.health_snapshot()["deduplicated_requests"] == 1
