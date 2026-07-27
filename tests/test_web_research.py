from fastapi.testclient import TestClient

from app.research_query_service import PagedResearchResult
from web.app import create_app
from tests.web_test_auth import (
    FakeAuthenticatedService,
    authenticated_client,
)


class FakeStatusService:
    def get_status(self, *, request):
        del request
        return type(
            "Result",
            (),
            {"to_dictionary": lambda self: {}},
        )()


class FakeHistoryService:
    def initialize(self):
        pass

    def list_recent(self, **kwargs):
        del kwargs
        return ()


class FakeJobService:
    def enqueue(self, **kwargs):
        del kwargs
        raise AssertionError

    def get(self, **kwargs):
        del kwargs
        return None

    def list_recent(self, **kwargs):
        del kwargs
        return ()


class FakeResearchService:
    def __init__(self) -> None:
        self.signal_kwargs = None
        self.outcome_kwargs = None

    def get_latest_report(self):
        return {"verdict": "PROMISING"}

    def list_signals(self, **kwargs):
        self.signal_kwargs = kwargs
        return PagedResearchResult(
            total_count=1,
            offset=kwargs["offset"],
            limit=kwargs["limit"],
            items=({"symbol": "AAPL"},),
        )

    def list_outcomes(self, **kwargs):
        self.outcome_kwargs = kwargs
        return PagedResearchResult(
            total_count=1,
            offset=kwargs["offset"],
            limit=kwargs["limit"],
            items=({"horizon_name": "1H"},),
        )

    def get_news_summary(self):
        return {"signal_count": 19, "outcome_count": 3}


def create_client(research: FakeResearchService) -> TestClient:
    app = create_app(
        authentication_service_factory=(
            lambda: FakeAuthenticatedService()
        ),
        system_status_service_factory=lambda: FakeStatusService(),
        run_history_service_factory=lambda: FakeHistoryService(),
        job_service_factory=lambda: FakeJobService(),
        research_query_service_factory=lambda: research,
    )
    return authenticated_client(app)


def test_returns_latest_research_report() -> None:
    response = create_client(FakeResearchService()).get(
        "/api/research/latest"
    )

    assert response.status_code == 200
    assert response.json() == {
        "available": True,
        "report": {"verdict": "PROMISING"},
    }


def test_filters_news_signals() -> None:
    service = FakeResearchService()
    response = create_client(service).get(
        "/api/news/signals"
        "?symbol=aapl"
        "&sentiment=positive"
        "&minimum_confidence=0.8"
        "&limit=10"
    )

    assert response.status_code == 200
    assert response.json()["items"] == [{"symbol": "AAPL"}]
    assert service.signal_kwargs["symbol"] == "aapl"
    assert service.signal_kwargs["minimum_confidence"] == 0.8


def test_filters_news_outcomes() -> None:
    service = FakeResearchService()
    response = create_client(service).get(
        "/api/news/outcomes?symbol=AAPL&horizon=1H"
    )

    assert response.status_code == 200
    assert response.json()["items"] == [
        {"horizon_name": "1H"}
    ]
    assert service.outcome_kwargs["horizon"] == "1H"


def test_returns_news_summary() -> None:
    response = create_client(FakeResearchService()).get(
        "/api/news/summary"
    )

    assert response.status_code == 200
    assert response.json()["signal_count"] == 19
