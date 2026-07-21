import os

import app.environment as environment


def test_loads_dotenv_file(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / ".env"
    path.write_text(
        "EXAMPLE_SETTING=loaded-value\n",
        encoding="utf-8",
    )

    monkeypatch.delenv(
        "EXAMPLE_SETTING",
        raising=False,
    )
    monkeypatch.setattr(
        environment,
        "_environment_loaded",
        False,
    )

    loaded = environment.load_environment(
        file_path=path
    )

    assert loaded is True
    assert (
        os.getenv("EXAMPLE_SETTING")
        == "loaded-value"
    )


def test_preserves_existing_environment_value(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / ".env"
    path.write_text(
        "EXAMPLE_SETTING=file-value\n",
        encoding="utf-8",
    )

    monkeypatch.setenv(
        "EXAMPLE_SETTING",
        "process-value",
    )
    monkeypatch.setattr(
        environment,
        "_environment_loaded",
        False,
    )

    environment.load_environment(
        file_path=path
    )

    assert (
        os.getenv("EXAMPLE_SETTING")
        == "process-value"
    )


def test_is_idempotent_without_override(
    tmp_path,
    monkeypatch,
) -> None:
    path = tmp_path / ".env"
    path.write_text(
        "EXAMPLE_SETTING=first-value\n",
        encoding="utf-8",
    )

    monkeypatch.delenv(
        "EXAMPLE_SETTING",
        raising=False,
    )
    monkeypatch.setattr(
        environment,
        "_environment_loaded",
        False,
    )

    assert (
        environment.load_environment(
            file_path=path
        )
        is True
    )

    path.write_text(
        "EXAMPLE_SETTING=second-value\n",
        encoding="utf-8",
    )

    assert (
        environment.load_environment(
            file_path=path
        )
        is False
    )
    assert (
        os.getenv("EXAMPLE_SETTING")
        == "first-value"
    )