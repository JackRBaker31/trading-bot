from datetime import (
    datetime,
    timezone,
)

import pytest

from app.news_signal_price_snapshot import (
    NewsSignalPriceSnapshot,
)
from app.news_signal_price_snapshot_store import (
    NewsSignalPriceSnapshotStore,
)


def create_snapshot() -> NewsSignalPriceSnapshot:
    return NewsSignalPriceSnapshot(
        article_id="article-1",
        symbol="AAPL",
        captured_at=datetime.now(
            timezone.utc
        ),
        price=100.0,
        provider="FAKE",
    )


def test_appends_and_loads_snapshot(
    tmp_path,
) -> None:
    store = NewsSignalPriceSnapshotStore(
        file_path=str(
            tmp_path / "snapshots.jsonl"
        )
    )
    snapshot = create_snapshot()

    store.append(snapshot=snapshot)

    assert store.load_all() == [
        snapshot
    ]
    assert (
        store.get_by_article_id(
            "article-1"
        )
        == snapshot
    )


def test_rejects_duplicate_snapshot(
    tmp_path,
) -> None:
    store = NewsSignalPriceSnapshotStore(
        file_path=str(
            tmp_path / "snapshots.jsonl"
        )
    )
    snapshot = create_snapshot()

    store.append(snapshot=snapshot)

    with pytest.raises(
        ValueError,
        match="already exists",
    ):
        store.append(snapshot=snapshot)