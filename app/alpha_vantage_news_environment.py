import os


def load_alpha_vantage_api_key() -> str:
    api_key = os.getenv(
        "ALPHA_VANTAGE_API_KEY",
        "",
    ).strip()

    if not api_key:
        raise ValueError(
            "ALPHA_VANTAGE_API_KEY "
            "is required."
        )

    return api_key