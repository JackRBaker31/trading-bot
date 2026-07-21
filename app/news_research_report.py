from app.news_research_summary import (
    NewsResearchGroup,
    NewsResearchSummary,
)


def format_news_research_summary(
    *,
    summary: NewsResearchSummary,
) -> str:
    lines = [
        "AI NEWS RESEARCH REPORT",
        "",
        "OVERVIEW",
        (
            f"Signals: {summary.signal_count}"
        ),
        (
            f"Outcomes: {summary.outcome_count}"
        ),
        (
            "Unmatched outcomes: "
            f"{summary.unmatched_outcome_count}"
        ),
        "",
    ]

    _append_section(
        lines=lines,
        title="SENTIMENT",
        groups=summary.sentiment_groups,
    )
    _append_section(
        lines=lines,
        title="MATERIALITY",
        groups=summary.materiality_groups,
    )
    _append_section(
        lines=lines,
        title="CONFIDENCE",
        groups=summary.confidence_groups,
    )
    _append_section(
        lines=lines,
        title="EVENT TYPES",
        groups=summary.event_type_groups,
    )

    return "\n".join(lines).rstrip()


def _append_section(
    *,
    lines: list[str],
    title: str,
    groups: tuple[NewsResearchGroup, ...],
) -> None:
    lines.append(title)

    if not groups:
        lines.append("No completed outcomes.")
        lines.append("")
        return

    for group in groups:
        lines.extend(
            [
                (
                    f"{group.group_name} "
                    f"[{group.horizon_name}]"
                ),
                (
                    f"  Samples: "
                    f"{group.sample_size}"
                ),
                (
                    "  Directional success: "
                    f"{group.directional_success_percent:.2f}%"
                ),
                (
                    "  Positive returns: "
                    f"{group.positive_return_percent:.2f}%"
                ),
                (
                    "  Average return: "
                    f"{group.average_return_percent:.2f}%"
                ),
                (
                    "  Median return: "
                    f"{group.median_return_percent:.2f}%"
                ),
                (
                    "  Range: "
                    f"{group.worst_return_percent:.2f}% "
                    "to "
                    f"{group.best_return_percent:.2f}%"
                ),
            ]
        )

    lines.append("")