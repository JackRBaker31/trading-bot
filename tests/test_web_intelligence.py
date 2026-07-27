from fastapi.testclient import TestClient

from web.app import create_app
from tests.web_test_auth import (
    FakeAuthenticatedService,
    authenticated_client,
)


class FakeIntelligenceResult:
    def to_dictionary(self):
        return {
            "market_outlook": "PROMISING",
            "confidence": 0.55,
            "trading_readiness": "NOT_READY",
            "top_opportunities": [],
        }


class FakeIntelligenceService:
    def get_snapshot(self):
        return FakeIntelligenceResult()


class FakeStatusService:
    def get_status(self, *, request):
        del request

        class Result:
            def to_dictionary(self):
                return {}

        return Result()


class FakeHistoryService:
    def initialize(self):
        pass

    def list_recent(self, **kwargs):
        del kwargs
        return ()


def test_returns_intelligence_snapshot():
    app = create_app(
        authentication_service_factory=(
            lambda: FakeAuthenticatedService()
        ),
        intelligence_service_factory=(
            lambda: FakeIntelligenceService()
        ),
        system_status_service_factory=(
            lambda: FakeStatusService()
        ),
        run_history_service_factory=(
            lambda: FakeHistoryService()
        ),
    )
    response = authenticated_client(app).get(
        "/api/intelligence/snapshot"
    )

    assert response.status_code == 200
    assert response.json()[
        "market_outlook"
    ] == "PROMISING"
    assert response.json()["confidence"] == 0.55
