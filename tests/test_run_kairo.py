from datetime import datetime, timezone

import run_kairo


def test_service_keys_are_unique() -> None:
    keys = [service.key for service in run_kairo.SERVICES]
    assert len(keys) == len(set(keys))


def test_api_health_endpoint() -> None:
    api = next(
        service
        for service in run_kairo.SERVICES
        if service.key == "api"
    )
    assert api.port == 8000
    assert api.health_url == "http://127.0.0.1:8000/health/ready"


def test_parse_iso_supports_z_suffix() -> None:
    assert run_kairo.parse_iso(
        "2026-07-24T20:00:00Z"
    ) == datetime(
        2026, 7, 24, 20, 0,
        tzinfo=timezone.utc,
    )


def test_duration_seconds() -> None:
    assert run_kairo.duration_seconds(
        "2026-07-24T20:00:00+00:00",
        "2026-07-24T20:00:12.500000+00:00",
    ) == 12.5


def test_stage_detail() -> None:
    job = {
        "result": {
            "stages": [
                {
                    "stage": "NEWS_RESEARCH",
                    "detail": {
                        "articles_fetched": 11,
                    },
                }
            ]
        }
    }
    assert run_kairo.stage_detail(
        job,
        "NEWS_RESEARCH",
    ) == {"articles_fetched": 11}


def test_count_warnings() -> None:
    job = {
        "result": {
            "stages": [
                {"warnings": ["one", "two"]},
                {"warnings": []},
            ]
        }
    }
    assert run_kairo.count_warnings(job) == 2


def test_state_round_trip(tmp_path, monkeypatch) -> None:
    state_path = tmp_path / "state.json"
    monkeypatch.setattr(
        run_kairo,
        "STATE_PATH",
        state_path,
    )
    expected = {
        "api": {
            "pid": 123,
            "foreground": True,
        }
    }
    run_kairo.save_state(expected)
    assert run_kairo.load_state() == expected



def test_trim_restart_history_removes_old_entries() -> None:
    assert run_kairo.trim_restart_history(
        [10.0, 50.0, 95.0],
        now=100.0,
        window_seconds=20.0,
    ) == [95.0]


def test_trim_restart_history_keeps_boundary() -> None:
    assert run_kairo.trim_restart_history(
        [80.0, 81.0, 100.0],
        now=100.0,
        window_seconds=20.0,
    ) == [80.0, 81.0, 100.0]


def test_append_monitor_event_writes_jsonl(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / "events.jsonl"

    monkeypatch.setattr(
        run_kairo,
        "MONITOR_EVENTS_PATH",
        path,
    )
    monkeypatch.setattr(
        run_kairo,
        "RUNTIME_DIR",
        tmp_path,
    )

    run_kairo.append_monitor_event(
        event="SERVICE_RESTARTED",
        service="worker",
        detail="Recovered.",
        pid=123,
    )

    payload = run_kairo.json.loads(
        path.read_text(
            encoding="utf-8"
        ).strip()
    )

    assert payload["event"] == "SERVICE_RESTARTED"
    assert payload["service"] == "worker"
    assert payload["pid"] == 123


def test_monitor_lock_rejects_live_existing_monitor(
    tmp_path,
    monkeypatch,
) -> None:
    lock_path = tmp_path / "monitor.json"
    lock_path.write_text(
        run_kairo.json.dumps(
            {"pid": 999}
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        run_kairo,
        "MONITOR_LOCK_PATH",
        lock_path,
    )
    monkeypatch.setattr(
        run_kairo,
        "RUNTIME_DIR",
        tmp_path,
    )
    monkeypatch.setattr(
        run_kairo,
        "pid_is_running",
        lambda pid: pid == 999,
    )

    assert (
        run_kairo.acquire_monitor_lock()
        is False
    )


def test_unified_supervisor_status_contains_all_services(
    tmp_path,
    monkeypatch,
) -> None:
    status_path = tmp_path / "supervisor_status.json"
    monkeypatch.setattr(
        run_kairo,
        "SUPERVISOR_STATUS_PATH",
        status_path,
    )
    monkeypatch.setattr(
        run_kairo,
        "load_state",
        lambda: {
            service.key: {
                "pid": 100 + index,
                "started_at": 1_700_000_000.0,
            }
            for index, service in enumerate(run_kairo.SERVICES)
        },
    )
    monkeypatch.setattr(
        run_kairo,
        "clean_state",
        lambda state: state,
    )
    monkeypatch.setattr(
        run_kairo,
        "service_is_running",
        lambda service, state: True,
    )
    monkeypatch.setattr(
        run_kairo,
        "_service_pid",
        lambda service, state: int(state[service.key]["pid"]),
    )

    monitored = {
        service.key: run_kairo.MonitoredServiceState()
        for service in run_kairo.SERVICES
    }
    health = {
        service.key: {
            "name": run_kairo._status_service_name(service),
            "healthy": True,
            "health_status": "HEALTHY",
            "persistent_fault": False,
            "consecutive_health_failures": 0,
            "last_health_check_at": "2026-07-28T08:00:00+00:00",
            "last_healthy_at": "2026-07-28T08:00:00+00:00",
            "health_detail": "Healthy.",
        }
        for service in run_kairo.SERVICES
    }

    run_kairo.write_unified_supervisor_status(
        monitored=monitored,
        health_payloads=health,
        supervisor_status="RUNNING",
        supervisor_process_id=999,
    )

    payload = run_kairo.json.loads(
        status_path.read_text(encoding="utf-8")
    )
    assert payload["supervisor_type"] == "KAIRO_UNIFIED_LAUNCHER"
    assert payload["supervisor_status"] == "RUNNING"
    assert payload["supervisor_process_id"] == 999
    assert [item["name"] for item in payload["processes"]] == [
        "api",
        "frontend",
        "job_worker",
        "scheduler",
    ]
    assert all(item["status"] == "RUNNING" for item in payload["processes"])


def test_supervisor_cli_status_reports_stale_dead_process(
    tmp_path,
    monkeypatch,
) -> None:
    status_path = tmp_path / "supervisor_status.json"
    status_path.write_text(
        run_kairo.json.dumps(
            {
                "generated_at": "2026-07-28T08:00:00+00:00",
                "supervisor_status": "RUNNING",
                "supervisor_process_id": 123,
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(run_kairo, "SUPERVISOR_STATUS_PATH", status_path)
    monkeypatch.setattr(run_kairo, "pid_is_running", lambda pid: False)

    assert run_kairo.supervisor_cli_status() == "STALE"


def test_stopped_supervisor_status_disables_restarts(
    tmp_path,
    monkeypatch,
) -> None:
    status_path = tmp_path / "supervisor_status.json"
    monkeypatch.setattr(run_kairo, "SUPERVISOR_STATUS_PATH", status_path)
    monkeypatch.setattr(run_kairo, "load_state", lambda: {})
    monkeypatch.setattr(run_kairo, "clean_state", lambda state: state)
    monkeypatch.setattr(
        run_kairo,
        "service_is_running",
        lambda service, state: False,
    )
    monkeypatch.setattr(run_kairo, "_service_pid", lambda service, state: None)

    run_kairo.write_stopped_supervisor_status()

    payload = run_kairo.json.loads(status_path.read_text(encoding="utf-8"))
    assert payload["supervisor_status"] == "STOPPED"
    assert payload["supervisor_process_id"] == 0
    assert payload["restart_enabled"] is False
