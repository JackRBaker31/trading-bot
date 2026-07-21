from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.news_signal_outcome import (
    NewsSignalOutcome,
)
from app.news_signal_outcome_store import (
    NewsSignalOutcomeStore,
)


def test_appends_and_loads_outcome(
    tmp_path,
) -> None:
    published_at = datetime(
        2026,
        7,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )

    outcome = NewsSignalOutcome(
        article_id="article-1",
        symbol="AAPL",
        horizon_name="1H",
        signal_published_at=published_at,
        observed_at=(
            published_at
            + timedelta(hours=1)
        ),
        reference_price=100.0,
        observed_price=105.0,
        return_percent=5.0,
    )

    store = NewsSignalOutcomeStore(
        file_path=str(
            tmp_path / "outcomes.jsonl"
        )
    )

    store.append(
        outcome=outcome
    )

    assert store.load_all() == [
        outcome
    ]