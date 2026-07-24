from pathlib import Path

import run_kairo


def test_service_definitions_are_unique(
) -> None:
    keys = [
        service.key
        for service in run_kairo.SERVICES
    ]

    assert len(keys) == len(set(keys))


def test_api_has_health_check(
) -> None:
    api = next(
        service
        for service in run_kairo.SERVICES
        if service.key == "api"
    )

    assert api.port == 8000
    assert (
        api.health_url
        == "http://127.0.0.1:8000/health/ready"
    )


def test_frontend_uses_project_frontend_directory(
) -> None:
    frontend = next(
        service
        for service in run_kairo.SERVICES
        if service.key == "frontend"
    )

    assert (
        frontend.cwd.name
        == "frontend"
    )


def test_load_state_returns_empty_for_invalid_json(
    tmp_path,
    monkeypatch,
) -> None:
    state_path = (
        tmp_path
        / "state.json"
    )
    state_path.write_text(
        "{invalid",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        run_kairo,
        "STATE_PATH",
        state_path,
    )

    assert run_kairo.load_state() == {}


def test_save_and_load_state_round_trip(
    tmp_path,
    monkeypatch,
) -> None:
    state_path = (
        tmp_path
        / "state.json"
    )

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

    assert (
        run_kairo.load_state()
        == expected
    )
