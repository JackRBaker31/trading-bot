from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest

from app.copilot_service import CopilotService
from app.infrastructure_status import (
    InfrastructureStatus,
    ServiceHealth,
)
from app.job import (
    JobRecord,
    JobStatus,
    JobType,
)
from app.scheduled_task import (
    CatchUpPolicy,
    ScheduleKind,
    ScheduledTask,
)


NOW = datetime(
    2026,
    7,
    23,
    16,
    0,
    tzinfo=timezone.utc,
)


def healthy_infrastructure(
) -> InfrastructureStatus:
    return InfrastructureStatus(
        generated_at=NOW,
        overall_status="HEALTHY",
        services=(
            ServiceHealth(
                name="api",
                status="ONLINE",
                online=True,
                detail="FastAPI is responding.",
            ),
            ServiceHealth(
                name="storage",
                status="ONLINE",
                online=True,
                detail="Storage is available.",
            ),
            ServiceHealth(
                name="supervisor",
                status="RUNNING",
                online=True,
                detail=(
                    "Automatic recovery is active."
                ),
            ),
            ServiceHealth(
                name="job_worker",
                status="IDLE",
                online=True,
                detail=(
                    "The job worker is healthy."
                ),
            ),
            ServiceHealth(
                name="scheduler",
                status="IDLE",
                online=True,
                detail=(
                    "The scheduler is healthy."
                ),
            ),
        ),
    )


def degraded_infrastructure(
) -> InfrastructureStatus:
    return InfrastructureStatus(
        generated_at=NOW,
        overall_status="DEGRADED",
        services=(
            ServiceHealth(
                name="api",
                status="ONLINE",
                online=True,
                detail="FastAPI is responding.",
            ),
            ServiceHealth(
                name="storage",
                status="ONLINE",
                online=True,
                detail="Storage is available.",
            ),
            ServiceHealth(
                name="supervisor",
                status="RUNNING",
                online=True,
                detail=(
                    "Automatic recovery is active."
                ),
            ),
            ServiceHealth(
                name="job_worker",
                status="STALE",
                online=False,
                detail=(
                    "The job-worker heartbeat is "
                    "stale."
                ),
            ),
            ServiceHealth(
                name="scheduler",
                status="IDLE",
                online=True,
                detail=(
                    "The scheduler is healthy."
                ),
            ),
        ),
    )


def running_job() -> JobRecord:
    return JobRecord(
        job_id="job-running-001",
        job_type=(
            JobType.NEWS_RESEARCH_CYCLE
        ),
        status=JobStatus.RUNNING,
        created_at=NOW - timedelta(
            minutes=2
        ),
        started_at=NOW - timedelta(
            minutes=1
        ),
        payload={},
    )


def failed_job() -> JobRecord:
    return JobRecord(
        job_id="job-failed-001",
        job_type=(
            JobType.INTELLIGENCE_CYCLE
        ),
        status=JobStatus.FAILED,
        created_at=NOW - timedelta(
            minutes=10
        ),
        started_at=NOW - timedelta(
            minutes=9
        ),
        finished_at=NOW - timedelta(
            minutes=8
        ),
        payload={},
        error_code="TEST_FAILURE",
        error_summary=(
            "Market-data provider failed."
        ),
    )


def next_schedule() -> ScheduledTask:
    return ScheduledTask(
        schedule_id="schedule-001",
        task_type=(
            JobType.INTELLIGENCE_CYCLE
        ),
        enabled=True,
        schedule_kind=(
            ScheduleKind.INTERVAL
        ),
        timezone_name="UTC",
        next_run_at=NOW + timedelta(
            minutes=30
        ),
        interval_seconds=3600,
        catch_up_policy=(
            CatchUpPolicy.RUN_ONCE
        ),
    )


def create_service(
    *,
    infrastructure: (
        InfrastructureStatus | None
    ) = None,
    jobs: tuple[JobRecord, ...] = (),
    schedules: tuple[
        ScheduledTask,
        ...
    ] = (),
) -> CopilotService:
    return CopilotService(
        infrastructure_status_provider=(
            lambda: (
                infrastructure
                or healthy_infrastructure()
            )
        ),
        recent_jobs_provider=lambda: jobs,
        schedules_provider=lambda: schedules,
        now_provider=lambda: NOW,
        intelligence_snapshot_provider=(
            lambda: {
                "trading_readiness": (
                    "NOT_READY"
                ),
                "market_outlook": (
                    "CAUTIOUS"
                ),
                "confidence": 63.5,
                "signal_count": 12,
                "actionable_signal_count": 2,
                "evidence_quality": "LOW",
            }
        ),
        graduation_status_provider=(
            lambda: {
                "ready": False,
                "checks": [
                    {
                        "name": (
                            "Decision sample"
                        ),
                        "passed": False,
                        "reason": (
                            "More shadow decisions "
                            "are required."
                        ),
                    },
                    {
                        "name": (
                            "Loss containment"
                        ),
                        "passed": True,
                        "reason": None,
                    },
                ],
            }
        ),
    )


