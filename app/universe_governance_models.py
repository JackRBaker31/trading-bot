from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True)
class UniverseVersion:
    version_id: str
    checksum: str
    created_at: datetime
    source_path: str
    symbol_count: int
    groups: dict[str, tuple[str, ...]]
    symbols: tuple[str, ...]
    previous_version_id: str | None
    added_symbols: tuple[str, ...]
    removed_symbols: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "version_id": self.version_id,
            "checksum": self.checksum,
            "created_at": self.created_at.isoformat(),
            "source_path": self.source_path,
            "symbol_count": self.symbol_count,
            "groups": {
                key: list(values)
                for key, values in self.groups.items()
            },
            "symbols": list(self.symbols),
            "previous_version_id": self.previous_version_id,
            "added_symbols": list(self.added_symbols),
            "removed_symbols": list(self.removed_symbols),
        }


@dataclass(frozen=True)
class UniverseCycleCoverage:
    coverage_id: int
    captured_at: datetime
    source: str
    version_id: str
    requested_count: int
    processed_count: int
    skipped_count: int
    coverage_percent: float
    processed_symbols: tuple[str, ...]
    skipped_symbols: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "coverage_id": self.coverage_id,
            "captured_at": self.captured_at.isoformat(),
            "source": self.source,
            "version_id": self.version_id,
            "requested_count": self.requested_count,
            "processed_count": self.processed_count,
            "skipped_count": self.skipped_count,
            "coverage_percent": self.coverage_percent,
            "processed_symbols": list(self.processed_symbols),
            "skipped_symbols": list(self.skipped_symbols),
        }


@dataclass(frozen=True)
class UniverseGroupSummary:
    name: str
    symbol_count: int
    share_percent: float
    symbols: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return asdict(self) | {"symbols": list(self.symbols)}


@dataclass(frozen=True)
class UniverseGovernanceReport:
    generated_at: datetime
    governance_version: str
    source_path: str
    current_version: UniverseVersion
    previous_version: UniverseVersion | None
    version_count: int
    group_summaries: tuple[UniverseGroupSummary, ...]
    duplicate_symbols: tuple[str, ...]
    invalid_symbols: tuple[str, ...]
    eligibility_status: str
    cached_symbol_count: int
    uncached_symbol_count: int
    cache_coverage_percent: float
    cached_symbols: tuple[str, ...]
    uncached_symbols: tuple[str, ...]
    estimated_live_requests: int
    daily_request_budget: int
    estimated_budget_percent: float
    latest_cycle_coverage: UniverseCycleCoverage | None
    recent_cycle_coverage: tuple[UniverseCycleCoverage, ...]
    versions: tuple[UniverseVersion, ...]
    rank_comparability_warning: str | None
    warnings: tuple[str, ...]

    def to_dictionary(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at.isoformat(),
            "governance_version": self.governance_version,
            "source_path": self.source_path,
            "current_version": self.current_version.to_dictionary(),
            "previous_version": (
                None
                if self.previous_version is None
                else self.previous_version.to_dictionary()
            ),
            "version_count": self.version_count,
            "group_summaries": [
                item.to_dictionary()
                for item in self.group_summaries
            ],
            "duplicate_symbols": list(self.duplicate_symbols),
            "invalid_symbols": list(self.invalid_symbols),
            "eligibility_status": self.eligibility_status,
            "cached_symbol_count": self.cached_symbol_count,
            "uncached_symbol_count": self.uncached_symbol_count,
            "cache_coverage_percent": self.cache_coverage_percent,
            "cached_symbols": list(self.cached_symbols),
            "uncached_symbols": list(self.uncached_symbols),
            "estimated_live_requests": self.estimated_live_requests,
            "daily_request_budget": self.daily_request_budget,
            "estimated_budget_percent": self.estimated_budget_percent,
            "latest_cycle_coverage": (
                None
                if self.latest_cycle_coverage is None
                else self.latest_cycle_coverage.to_dictionary()
            ),
            "recent_cycle_coverage": [
                item.to_dictionary()
                for item in self.recent_cycle_coverage
            ],
            "versions": [
                item.to_dictionary()
                for item in self.versions
            ],
            "rank_comparability_warning": self.rank_comparability_warning,
            "warnings": list(self.warnings),
        }
