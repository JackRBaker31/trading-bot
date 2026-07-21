from datetime import (
    datetime,
    timedelta,
    timezone,
)

import pytest

from app.news_signal import NewsSignal
from app.news_signal_store import (
    NewsSignalStore,
)


def create_signal() -> NewsSignal:
    published_at = datetime(
        2026,
        7,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )

    return NewsSignal(
        article_id="article-1",
        symbol="AAPL",
        headline="Apple raises guidance",
        sentiment=0.7,
        relevance=0.9,
        confidence=0.8,
        event_type="GUIDANCE_RAISED",
        is_material=True,
        published_at=published_at,
        expires_at=(
            published_at
            + timedelta(hours=24)
        ),
        source="Example News",
        reasoning_summary=(
            "Guidance increased."
        ),
    )


def test_appends_and_loads_signal(
    tmp_path,
) -> None:
    store = NewsSignalStore(
        file_path=str(
            tmp_path
            / "news_signals.jsonl"
        )
    )

    signal = create_signal()

    store.append(
        signal=signal
    )

    assert store.load_all() == [
        signal
    ]


def test_returns_empty_when_store_missing(
    tmp_path,
) -> None:
    store = NewsSignalStore(
        file_path=str(
            tmp_path
            / "missing.jsonl"
        )
    )

    assert store.load_all() == []


def test_rejects_invalid_record(
    tmp_path,
) -> None:
    path = (
        tmp_path
        / "news_signals.jsonl"
    )
    path.write_text(
        "not-json\n",
        encoding="utf-8",
    )

    store = NewsSignalStore(
        file_path=str(path)
    )

    with pytest.raises(
        ValueError,
        match="line 1",
    ):
        store.load_all()