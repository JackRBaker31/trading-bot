import json
import sqlite3

from app.job_reliability_service import JobReliabilityService


def test_reliability_status_counts_jobs_crashes_and_restarts(tmp_path):
    database = tmp_path / "application.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE jobs (status TEXT NOT NULL)")
        connection.executemany(
            "INSERT INTO jobs (status) VALUES (?)",
            [("SUCCEEDED",), ("RUNNING",)],
        )
        connection.commit()

    crashes = tmp_path / "crashes"
    crashes.mkdir()
    (crashes / "one.json").write_text(
        json.dumps(
            {
                "timestamp": "2026-07-27T08:00:00+00:00",
                "job_id": "job-1",
                "job_type": "INTELLIGENCE_CYCLE",
                "stage": "NEWS_RESEARCH",
                "exception_type": "SystemExit",
            }
        ),
        encoding="utf-8",
    )

    events = tmp_path / "events.jsonl"
    events.write_text(
        json.dumps(
            {
                "event": "SERVICE_RESTARTED",
                "pid": 123,
            }
        )
        + "\n",
        encoding="utf-8",
    )

    status = JobReliabilityService(
        database_path=str(database),
        crash_directory=str(crashes),
        launcher_events_path=str(events),
    ).get_status()

    assert status["abandoned_running_jobs"] == 1
    assert status["crash_report_count"] == 1
    assert status["worker_restart_count"] == 1
