from __future__ import annotations

from collections.abc import Callable, Iterable
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path

from app.market_data_resilience import HistoricalDataCache
from app.universe_governance_models import (
    UniverseCycleCoverage,
    UniverseGovernanceReport,
    UniverseGroupSummary,
    UniverseVersion,
)
from app.universe_governance_repository import UniverseGovernanceRepository
from app.watchlist_loader import WatchlistParseResult, parse_watchlist


class UniverseGovernanceService:
    GOVERNANCE_VERSION = "KAIRO-UGOV-1.0"

    def __init__(
        self,
        *,
        repository: UniverseGovernanceRepository,
        watchlist_path: str = "data/watchlists/core_universe.txt",
        cache: HistoricalDataCache | None = None,
        now_provider: Callable[[], datetime] | None = None,
        daily_request_budget: int | None = None,
    ) -> None:
        self._repository = repository
        self._watchlist_path = watchlist_path
        self._cache = cache or HistoricalDataCache(
            directory=os.getenv(
                "KAIRO_MARKET_DATA_CACHE_DIR",
                "data/runtime/market-data-cache",
            )
        )
        self._now_provider = now_provider or (
            lambda: datetime.now(timezone.utc)
        )
        self._daily_request_budget = daily_request_budget or int(
            os.getenv("KAIRO_MARKET_DATA_MAX_REQUESTS_PER_DAY", "750")
        )

    def initialize(self) -> None:
        self._repository.initialize()
        self.ensure_current_version()

    def ensure_current_version(self) -> UniverseVersion:
        parsed = parse_watchlist(file_path=self._watchlist_path)
        return self._register(parsed)

    def current_context(self) -> tuple[str, int]:
        version = self.ensure_current_version()
        return version.version_id, version.symbol_count

    def record_cycle(
        self,
        *,
        requested_symbols: Iterable[str],
        processed_symbols: Iterable[str],
        source: str = "INTELLIGENCE_CYCLE",
    ) -> UniverseCycleCoverage:
        version = self.ensure_current_version()
        requested = self._symbols(requested_symbols)
        processed = tuple(
            symbol
            for symbol in self._symbols(processed_symbols)
            if symbol in set(requested)
        )
        processed_set = set(processed)
        skipped = tuple(
            symbol for symbol in requested if symbol not in processed_set
        )
        requested_count = len(requested)
        processed_count = len(processed)
        coverage_percent = (
            100.0
            if requested_count == 0
            else processed_count / requested_count * 100.0
        )
        return self._repository.add_coverage(
            coverage=UniverseCycleCoverage(
                coverage_id=0,
                captured_at=self._utc_now(),
                source=source.upper().strip() or "INTELLIGENCE_CYCLE",
                version_id=version.version_id,
                requested_count=requested_count,
                processed_count=processed_count,
                skipped_count=len(skipped),
                coverage_percent=round(coverage_percent, 2),
                processed_symbols=processed,
                skipped_symbols=skipped,
            )
        )

    def get_report(self) -> UniverseGovernanceReport:
        parsed = parse_watchlist(file_path=self._watchlist_path)
        current = self._register(parsed)
        versions = self._repository.list_versions(limit=20)
        previous = next(
            (
                version
                for version in versions
                if version.version_id == current.previous_version_id
            ),
            None,
        )
        coverage = self._repository.list_coverage(limit=30)
        cached_set = set(self._cache.cached_symbols())
        current_set = set(current.symbols)
        cached = tuple(sorted(current_set & cached_set))
        uncached = tuple(sorted(current_set - cached_set))
        cache_percent = (
            100.0
            if current.symbol_count == 0
            else len(cached) / current.symbol_count * 100.0
        )
        budget_percent = (
            0.0
            if self._daily_request_budget <= 0
            else len(uncached) / self._daily_request_budget * 100.0
        )

        group_summaries = tuple(
            UniverseGroupSummary(
                name=name,
                symbol_count=len(symbols),
                share_percent=round(
                    len(symbols) / current.symbol_count * 100.0,
                    2,
                ) if current.symbol_count else 0.0,
                symbols=symbols,
            )
            for name, symbols in sorted(
                current.groups.items(),
                key=lambda item: (-len(item[1]), item[0]),
            )
        )

        warnings: list[str] = []
        if parsed.duplicate_symbols:
            warnings.append(
                "Duplicate symbols were detected and deduplicated: "
                + ", ".join(parsed.duplicate_symbols)
            )
        if parsed.invalid_symbols:
            warnings.append(
                "Malformed symbols are rejected: "
                + ", ".join(parsed.invalid_symbols)
            )
        if cache_percent < 50.0:
            warnings.append(
                "Less than half of the active universe has historical-data cache coverage. "
                "Expect a gradual cache warm-up after expansion."
            )
        if budget_percent >= 50.0:
            warnings.append(
                "A full uncached universe refresh would consume at least half of the configured daily request budget."
            )

        comparison_warning = None
        if previous is not None and previous.version_id != current.version_id:
            comparison_warning = (
                "Absolute ranks before and after this universe change are not directly comparable: "
                f"the active universe changed from {previous.symbol_count} to "
                f"{current.symbol_count} symbols."
            )

        eligibility_status = (
            "INVALID"
            if parsed.invalid_symbols
            else "VALID_WITH_DUPLICATES"
            if parsed.duplicate_symbols
            else "VALID"
        )

        return UniverseGovernanceReport(
            generated_at=self._utc_now(),
            governance_version=self.GOVERNANCE_VERSION,
            source_path=str(Path(self._watchlist_path)),
            current_version=current,
            previous_version=previous,
            version_count=len(versions),
            group_summaries=group_summaries,
            duplicate_symbols=parsed.duplicate_symbols,
            invalid_symbols=parsed.invalid_symbols,
            eligibility_status=eligibility_status,
            cached_symbol_count=len(cached),
            uncached_symbol_count=len(uncached),
            cache_coverage_percent=round(cache_percent, 2),
            cached_symbols=cached,
            uncached_symbols=uncached,
            estimated_live_requests=len(uncached),
            daily_request_budget=self._daily_request_budget,
            estimated_budget_percent=round(budget_percent, 2),
            latest_cycle_coverage=(coverage[0] if coverage else None),
            recent_cycle_coverage=coverage,
            versions=versions,
            rank_comparability_warning=comparison_warning,
            warnings=tuple(warnings),
        )

    def _register(self, parsed: WatchlistParseResult) -> UniverseVersion:
        checksum = self._checksum(parsed)
        existing = self._repository.get_by_checksum(checksum=checksum)
        if existing is not None:
            return existing

        previous = self._repository.latest_version()
        current_symbols = parsed.symbol_values
        previous_set = set(() if previous is None else previous.symbols)
        current_set = set(current_symbols)
        version = UniverseVersion(
            version_id=(
                f"KAIRO-U-{len(current_symbols)}-{checksum[:12].upper()}"
            ),
            checksum=checksum,
            created_at=self._utc_now(),
            source_path=parsed.file_path,
            symbol_count=len(current_symbols),
            groups=parsed.groups,
            symbols=current_symbols,
            previous_version_id=(
                None if previous is None else previous.version_id
            ),
            added_symbols=tuple(sorted(current_set - previous_set)),
            removed_symbols=tuple(sorted(previous_set - current_set)),
        )
        self._repository.add_version(version=version)
        return version

    @staticmethod
    def _checksum(parsed: WatchlistParseResult) -> str:
        payload = {
            "symbols": list(parsed.symbol_values),
            "groups": {
                key: list(values)
                for key, values in parsed.groups.items()
            },
        }
        return hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _symbols(values: Iterable[str]) -> tuple[str, ...]:
        return tuple(
            dict.fromkeys(
                str(value).upper().strip()
                for value in values
                if str(value).strip()
            )
        )

    def _utc_now(self) -> datetime:
        value = self._now_provider()
        if value.tzinfo is None:
            raise ValueError(
                "Universe-governance clock must be timezone-aware."
            )
        return value.astimezone(timezone.utc)
