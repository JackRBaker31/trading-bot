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


class FakeOpportunityRankingService:
    def get_report(self) -> FakeReport:
        return FakeReport()


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
