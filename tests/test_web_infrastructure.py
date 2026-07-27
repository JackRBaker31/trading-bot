from fastapi.testclient import TestClient

from web.app import create_app
from tests.web_test_auth import (
    FakeAuthenticatedService,
    authenticated_client,
)


class FakeResult:
    def __init__(self, payload):
        self._payload = payload

    def to_dictionary(self):
        return self._payload


class FakeInfrastructureService:
    def get_status(self):
        return FakeResult(
            {
                "overall_status": "HEALTHY",
                "services": {
                    "job_worker": {
                        "online": True,
                        "status": "IDLE",
                    }
                },
            }
        )

    def get_worker_status(self):
        return FakeResult(
            {
                "name": "job_worker",
                "online": True,
                "status": "IDLE",
            }
        )


def test_returns_infrastructure_status() -> None:
    client = authenticated_client(
        create_app(
            authentication_service_factory=(
                lambda: FakeAuthenticatedService()
            ),
            infrastructure_status_service_factory=(
                lambda: FakeInfrastructureService()
            )
        )
    )

    response = client.get(
        "/api/infrastructure/status"
    )

    assert response.status_code == 200
    assert response.json()["overall_status"] == "HEALTHY"


def test_returns_job_worker_status() -> None:
    client = authenticated_client(
        create_app(
            authentication_service_factory=(
                lambda: FakeAuthenticatedService()
            ),
            infrastructure_status_service_factory=(
                lambda: FakeInfrastructureService()
            )
        )
    )

    response = client.get(
        "/api/workers/job/status"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "IDLE"