def test_answers_platform_health_question(
) -> None:
    response = create_service().answer(
        question="Is KAIRO healthy?"
    )

    assert (
        "5 of 5 required services"
        in response.summary
    )
    assert all(
        suggestion.kind == "success"
        for suggestion
        in response.suggestions
    )


def test_reports_degraded_service(
) -> None:
    response = create_service(
        infrastructure=(
            degraded_infrastructure()
        ),
    ).platform_health()

    assert "DEGRADED" in response.summary
    assert any(
        suggestion.title
        == "Job Worker"
        and suggestion.kind
        == "warning"
        for suggestion
        in response.suggestions
    )


def test_reports_recent_failed_job(
) -> None:
    response = create_service(
        jobs=(failed_job(),),
    ).answer(
        question=(
            "What failed recently?"
        )
    )

    assert response.summary == (
        "1 failed job(s) were found."
    )
    assert (
        response.suggestions[0].title
        == "INTELLIGENCE_CYCLE"
    )
    assert (
        response.suggestions[0].message
        == "Market-data provider failed."
    )


def test_reports_no_recent_failures(
) -> None:
    response = create_service(
        jobs=(running_job(),),
    ).recent_failures()

    assert (
        "No failed jobs"
        in response.summary
    )
    assert (
        response.suggestions[0].kind
        == "success"
    )


def test_reports_current_activity(
) -> None:
    response = create_service(
        jobs=(running_job(),),
    ).answer(
        question=(
            "What is running now?"
        )
    )

    assert response.summary == (
        "1 job(s) are currently active."
    )
    assert (
        "RUNNING"
        in response.suggestions[0].message
    )


def test_reports_idle_worker(
) -> None:
    response = create_service(
    ).current_activity()

    assert (
        "no running or queued jobs"
        in response.summary.lower()
    )


def test_reports_next_schedule(
) -> None:
    response = create_service(
        schedules=(next_schedule(),),
    ).answer(
        question=(
            "What happens next?"
        )
    )

    assert (
        "INTELLIGENCE_CYCLE"
        in response.summary
    )
    assert (
        "in 30 minutes"
        in response.suggestions[0].message
    )


def test_operational_overview_includes_health_and_schedule(
) -> None:
    response = create_service(
        schedules=(next_schedule(),),
    ).operational_overview()

    assert response.summary == (
        "KAIRO is operating normally."
    )

    titles = {
        suggestion.title
        for suggestion
        in response.suggestions
    }

    assert "Platform health" in titles
    assert "Next scheduled task" in titles


def test_blank_question_is_rejected(
) -> None:
    service = create_service()

    with pytest.raises(
        ValueError,
        match="question is required",
    ):
        service.answer(
            question="   "
        )


def test_naive_clock_is_rejected(
) -> None:
    service = CopilotService(
        infrastructure_status_provider=(
            healthy_infrastructure
        ),
        recent_jobs_provider=lambda: (),
        schedules_provider=lambda: (
            next_schedule(),
        ),
        now_provider=lambda: datetime(
            2026,
            7,
            23,
            16,
            0,
        ),
    )

    with pytest.raises(
        ValueError,
        match="timezone-aware",
    ):
        service.upcoming_work()
        
def test_dashboard_overview_reports_healthy_platform(
) -> None:
    overview = create_service(
        schedules=(next_schedule(),),
    ).dashboard_overview()

    assert (
        overview.overall_status
        == "HEALTHY"
    )

    assert (
        overview.platform
        .online_services
        == 5
    )

    assert (
        overview.platform
        .required_services
        == 5
    )

    assert (
        overview.activity.active_jobs
        == 0
    )

    assert overview.schedule is not None

    assert (
        overview.schedule.task_type
        == "INTELLIGENCE_CYCLE"
    )

    assert (
        overview.failures.recent_count
        == 0
    )

    assert (
        overview.attention_items
        == ()
    )


