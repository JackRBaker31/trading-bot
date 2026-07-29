from datetime import datetime, timezone

from app.market_data_resilience import HistoricalDataCache
from app.universe_governance_repository import UniverseGovernanceRepository
from app.universe_governance_service import UniverseGovernanceService


NOW = datetime(2026, 7, 29, 12, 0, tzinfo=timezone.utc)


def service(tmp_path, watchlist_text: str) -> UniverseGovernanceService:
    watchlist = tmp_path / "core_universe.txt"
    watchlist.write_text(watchlist_text.strip(), encoding="utf-8")
    return UniverseGovernanceService(
        repository=UniverseGovernanceRepository(
            database_path=str(tmp_path / "app.db")
        ),
        watchlist_path=str(watchlist),
        cache=HistoricalDataCache(directory=tmp_path / "cache"),
        now_provider=lambda: NOW,
        daily_request_budget=750,
    )


def test_versions_current_universe_and_sector_distribution(tmp_path) -> None:
    governance = service(
        tmp_path,
        """
# Technology
AAPL
MSFT
# Healthcare
LLY
""",
    )
    governance.initialize()

    report = governance.get_report()

    assert report.current_version.symbol_count == 3
    assert report.current_version.version_id.startswith("KAIRO-U-3-")
    assert report.eligibility_status == "VALID"
    assert report.version_count == 1
    assert report.group_summaries[0].symbol_count == 2
    assert report.uncached_symbol_count == 3
    assert report.estimated_live_requests == 3


def test_detects_new_version_and_rank_comparability_warning(tmp_path) -> None:
    governance = service(
        tmp_path,
        """
# Technology
AAPL
MSFT
""",
    )
    governance.initialize()
    watchlist = tmp_path / "core_universe.txt"
    watchlist.write_text(
        """
# Technology
AAPL
MSFT
NVDA
""".strip(),
        encoding="utf-8",
    )

    report = governance.get_report()

    assert report.version_count == 2
    assert report.current_version.added_symbols == ("NVDA",)
    assert report.previous_version is not None
    assert report.previous_version.symbol_count == 2
    assert report.rank_comparability_warning is not None
    assert "2 to 3 symbols" in report.rank_comparability_warning


def test_records_cycle_coverage_and_skipped_symbols(tmp_path) -> None:
    governance = service(
        tmp_path,
        """
# Technology
AAPL
MSFT
NVDA
""",
    )
    governance.initialize()

    coverage = governance.record_cycle(
        requested_symbols=("AAPL", "MSFT", "NVDA"),
        processed_symbols=("AAPL", "NVDA"),
    )
    report = governance.get_report()

    assert coverage.coverage_percent == 66.67
    assert coverage.skipped_symbols == ("MSFT",)
    assert report.latest_cycle_coverage is not None
    assert report.latest_cycle_coverage.skipped_count == 1
