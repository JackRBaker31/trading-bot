import os
from pathlib import Path


DEFAULT_NEWS_POLICY_MODE = "off"
DEFAULT_NEWS_POLICY_OBSERVATION_PATH = Path(
    "data/news-policy-observations.jsonl"
)

SUPPORTED_NEWS_POLICY_MODES = {
    "off",
    "shadow",
    "enforce",
}


def load_news_policy_mode() -> str:
    mode = os.getenv(
        "NEWS_POLICY_MODE",
        DEFAULT_NEWS_POLICY_MODE,
    ).strip().lower()

    if mode not in SUPPORTED_NEWS_POLICY_MODES:
        raise ValueError(
            "Unsupported news policy mode: "
            f"{mode}"
        )

    return mode


def load_news_policy_observation_path() -> Path:
    raw_path = os.getenv(
        "NEWS_POLICY_OBSERVATION_PATH",
        str(
            DEFAULT_NEWS_POLICY_OBSERVATION_PATH
        ),
    ).strip()

    if not raw_path:
        raise ValueError(
            "NEWS_POLICY_OBSERVATION_PATH "
            "must not be empty."
        )

    return Path(
        raw_path
    )