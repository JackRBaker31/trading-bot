from __future__ import annotations

from collections import deque

import pytest

from app.restart_policy import RestartPolicy, RestartPolicyConfig


def test_approves_restart_with_exponential_backoff():
    policy = RestartPolicy()
    restart_times: deque[float] = deque()

    first = policy.decide(
        restart_times=restart_times,
        now=100.0,
        reason="process exited",
    )
    policy.record_restart(restart_times=restart_times, now=100.0)
    second = policy.decide(
        restart_times=restart_times,
        now=101.0,
        reason="heartbeat stale",
    )

    assert first.allowed is True
    assert first.delay_seconds == 1.0
    assert second.delay_seconds == 2.0
    assert second.restart_number == 2


def test_denies_restart_after_limit():
    policy = RestartPolicy(RestartPolicyConfig(max_restarts=2))
    restart_times = deque([90.0, 95.0])

    decision = policy.decide(
        restart_times=restart_times,
        now=100.0,
        reason="API unreachable",
    )

    assert decision.allowed is False
    assert decision.state == "FAILED"
    assert "manual review" in decision.detail


def test_old_restarts_are_pruned():
    policy = RestartPolicy(
        RestartPolicyConfig(max_restarts=2, restart_window_seconds=10.0)
    )
    restart_times = deque([50.0, 95.0])

    decision = policy.decide(
        restart_times=restart_times,
        now=100.0,
        reason="worker stale",
    )

    assert list(restart_times) == [95.0]
    assert decision.allowed is True
    assert decision.restart_number == 2


def test_recovery_grace_uses_process_start_time():
    policy = RestartPolicy(
        RestartPolicyConfig(recovery_grace_seconds=15.0)
    )

    assert policy.within_recovery_grace(
        started_monotonic=100.0,
        now=110.0,
    ) is True
    assert policy.within_recovery_grace(
        started_monotonic=100.0,
        now=116.0,
    ) is False


def test_rejects_invalid_configuration():
    with pytest.raises(ValueError):
        RestartPolicyConfig(max_restarts=-1)