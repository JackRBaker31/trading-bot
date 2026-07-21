from pathlib import Path

from dotenv import load_dotenv


_environment_loaded = False


def load_environment(
    *,
    file_path: str | Path = ".env",
    override: bool = False,
) -> bool:
    """
    Load environment variables from a dotenv file once.

    Existing operating-system environment variables take precedence
    unless override=True is explicitly requested.
    """
    global _environment_loaded

    if _environment_loaded and not override:
        return False

    loaded = load_dotenv(
        dotenv_path=Path(file_path),
        override=override,
    )

    _environment_loaded = True
    return loaded