from app.news_analysis import (
    NewsAnalysis,
    parse_news_analysis,
)
from app.news_model_client import (
    NewsModelClient,
)


class NewsAnalysisService:
    def __init__(
        self,
        model_client: NewsModelClient,
    ) -> None:
        self.model_client = model_client

    def analyse(
        self,
        article_text: str,
    ) -> NewsAnalysis:
        raw_output = (
            self.model_client.analyse(
                article_text
            )
        )

        return parse_news_analysis(
            raw_output
        )