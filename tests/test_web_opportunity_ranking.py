from tests.web_test_auth import (
    FakeAuthenticatedService,
    authenticated_client,
)
from web.app import create_app


class FakeReport:
    def to_dictionary(self) -> dict[str, object]:
        return {
            "generated_at": "2026-07-28T08:30:00+00:00",
            "methodology_version": "KAIRO-ORANK-1.0",
            "advisory_only": True,
            "ranking_count": 1,
            "items": [
                {
                    "rank": 1,
                    "symbol": "AAPL",
                    "opportunity_score": 82.4,
                }
            ],
        }


class FakeDictionaryResult:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def to_dictionary(self) -> dict[str, object]:
        return self._payload


class FakeOpportunityRankingService:
    def get_report(self) -> FakeReport:
        return FakeReport()

    def get_history_overview(self, *, window_days: int):
        return FakeDictionaryResult(
            {
                "window_days": window_days,
                "tracked_symbol_count": 1,
                "largest_risers": [{"symbol": "AAPL", "score_change": 3.2}],
                "largest_fallers": [],
            }
        )

    def get_symbol_history(self, *, symbol: str, window_days: int):
        return FakeDictionaryResult(
            {
                "symbol": symbol,
                "window_days": window_days,
                "snapshot_count": 2,
                "score_change": 3.2,
                "rank_change": 1,
            }
        )


def test_returns_authenticated_opportunity_ranking() -> None:
    client = authenticated_client(
        create_app(
            authentication_service_factory=lambda: FakeAuthenticatedService(),
            opportunity_ranking_service_factory=(
                lambda: FakeOpportunityRankingService()
            ),
        )
    )

    response = client.get("/api/opportunity-ranking")

    assert response.status_code == 200
    assert response.json()["methodology_version"] == "KAIRO-ORANK-1.0"
    assert response.json()["items"][0]["symbol"] == "AAPL"


def test_returns_authenticated_opportunity_history_overview() -> None:
    client = authenticated_client(
        create_app(
            authentication_service_factory=lambda: FakeAuthenticatedService(),
            opportunity_ranking_service_factory=(
                lambda: FakeOpportunityRankingService()
            ),
        )
    )

    response = client.get("/api/opportunity-ranking/history?window_days=7")

    assert response.status_code == 200
    assert response.json()["window_days"] == 7
    assert response.json()["largest_risers"][0]["symbol"] == "AAPL"


def test_returns_authenticated_symbol_rank_history() -> None:
    client = authenticated_client(
        create_app(
            authentication_service_factory=lambda: FakeAuthenticatedService(),
            opportunity_ranking_service_factory=(
                lambda: FakeOpportunityRankingService()
            ),
        )
    )

    response = client.get(
        "/api/opportunity-ranking/history/aapl?window_days=30"
    )

    assert response.status_code == 200
    assert response.json()["symbol"] == "AAPL"
    assert response.json()["snapshot_count"] == 2


def test_opportunity_ranking_requires_authentication() -> None:
    from fastapi.testclient import TestClient

    client = TestClient(
        create_app(
            authentication_service_factory=lambda: FakeAuthenticatedService(),
            opportunity_ranking_service_factory=(
                lambda: FakeOpportunityRankingService()
            ),
        )
    )

    response = client.get("/api/opportunity-ranking")

    assert response.status_code == 401
