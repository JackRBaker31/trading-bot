from app.news_research_report import (
    format_news_research_summary,
)
from app.news_research_summary import (
    NewsResearchSummary,
)


def test_formats_empty_research_report() -> None:
    text = format_news_research_summary(
        summary=NewsResearchSummary(
            signal_count=1,
            outcome_count=0,
            unmatched_outcome_count=0,
            sentiment_groups=(),
            materiality_groups=(),
            event_type_groups=(),
            confidence_groups=(),
        )
    )

    assert "AI NEWS RESEARCH REPORT" in text
    assert "Signals: 1" in text
    assert "No completed outcomes." in text