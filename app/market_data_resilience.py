from collections import deque
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
import json
import logging
from pathlib import Path
import threading
from typing import Callable, Protocol

from app.backtest_models import HistoricalPriceBar
from app.market_data import (
    MarketDataError,
    MarketDataProviderError,
    MarketDataUnavailableError,
)


logger = logging.getLogger(__name__)


class HistoricalBarsProvider(Protocol):
    def get_daily_bars(
        self,
        *,
        symbol: str,
        output_size: int,
    ) -> list[HistoricalPriceBar]: ...


@dataclass(frozen=True)
class HistoricalDataResult:
    bars: tuple[HistoricalPriceBar, ...]
    data_source: str
    is_stale: bool
    refreshed_at: datetime
    age_seconds: float
    warning: str | None = None

    def to_metadata(self) -> dict[str, object]:
        return {
            "data_source": self.data_source,
            "is_stale": self.is_stale,
            "last_updated_at": self.refreshed_at.isoformat(),
            "age_seconds": round(self.age_seconds, 2),
            "bar_count": len(self.bars),
            "warning": self.warning,
        }


@dataclass(frozen=True)
class _CacheRecord:
    symbol: str
    interval: str
    fetched_at: datetime
    bars: tuple[HistoricalPriceBar, ...]

    def subset(self, output_size: int) -> tuple[HistoricalPriceBar, ...]:
        return self.bars[-output_size:]


