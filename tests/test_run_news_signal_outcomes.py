import pytest

from app.run_news_signal_outcomes import (
    parse_args,
    resolve_provider_name,
)


def test_parses_news_outcome_paths() -> None:
    args = parse_args(
        [
            "--signals",
            "signals.jsonl",
            "--snapshots",
            "snapshots.jsonl",
            "--outcomes",
            "outcomes.jsonl",
        ]
    )

    assert args.signals == "signals.jsonl"
    assert args.snapshots == "snapshots.jsonl"
    assert args.outcomes == "outcomes.jsonl"
    assert args.provider is None


def test_parses_provider_override() -> None:
    args = parse_args(
        [
            "--provider",
            "twelve_data",
        ]
    )

    assert args.provider == "TWELVE_DATA"


def test_resolves_provider_override() -> None:
    assert resolve_provider_name(
        configured_provider_name="SIMULATED",
        provider_override="TWELVE_DATA",
    ) == "TWELVE_DATA"


def test_uses_configured_provider_without_override() -> None:
    assert resolve_provider_name(
        configured_provider_name="SIMULATED",
        provider_override=None,
    ) == "SIMULATED"


def test_rejects_unknown_provider() -> None:
    with pytest.raises(
        SystemExit,
    ):
        parse_args(
            [
                "--provider",
                "UNKNOWN",
            ]
        )