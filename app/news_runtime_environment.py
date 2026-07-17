import os


DEFAULT_NEWS_ANALYSIS_TTL_SECONDS = 1_800.0
DEFAULT_NEWS_MAXIMUM_AGE_SECONDS = 3_600.0


def _load_positive_float(
    *,
    environment_name: str,
    default_value: float,
) -> float:
    raw_value = os.getenv(
        environment_name,
        str(default_value),
    ).strip()

    try:
        value = float(
            raw_value
        )
    except ValueError as error:
        raise ValueError(
            f"{environment_name} must be a number."
        ) from error

    if value <= 0:
        raise ValueError(
            f"{environment_name} must be "
            "greater than zero."
        )

    return value


def load_news_analysis_ttl_seconds() -> float:
    return _load_positive_float(
        environment_name=(
            "NEWS_ANALYSIS_TTL_SECONDS"
        ),
        default_value=(
            DEFAULT_NEWS_ANALYSIS_TTL_SECONDS
        ),
    )


def load_news_maximum_age_seconds() -> float:
    return _load_positive_float(
        environment_name=(
            "NEWS_MAXIMUM_AGE_SECONDS"
        ),
        default_value=(
            DEFAULT_NEWS_MAXIMUM_AGE_SECONDS
        ),
    )