import re
from dataclasses import dataclass

from app.news_analysis import NewsAnalysis


@dataclass(frozen=True)
class NewsAnalysisValidationResult:
    approved: bool
    reasons: tuple[str, ...]


class NewsAnalysisValidator:
    def validate(
        self,
        *,
        article_text: str,
        analysis: NewsAnalysis,
        allowed_symbols: set[str] | None = None,
    ) -> NewsAnalysisValidationResult:
        reasons: list[str] = []

        article_numbers = set(
            re.findall(
                r"\d+(?:\.\d+)?",
                article_text,
            )
        )

        highlight_numbers = set(
            re.findall(
                r"\d+(?:\.\d+)?",
                " ".join(
                    analysis.highlights
                ),
            )
        )

        unsupported_numbers = (
            highlight_numbers
            - article_numbers
        )

        if unsupported_numbers:
            reasons.append(
                "Analysis introduced unsupported "
                "numeric claims: "
                + ", ".join(
                    sorted(
                        unsupported_numbers
                    )
                )
            )

        if allowed_symbols is not None:
            unknown_items = {
                item
                for item in analysis.scope_items
                if item not in allowed_symbols
            }

            if unknown_items:
                reasons.append(
                    "Analysis returned unknown "
                    "scope items: "
                    + ", ".join(
                        sorted(
                            unknown_items
                        )
                    )
                )

        return NewsAnalysisValidationResult(
            approved=not reasons,
            reasons=tuple(reasons),
        )