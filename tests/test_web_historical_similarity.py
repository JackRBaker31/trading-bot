from tests.web_test_auth import (
    FakeAuthenticatedService,
    authenticated_client,
)
from web.app import create_app


class FakeReport:
    def to_dictionary(self) -> dict[str, object]:
        return {
            "generated_at": "2026-07-27T12:00:00+00:00",
            "symbol": "AAPL",
            "methodology_version": "KAIRO-HSIM-1.0",
            "candidate_count": 8,
            "matched_case_count": 3,
            "measured_case_count": 2,
            "cases": [],
        }


class FakeHistoricalSimilarityService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def analyse(
        self,
        *,
        symbol: str,
        minimum_similarity_percent: float,
        limit: int,
    ) -> FakeReport:
        self.calls.append(
            {
                "symbol": symbol,
                "minimum_similarity_percent": minimum_similarity_percent,
                "limit": limit,
            }
        )
        return FakeReport()


class MissingHistoricalSimilarityService:
    def analyse(self, **kwargs):
        del kwargs
        raise LookupError("No current investment thesis is available for MSFT.")


def test_returns_authenticated_historical_similarity_report() -> None:
    service = FakeHistoricalSimilarityService()
    client = authenticated_client(
        create_app(
            authentication_service_factory=lambda: FakeAuthenticatedService(),
            historical_similarity_service_factory=lambda: service,
        )
    )

    response = client.get(
        "/api/copilot/historical-similarity/AAPL"
        "?minimum_similarity_percent=72.5&limit=7"
    )

    assert response.status_code == 200
    assert response.json()["methodology_version"] == "KAIRO-HSIM-1.0"
    assert service.calls == [
        {
            "symbol": "AAPL",
            "minimum_similarity_percent": 72.5,
            "limit": 7,
        }
    ]


def test_returns_404_when_current_thesis_is_missing() -> None:
    client = authenticated_client(
        create_app(
            authentication_service_factory=lambda: FakeAuthenticatedService(),
            historical_similarity_service_factory=(
                lambda: MissingHistoricalSimilarityService()
            ),
        )
    )

    response = client.get(
        "/api/copilot/historical-similarity/MSFT"
    )

    assert response.status_code == 404
    assert "MSFT" in response.json()["detail"]
