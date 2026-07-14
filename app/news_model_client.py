from typing import Protocol


class NewsModelTransport(Protocol):
    def generate(
        self,
        *,
        prompt: str,
    ) -> str:
        """Return raw model output."""


class NewsModelClient:
    def __init__(
        self,
        transport: NewsModelTransport,
    ) -> None:
        self.transport = transport

    def analyse(
        self,
        article_text: str,
    ) -> str:
        cleaned_article = article_text.strip()

        if not cleaned_article:
            raise ValueError(
                "News article text is required."
            )

        prompt = (
            "You are a strict financial-news extraction system.\n"
            "Use ONLY facts explicitly stated in the article.\n"
            "Do not use prior knowledge.\n"
            "Do not infer missing values.\n"
            "Do not invent numbers, dates, percentages, forecasts, "
            "earnings results, guidance ranges, or company history.\n"
            "Every highlight must be directly supported by the article.\n"
            "If a fact is not explicitly present, omit it.\n"
            "For stock-specific news, return exchange ticker symbols "
            "such as AAPL, MSFT, or NVDA—not company names.\n"
            "If the ticker cannot be determined solely from the article, "
            "return an empty scope_items list.\n"
            "Never output placeholder words such as TICKER, SYMBOL, "
            "COMPANY, UNKNOWN, or N/A.\n"
            "If no explicit ticker symbol appears in the article, "
            "return an empty scope_items list.\n"
            "Return JSON only.\n\n"
            "Required schema:\n"
            "{\n"
            '  "impact_term": "SHORTTERM" or "LONGTERM",\n'
            '  "impact_scope": "GLOBAL", "INDUSTRY", or "STOCK",\n'
            '  "scope_items": [],\n'
            '  "highlights": ["fact explicitly stated in article"],\n'
            '  "sentiment": "POSITIVE", "NEGATIVE", or "NEUTRAL"\n'
            "}\n\n"
            "Article:\n"
            f"{cleaned_article}"
        )

        return self.transport.generate(
            prompt=prompt,
        )