from tests.web_test_auth import (
    FakeAuthenticatedService,
    authenticated_client,
)
from web.app import create_app


class FakeDictionaryResult:
    def to_dictionary(self) -> dict[str, object]:
        return {
            "governance_version": "KAIRO-UGOV-1.0",
            "eligibility_status": "VALID",
            "current_version": {
                "version_id": "KAIRO-U-106-ABC",
                "symbol_count": 106,
            },
            "cache_coverage_percent": 76.4,
        }


class FakeUniverseGovernanceService:
    def get_report(self) -> FakeDictionaryResult:
        return FakeDictionaryResult()


def test_returns_authenticated_universe_governance_report() -> None:
    client = authenticated_client(
        create_app(
            authentication_service_factory=lambda: FakeAuthenticatedService(),
            universe_governance_service_factory=(
                lambda: FakeUniverseGovernanceService()
            ),
        )
    )

    response = client.get("/api/universe-governance")

    assert response.status_code == 200
    assert response.json()["governance_version"] == "KAIRO-UGOV-1.0"
    assert response.json()["current_version"]["symbol_count"] == 106
