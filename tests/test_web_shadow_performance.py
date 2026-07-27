from fastapi.testclient import TestClient

from web.app import create_app
from tests.web_test_auth import (
    FakeAuthenticatedService,
    authenticated_client,
)


class FakeReport:
    def to_dictionary(self):
        return {
            "total_decision_count": 25,
            "trading_impact": "NONE",
        }


class FakePerformanceService:
    def get_report(self):
        return FakeReport()


class FakeGraduationStatus:
    def to_dictionary(self):
        return {
            "eligible": False,
            "status": "RESEARCH_ONLY",
            "trading_impact": "NONE",
        }


class FakeGraduationService:
    def get_status(self):
        return FakeGraduationStatus()


def test_returns_shadow_performance() -> None:
    client = authenticated_client(
        create_app(
            authentication_service_factory=(
                lambda: FakeAuthenticatedService()
            ),
            shadow_performance_service_factory=(
                lambda: FakePerformanceService()
            ),
            intelligence_graduation_service_factory=(
                lambda: FakeGraduationService()
            ),
        )
    )

    response = client.get(
        "/api/shadow-performance"
    )

    assert response.status_code == 200
    assert response.json()[
        "total_decision_count"
    ] == 25
    assert response.json()[
        "trading_impact"
    ] == "NONE"


def test_returns_graduation_status() -> None:
    client = authenticated_client(
        create_app(
            authentication_service_factory=(
                lambda: FakeAuthenticatedService()
            ),
            shadow_performance_service_factory=(
                lambda: FakePerformanceService()
            ),
            intelligence_graduation_service_factory=(
                lambda: FakeGraduationService()
            ),
        )
    )

    response = client.get(
        "/api/intelligence/graduation-status"
    )

    assert response.status_code == 200
    assert response.json()["eligible"] is False
    assert response.json()["status"] == (
        "RESEARCH_ONLY"
    )