def test_dashboard_overview_reports_activity_and_failure(
) -> None:
    overview = create_service(
        jobs=(
            running_job(),
            failed_job(),
        ),
        schedules=(next_schedule(),),
    ).dashboard_overview()

    assert (
        overview.overall_status
        == "ATTENTION"
    )

    assert (
        overview.activity.running_jobs
        == 1
    )

    assert (
        overview.activity.queued_jobs
        == 0
    )

    assert (
        overview.failures.recent_count
        == 1
    )

    assert (
        overview.failures.latest
        is not None
    )

    assert (
        overview.failures.latest.job_id
        == "job-failed-001"
    )

    codes = {
        item.code
        for item
        in overview.attention_items
    }

    assert (
        "RECENT_JOB_FAILURES"
        in codes
    )


def test_dashboard_overview_reports_degraded_infrastructure(
) -> None:
    overview = create_service(
        infrastructure=(
            degraded_infrastructure()
        ),
        schedules=(next_schedule(),),
    ).dashboard_overview()

    assert (
        overview.overall_status
        == "ATTENTION"
    )

    assert (
        overview.platform
        .online_services
        == 4
    )

    codes = {
        item.code
        for item
        in overview.attention_items
    }

    assert (
        "INFRASTRUCTURE_DEGRADED"
        in codes
    )


def test_dashboard_overview_reports_missing_schedule(
) -> None:
    overview = create_service(
    ).dashboard_overview()

    assert overview.schedule is None

    codes = {
        item.code
        for item
        in overview.attention_items
    }

    assert (
        "NO_ENABLED_SCHEDULES"
        in codes
    )


def test_dashboard_overview_serialises_to_dictionary(
) -> None:
    payload = create_service(
        schedules=(next_schedule(),),
    ).dashboard_overview(
    ).to_dictionary()

    assert payload[
        "overall_status"
    ] == "HEALTHY"

    assert payload[
        "platform"
    ] == {
        "overall_status": "HEALTHY",
        "online_services": 5,
        "required_services": 5,
    }

    assert payload[
        "activity"
    ] == {
        "running_jobs": 0,
        "queued_jobs": 0,
        "active_jobs": 0,
    }

    assert payload[
        "schedule"
    ][
        "task_type"
    ] == "INTELLIGENCE_CYCLE"
    
def test_builds_trading_intelligence(
) -> None:
    state = (
        create_service()
        .trading_intelligence()
    )

    assert (
        state.intelligence
        .trading_readiness
        == "NOT_READY"
    )

    assert (
        state.intelligence
        .confidence
        == 63.5
    )

    assert (
        state.intelligence
        .actionable_signal_count
        == 2
    )

    assert not state.graduation.ready

    assert (
        state.graduation
        .passed_checks
        == 1
    )

    assert (
        len(
            state.graduation
            .failed_checks
        )
        == 1
    )


def test_answers_intelligence_question(
) -> None:
    response = (
        create_service().answer(
            question=(
                "How strong is current "
                "intelligence?"
            )
        )
    )

    assert (
        "Confidence is 63.5"
        in response.summary
    )

    assert any(
        suggestion.title
        == "Evidence quality"
        for suggestion
        in response.suggestions
    )


def test_answers_graduation_question(
) -> None:
    response = (
        create_service().answer(
            question=(
                "What is blocking "
                "graduation?"
            )
        )
    )

    assert (
        "not ready to graduate"
        in response.summary
    )

    assert (
        response.suggestions[0]
        .title
        == "Decision sample"
    )


def test_explains_why_no_trade(
) -> None:
    response = (
        create_service().answer(
            question=(
                "Why didn't we trade "
                "today?"
            )
        )
    )

    assert (
        "requirements remain blocked"
        in response.summary
    )

    messages = {
        suggestion.message
        for suggestion
        in response.suggestions
    }

    assert (
        "Trading readiness has not "
        "reached READY."
        in messages
    )

    assert (
        "More shadow decisions are "
        "required."
        in messages
    )


def test_trading_intelligence_serialises(
) -> None:
    payload = (
        create_service()
        .trading_intelligence()
        .to_dictionary()
    )

    assert payload[
        "intelligence"
    ][
        "trading_readiness"
    ] == "NOT_READY"

    assert payload[
        "graduation"
    ][
        "failed_checks"
    ] == 1

    assert (
        payload["blockers"]
    )