class HistoricalDataCache:
    def __init__(
        self,
        *,
        directory: str | Path = "data/runtime/market-data-cache",
    ) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def load(
        self,
        *,
        symbol: str,
        interval: str = "1day",
    ) -> _CacheRecord | None:
        path = self._path(symbol=symbol, interval=interval)
        if not path.exists():
            return None

        with self._lock:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                return self._parse_record(payload)
            except (OSError, ValueError, TypeError, KeyError) as error:
                logger.warning(
                    "market_data_cache_read_failed path=%s error=%s",
                    path,
                    error,
                )
                return None

    def save(
        self,
        *,
        symbol: str,
        bars: list[HistoricalPriceBar],
        fetched_at: datetime,
        interval: str = "1day",
    ) -> None:
        if not bars:
            return

        path = self._path(symbol=symbol, interval=interval)
        temp_path = path.with_suffix(".tmp")
        payload = {
            "version": 1,
            "symbol": symbol.upper().strip(),
            "interval": interval,
            "fetched_at": self._normalise_datetime(fetched_at).isoformat(),
            "bars": [
                {
                    "trading_date": bar.trading_date.isoformat(),
                    "open_price": bar.open_price,
                    "high_price": bar.high_price,
                    "low_price": bar.low_price,
                    "close_price": bar.close_price,
                    "volume": bar.volume,
                }
                for bar in bars
            ],
        }

        with self._lock:
            self.directory.mkdir(parents=True, exist_ok=True)
            temp_path.write_text(
                json.dumps(payload, separators=(",", ":")),
                encoding="utf-8",
            )
            temp_path.replace(path)

    def entry_count(self) -> int:
        return len(tuple(self.directory.glob("*.json")))

    def oldest_entry_age_seconds(
        self,
        *,
        now: datetime,
    ) -> float | None:
        ages: list[float] = []
        for path in self.directory.glob("*.json"):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
                fetched_at = self._parse_datetime(payload["fetched_at"])
            except (OSError, ValueError, TypeError, KeyError):
                continue
            ages.append(max(0.0, (now - fetched_at).total_seconds()))
        return max(ages) if ages else None

    def cached_symbols(self) -> tuple[str, ...]:
        symbols: set[str] = set()
        for path in self.directory.glob("*.json"):
            stem = path.stem
            if "__" in stem:
                symbols.add(stem.split("__", 1)[0].upper())
        return tuple(sorted(symbols))

    def _path(self, *, symbol: str, interval: str) -> Path:
        cleaned_symbol = "".join(
            character
            for character in symbol.upper().strip()
            if character.isalnum() or character in {"-", "."}
        )
        cleaned_interval = "".join(
            character
            for character in interval.lower().strip()
            if character.isalnum()
        )
        if not cleaned_symbol or not cleaned_interval:
            raise ValueError("A valid cache key is required.")
        return self.directory / f"{cleaned_symbol}__{cleaned_interval}.json"

    @classmethod
    def _parse_record(cls, payload: object) -> _CacheRecord:
        if not isinstance(payload, dict):
            raise ValueError("Invalid cache payload.")
        symbol = str(payload["symbol"]).upper().strip()
        interval = str(payload["interval"]).lower().strip()
        fetched_at = cls._parse_datetime(payload["fetched_at"])
        raw_bars = payload["bars"]
        if not isinstance(raw_bars, list):
            raise ValueError("Invalid cached bars.")
        bars = tuple(
            HistoricalPriceBar(
                symbol=symbol,
                trading_date=date.fromisoformat(str(item["trading_date"])),
                open_price=float(item["open_price"]),
                high_price=float(item["high_price"]),
                low_price=float(item["low_price"]),
                close_price=float(item["close_price"]),
                volume=int(item["volume"]),
            )
            for item in raw_bars
            if isinstance(item, dict)
        )
        if not bars:
            raise ValueError("Cached bars are empty.")
        return _CacheRecord(
            symbol=symbol,
            interval=interval,
            fetched_at=fetched_at,
            bars=bars,
        )

    @staticmethod
    def _parse_datetime(value: object) -> datetime:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return HistoricalDataCache._normalise_datetime(parsed)

    @staticmethod
    def _normalise_datetime(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


@dataclass
class _InFlightRequest:
    event: threading.Event
    error: BaseException | None = None


class ResilientHistoricalDataClient:
    def __init__(
        self,
        *,
        provider: HistoricalBarsProvider,
        cache: HistoricalDataCache | None = None,
        provider_name: str = "TWELVE_DATA",
        fresh_ttl_seconds: float = 15 * 60,
        stale_max_age_seconds: float = 7 * 24 * 60 * 60,
        max_requests_per_minute: int = 6,
        max_requests_per_day: int = 750,
        circuit_failure_threshold: int = 2,
        circuit_cooldown_seconds: float = 60.0,
        now_provider: Callable[[], datetime] | None = None,
    ) -> None:
        if fresh_ttl_seconds <= 0:
            raise ValueError("Fresh-cache TTL must be positive.")
        if stale_max_age_seconds < fresh_ttl_seconds:
            raise ValueError(
                "Stale-cache maximum age must not be below the fresh TTL."
            )
        if max_requests_per_minute <= 0 or max_requests_per_day <= 0:
            raise ValueError("Market-data request budgets must be positive.")
        if circuit_failure_threshold <= 0:
            raise ValueError("Circuit failure threshold must be positive.")
        if circuit_cooldown_seconds <= 0:
            raise ValueError("Circuit cooldown must be positive.")

        self._provider = provider
        self._cache = cache or HistoricalDataCache()
        self._provider_name = provider_name.upper().strip()
        self._fresh_ttl_seconds = fresh_ttl_seconds
        self._stale_max_age_seconds = stale_max_age_seconds
        self._max_requests_per_minute = max_requests_per_minute
        self._max_requests_per_day = max_requests_per_day
        self._circuit_failure_threshold = circuit_failure_threshold
        self._circuit_cooldown_seconds = circuit_cooldown_seconds
        self._now_provider = now_provider or (
            lambda: datetime.now(timezone.utc)
        )

        self._lock = threading.RLock()
        self._inflight: dict[tuple[str, int], _InFlightRequest] = {}
        self._minute_requests: deque[datetime] = deque()
        self._day_requests: deque[datetime] = deque()
        self._circuit_open_until: datetime | None = None
        self._consecutive_failures = 0
        self._last_success_at: datetime | None = None
        self._last_failure_at: datetime | None = None
        self._last_error: str | None = None
        self._last_access: dict[str, object] | None = None

        self._live_requests = 0
        self._cache_hits = 0
        self._stale_fallbacks = 0
        self._failed_requests = 0
        self._rate_limit_events = 0
        self._deduplicated_requests = 0
        self._budget_deferrals = 0

    def get_daily_bars(
        self,
        *,
        symbol: str,
        output_size: int,
    ) -> list[HistoricalPriceBar]:
        return list(
            self.get_daily_bars_result(
                symbol=symbol,
                output_size=output_size,
            ).bars
        )

    def get_daily_bars_result(
        self,
        *,
        symbol: str,
        output_size: int,
    ) -> HistoricalDataResult:
        cleaned_symbol = symbol.upper().strip()
        if not cleaned_symbol:
            raise ValueError("A stock symbol is required.")
        if output_size <= 0:
            raise ValueError("Output size must be positive.")

        now = self._utc_now()
        cached = self._cache.load(symbol=cleaned_symbol)
        fresh_result = self._fresh_cache_result(
            cached=cached,
            output_size=output_size,
            now=now,
        )
        if fresh_result is not None:
            with self._lock:
                self._cache_hits += 1
                self._record_access(
                    symbol=cleaned_symbol,
                    output_size=output_size,
                    result=fresh_result,
                )
            return fresh_result

        key = (cleaned_symbol, output_size)
        with self._lock:
            inflight = self._inflight.get(key)
            if inflight is None:
                inflight = _InFlightRequest(event=threading.Event())
                self._inflight[key] = inflight
                leader = True
            else:
                self._deduplicated_requests += 1
                leader = False

        if not leader:
            inflight.event.wait(timeout=45.0)
            cached_after_wait = self._cache.load(symbol=cleaned_symbol)
            if cached_after_wait is not None:
                result = self._cache_result(
                    cached=cached_after_wait,
                    output_size=output_size,
                    now=self._utc_now(),
                    warning=(
                        "Shared an in-flight market-data request; "
                        "the resulting cached dataset was reused."
                    ),
                )
                with self._lock:
                    self._cache_hits += 1
                    self._record_access(
                        symbol=cleaned_symbol,
                        output_size=output_size,
                        result=result,
                    )
                return result
            if inflight.error is not None:
                raise inflight.error
            raise MarketDataUnavailableError(
                f"Market data was not produced for {cleaned_symbol}.",
                code="INFLIGHT_REQUEST_FAILED",
                provider=self._provider_name,
            )

        try:
            return self._load_as_leader(
                symbol=cleaned_symbol,
                output_size=output_size,
                cached=cached,
                now=now,
            )
        except BaseException as error:
            inflight.error = error
            raise
        finally:
            inflight.event.set()
            with self._lock:
                self._inflight.pop(key, None)

    def health_snapshot(self) -> dict[str, object]:
        now = self._utc_now()
        with self._lock:
            self._prune_request_history(now)
            circuit_state = self._circuit_state(now)
            total_served = self._live_requests + self._cache_hits + self._stale_fallbacks
            cache_served = self._cache_hits + self._stale_fallbacks
            cache_hit_rate = (
                cache_served / total_served * 100.0
                if total_served > 0
                else 0.0
            )
            cached_entries = self._cache.entry_count()
            unrecovered_failure = (
                self._last_failure_at is not None
                and (
                    self._last_success_at is None
                    or self._last_failure_at > self._last_success_at
                )
            )
            status = "HEALTHY"
            if circuit_state == "OPEN" or unrecovered_failure:
                status = "DEGRADED"
            if (
                self._last_success_at is None
                and self._failed_requests > 0
                and cached_entries == 0
            ):
                status = "UNAVAILABLE"

            return {
                "provider": self._provider_name,
                "status": status,
                "cache_hit_rate_percent": round(cache_hit_rate, 1),
                "live_requests": self._live_requests,
                "cache_hits": self._cache_hits,
                "stale_fallbacks": self._stale_fallbacks,
                "failed_requests": self._failed_requests,
                "rate_limit_events": self._rate_limit_events,
                "deduplicated_requests": self._deduplicated_requests,
                "budget_deferrals": self._budget_deferrals,
                "requests_last_minute": len(self._minute_requests),
                "requests_today": len(self._day_requests),
                "max_requests_per_minute": self._max_requests_per_minute,
                "max_requests_per_day": self._max_requests_per_day,
                "cached_entries": cached_entries,
                "cached_symbols": len(self._cache.cached_symbols()),
                "oldest_cache_age_seconds": self._cache.oldest_entry_age_seconds(
                    now=now
                ),
                "fresh_ttl_seconds": self._fresh_ttl_seconds,
                "stale_max_age_seconds": self._stale_max_age_seconds,
                "circuit_state": circuit_state,
                "circuit_open_until": (
                    None
                    if self._circuit_open_until is None
                    else self._circuit_open_until.isoformat()
                ),
                "consecutive_failures": self._consecutive_failures,
                "last_success_at": (
                    None
                    if self._last_success_at is None
                    else self._last_success_at.isoformat()
                ),
                "last_failure_at": (
                    None
                    if self._last_failure_at is None
                    else self._last_failure_at.isoformat()
                ),
                "last_error": self._last_error,
                "last_access": dict(self._last_access or {}),
                "cache_directory": str(self._cache.directory),
            }

    def _load_as_leader(
        self,
        *,
        symbol: str,
        output_size: int,
        cached: _CacheRecord | None,
        now: datetime,
    ) -> HistoricalDataResult:
        restriction = self._provider_restriction(now)
        if restriction is not None:
            code, message, retry_after = restriction
            with self._lock:
                if code == "RATE_BUDGET_EXHAUSTED":
                    self._budget_deferrals += 1
            return self._fallback_or_raise(
                symbol=symbol,
                output_size=output_size,
                cached=cached,
                now=now,
                warning=message,
                code=code,
                retry_after_seconds=retry_after,
            )

        self._reserve_provider_request(now)
        try:
            bars = self._provider.get_daily_bars(
                symbol=symbol,
                output_size=output_size,
            )
        except MarketDataError as error:
            return self._handle_provider_failure(
                symbol=symbol,
                output_size=output_size,
                cached=cached,
                now=self._utc_now(),
                error=error,
            )

        refreshed_at = self._utc_now()
        self._cache.save(
            symbol=symbol,
            bars=bars,
            fetched_at=refreshed_at,
        )
        result = HistoricalDataResult(
            bars=tuple(bars[-output_size:]),
            data_source="LIVE",
            is_stale=False,
            refreshed_at=refreshed_at,
            age_seconds=0.0,
        )
        with self._lock:
            self._live_requests += 1
            self._consecutive_failures = 0
            self._circuit_open_until = None
            self._last_success_at = refreshed_at
            self._last_error = None
            self._record_access(
                symbol=symbol,
                output_size=output_size,
                result=result,
            )
        return result

    def _handle_provider_failure(
        self,
        *,
        symbol: str,
        output_size: int,
        cached: _CacheRecord | None,
        now: datetime,
        error: MarketDataError,
    ) -> HistoricalDataResult:
        rate_limited = (
            isinstance(error, MarketDataProviderError)
            and error.rate_limited
        )
        retry_after = (
            error.retry_after_seconds
            if isinstance(error, MarketDataProviderError)
            else None
        )
        with self._lock:
            self._failed_requests += 1
            self._consecutive_failures += 1
            self._last_failure_at = now
            self._last_error = str(error)
            if rate_limited:
                self._rate_limit_events += 1
            if (
                rate_limited
                or self._consecutive_failures
                >= self._circuit_failure_threshold
            ):
                cooldown = max(
                    self._circuit_cooldown_seconds,
                    retry_after or 0.0,
                )
                self._circuit_open_until = now + timedelta(seconds=cooldown)

        warning = str(error)
        if rate_limited:
            warning = (
                "Market-data provider rate limit reached. "
                "KAIRO is serving the most recent cached dataset."
            )
        return self._fallback_or_raise(
            symbol=symbol,
            output_size=output_size,
            cached=cached,
            now=now,
            warning=warning,
            code=(
                "MARKET_DATA_RATE_LIMITED"
                if rate_limited
                else "MARKET_DATA_PROVIDER_FAILED"
            ),
            retry_after_seconds=retry_after,
        )

    def _fallback_or_raise(
        self,
        *,
        symbol: str,
        output_size: int,
        cached: _CacheRecord | None,
        now: datetime,
        warning: str,
        code: str,
        retry_after_seconds: float | None,
    ) -> HistoricalDataResult:
        if cached is not None:
            age_seconds = max(0.0, (now - cached.fetched_at).total_seconds())
            if age_seconds <= self._stale_max_age_seconds:
                suffix = ""
                if len(cached.bars) < output_size:
                    suffix = (
                        f" Cached history contains {len(cached.bars)} "
                        f"of the requested {output_size} bars."
                    )
                result = self._cache_result(
                    cached=cached,
                    output_size=output_size,
                    now=now,
                    warning=f"{warning}{suffix}",
                )
                with self._lock:
                    self._stale_fallbacks += 1
                    self._record_access(
                        symbol=symbol,
                        output_size=output_size,
                        result=result,
                    )
                return result

        raise MarketDataUnavailableError(
            f"{warning} No usable cached dataset exists for {symbol}.",
            code=code,
            provider=self._provider_name,
            retry_after_seconds=retry_after_seconds,
        )

    def _fresh_cache_result(
        self,
        *,
        cached: _CacheRecord | None,
        output_size: int,
        now: datetime,
    ) -> HistoricalDataResult | None:
        if cached is None or len(cached.bars) < output_size:
            return None
        age_seconds = max(0.0, (now - cached.fetched_at).total_seconds())
        if age_seconds > self._fresh_ttl_seconds:
            return None
        return HistoricalDataResult(
            bars=cached.subset(output_size),
            data_source="CACHE_FRESH",
            is_stale=False,
            refreshed_at=cached.fetched_at,
            age_seconds=age_seconds,
        )

    def _cache_result(
        self,
        *,
        cached: _CacheRecord,
        output_size: int,
        now: datetime,
        warning: str | None,
    ) -> HistoricalDataResult:
        age_seconds = max(0.0, (now - cached.fetched_at).total_seconds())
        return HistoricalDataResult(
            bars=cached.subset(output_size),
            data_source=(
                "CACHE_FRESH"
                if age_seconds <= self._fresh_ttl_seconds
                else "CACHE_STALE"
            ),
            is_stale=age_seconds > self._fresh_ttl_seconds,
            refreshed_at=cached.fetched_at,
            age_seconds=age_seconds,
            warning=warning,
        )

    def _provider_restriction(
        self,
        now: datetime,
    ) -> tuple[str, str, float | None] | None:
        with self._lock:
            self._prune_request_history(now)
            if (
                self._circuit_open_until is not None
                and now < self._circuit_open_until
            ):
                retry_after = max(
                    0.0,
                    (self._circuit_open_until - now).total_seconds(),
                )
                return (
                    "MARKET_DATA_CIRCUIT_OPEN",
                    "Market-data circuit breaker is open; cached data is being used.",
                    retry_after,
                )
            if self._circuit_open_until is not None:
                self._circuit_open_until = None
                self._consecutive_failures = 0

            if len(self._minute_requests) >= self._max_requests_per_minute:
                oldest = self._minute_requests[0]
                retry_after = max(
                    0.0,
                    60.0 - (now - oldest).total_seconds(),
                )
                return (
                    "RATE_BUDGET_EXHAUSTED",
                    "KAIRO's market-data minute budget is exhausted; cached data is being used.",
                    retry_after,
                )
            if len(self._day_requests) >= self._max_requests_per_day:
                return (
                    "RATE_BUDGET_EXHAUSTED",
                    "KAIRO's daily market-data budget is exhausted; cached data is being used.",
                    None,
                )
        return None

    def _reserve_provider_request(self, now: datetime) -> None:
        with self._lock:
            self._minute_requests.append(now)
            self._day_requests.append(now)

    def _prune_request_history(self, now: datetime) -> None:
        minute_cutoff = now - timedelta(minutes=1)
        day_cutoff = now - timedelta(days=1)
        while self._minute_requests and self._minute_requests[0] <= minute_cutoff:
            self._minute_requests.popleft()
        while self._day_requests and self._day_requests[0] <= day_cutoff:
            self._day_requests.popleft()

    def _circuit_state(self, now: datetime) -> str:
        if self._circuit_open_until is None:
            return "CLOSED"
        if now < self._circuit_open_until:
            return "OPEN"
        return "READY_FOR_RETRY"

    def _record_access(
        self,
        *,
        symbol: str,
        output_size: int,
        result: HistoricalDataResult,
    ) -> None:
        self._last_access = {
            "symbol": symbol,
            "output_size": output_size,
            **result.to_metadata(),
        }

    def _utc_now(self) -> datetime:
        value = self._now_provider()
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
