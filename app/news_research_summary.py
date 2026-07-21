from collections import defaultdict
from dataclasses import dataclass
from statistics import median

from app.news_signal import NewsSignal
from app.news_signal_outcome import NewsSignalOutcome


@dataclass(frozen=True)
class NewsResearchGroup:
    group_name: str
    horizon_name: str
    sample_size: int
    directional_success_count: int
    directional_success_percent: float
    positive_return_count: int
    positive_return_percent: float
    average_return_percent: float
    median_return_percent: float
    worst_return_percent: float
    best_return_percent: float


@dataclass(frozen=True)
class NewsResearchSummary:
    signal_count: int
    outcome_count: int
    unmatched_outcome_count: int
    sentiment_groups: tuple[NewsResearchGroup, ...]
    materiality_groups: tuple[NewsResearchGroup, ...]
    event_type_groups: tuple[NewsResearchGroup, ...]
    confidence_groups: tuple[NewsResearchGroup, ...]


def summarize_news_research(
    *,
    signals: list[NewsSignal],
    outcomes: list[NewsSignalOutcome],
) -> NewsResearchSummary:
    signals_by_article_id = {
        signal.article_id: signal
        for signal in signals
    }

    matched: list[
        tuple[NewsSignal, NewsSignalOutcome]
    ] = []
    unmatched_outcome_count = 0

    for outcome in outcomes:
        signal = signals_by_article_id.get(
            outcome.article_id
        )

        if signal is None:
            unmatched_outcome_count += 1
            continue

        matched.append(
            (
                signal,
                outcome,
            )
        )

    return NewsResearchSummary(
        signal_count=len(signals),
        outcome_count=len(outcomes),
        unmatched_outcome_count=(
            unmatched_outcome_count
        ),
        sentiment_groups=_build_groups(
            matched=matched,
            group_name_provider=(
                lambda signal: _sentiment_name(
                    signal.sentiment
                )
            ),
        ),
        materiality_groups=_build_groups(
            matched=matched,
            group_name_provider=(
                lambda signal: (
                    "MATERIAL"
                    if signal.is_material
                    else "NON_MATERIAL"
                )
            ),
        ),
        event_type_groups=_build_groups(
            matched=matched,
            group_name_provider=(
                lambda signal: signal.event_type
            ),
        ),
        confidence_groups=_build_groups(
            matched=matched,
            group_name_provider=(
                lambda signal: _confidence_band(
                    signal.confidence
                )
            ),
        ),
    )


def _build_groups(
    *,
    matched: list[
        tuple[NewsSignal, NewsSignalOutcome]
    ],
    group_name_provider,
) -> tuple[NewsResearchGroup, ...]:
    grouped: dict[
        tuple[str, str],
        list[
            tuple[NewsSignal, NewsSignalOutcome]
        ],
    ] = defaultdict(list)

    for signal, outcome in matched:
        group_name = group_name_provider(
            signal
        )
        horizon_name = (
            outcome.horizon_name
            .upper()
            .strip()
        )

        grouped[
            (
                group_name,
                horizon_name,
            )
        ].append(
            (
                signal,
                outcome,
            )
        )

    results = [
        _summarize_group(
            group_name=group_name,
            horizon_name=horizon_name,
            rows=rows,
        )
        for (
            group_name,
            horizon_name,
        ), rows in grouped.items()
    ]

    return tuple(
        sorted(
            results,
            key=lambda result: (
                result.horizon_name,
                result.group_name,
            ),
        )
    )


def _summarize_group(
    *,
    group_name: str,
    horizon_name: str,
    rows: list[
        tuple[NewsSignal, NewsSignalOutcome]
    ],
) -> NewsResearchGroup:
    returns = [
        outcome.return_percent
        for _, outcome in rows
    ]

    directional_success_count = sum(
        1
        for signal, outcome in rows
        if _is_directional_success(
            signal=signal,
            return_percent=(
                outcome.return_percent
            ),
        )
    )

    positive_return_count = sum(
        1
        for value in returns
        if value > 0
    )

    sample_size = len(rows)

    return NewsResearchGroup(
        group_name=group_name,
        horizon_name=horizon_name,
        sample_size=sample_size,
        directional_success_count=(
            directional_success_count
        ),
        directional_success_percent=(
            directional_success_count
            / sample_size
            * 100.0
        ),
        positive_return_count=(
            positive_return_count
        ),
        positive_return_percent=(
            positive_return_count
            / sample_size
            * 100.0
        ),
        average_return_percent=(
            sum(returns)
            / sample_size
        ),
        median_return_percent=median(
            returns
        ),
        worst_return_percent=min(
            returns
        ),
        best_return_percent=max(
            returns
        ),
    )


def _sentiment_name(
    sentiment: float,
) -> str:
    if sentiment > 0:
        return "POSITIVE"

    if sentiment < 0:
        return "NEGATIVE"

    return "NEUTRAL"


def _confidence_band(
    confidence: float,
) -> str:
    if confidence >= 0.90:
        return "HIGH_0.90_TO_1.00"

    if confidence >= 0.70:
        return "MEDIUM_0.70_TO_0.89"

    return "LOW_BELOW_0.70"


def _is_directional_success(
    *,
    signal: NewsSignal,
    return_percent: float,
) -> bool:
    if signal.sentiment > 0:
        return return_percent > 0

    if signal.sentiment < 0:
        return return_percent < 0

    return abs(return_percent) < 0.25