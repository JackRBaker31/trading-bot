from fastapi.testclient import TestClient

from web.app import create_app


class FakeBriefing:
    def to_dictionary(self):
        return {
            "headline": "KAIRO is cautious",
            "market_outlook": "CAUTIOUS",
            "actions": [],
            "trading_impact": "NONE",
        }


class FakeBriefingService:
    def get_briefing(self):
        return FakeBriefing()


def test_returns_daily_briefing() -> None:
    client = TestClient(
        create_app(
            daily_briefing_service_factory=(
                lambda: FakeBriefingService()
            )
        )
    )

    response = client.get(
        "/api/intelligence/briefing"
    )

    assert response.status_code == 200
    assert response.json()["market_outlook"] == (
        "CAUTIOUS"
    )
    assert response.json()["trading_impact"] == (
        "NONE"
    )
