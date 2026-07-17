import json
import sqlite3
from pathlib import Path

from app.news_analysis import (
    NewsAnalysis,
    NewsImpactScope,
    NewsImpactTerm,
    NewsSentiment,
)
from app.stored_news_analysis import (
    StoredNewsAnalysis,
)


class SQLiteNewsAnalysisRepository:
    def __init__(
        self,
        *,
        database_path: str | Path,
    ) -> None:
        self._database_path = Path(
            database_path
        )

        self._database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialise_database()

    def _connect(
        self,
    ) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self._database_path
        )

        connection.row_factory = (
            sqlite3.Row
        )

        return connection

    def _initialise_database(
        self,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS
                news_analyses (
                    id INTEGER PRIMARY KEY
                        AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    impact_term TEXT NOT NULL,
                    impact_scope TEXT NOT NULL,
                    scope_items_json TEXT NOT NULL,
                    highlights_json TEXT NOT NULL,
                    sentiment TEXT NOT NULL,
                    analysed_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    article_title TEXT NOT NULL,
                    article_url TEXT,
                    published_at TEXT NOT NULL,
                    relevance_score REAL NOT NULL,
                    source_sentiment_label TEXT,
                    source_sentiment_score REAL,
                    model_name TEXT NOT NULL,
                    prompt_version TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_news_analyses_symbol_id
                ON news_analyses (
                    symbol,
                    id DESC
                )
                """
            )

    def save(
        self,
        *,
        symbol: str,
        stored_analysis: StoredNewsAnalysis,
    ) -> None:
        normalised_symbol = (
            symbol.upper().strip()
        )

        analysis = (
            stored_analysis.analysis
        )

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO news_analyses (
                    symbol,
                    impact_term,
                    impact_scope,
                    scope_items_json,
                    highlights_json,
                    sentiment,
                    analysed_at,
                    expires_at,
                    article_title,
                    article_url,
                    published_at,
                    relevance_score,
                    source_sentiment_label,
                    source_sentiment_score,
                    model_name,
                    prompt_version
                )
                VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?,
                    ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    normalised_symbol,
                    analysis.impact_term.value,
                    analysis.impact_scope.value,
                    json.dumps(
                        analysis.scope_items
                    ),
                    json.dumps(
                        analysis.highlights
                    ),
                    analysis.sentiment.value,
                    stored_analysis
                    .analysed_at
                    .isoformat(),
                    stored_analysis
                    .expires_at
                    .isoformat(),
                    stored_analysis.article_title,
                    stored_analysis.article_url,
                    stored_analysis
                    .published_at
                    .isoformat(),
                    stored_analysis
                    .relevance_score,
                    stored_analysis
                    .source_sentiment_label,
                    stored_analysis
                    .source_sentiment_score,
                    stored_analysis.model_name,
                    stored_analysis.prompt_version,
                ),
            )

    def get_latest(
        self,
        symbol: str,
    ) -> StoredNewsAnalysis | None:
        normalised_symbol = (
            symbol.upper().strip()
        )

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    impact_term,
                    impact_scope,
                    scope_items_json,
                    highlights_json,
                    sentiment,
                    analysed_at,
                    expires_at,
                    article_title,
                    article_url,
                    published_at,
                    relevance_score,
                    source_sentiment_label,
                    source_sentiment_score,
                    model_name,
                    prompt_version
                FROM news_analyses
                WHERE symbol = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (
                    normalised_symbol,
                ),
            ).fetchone()

        if row is None:
            return None

        return StoredNewsAnalysis(
            analysis=NewsAnalysis(
                impact_term=(
                    NewsImpactTerm(
                        row["impact_term"]
                    )
                ),
                impact_scope=(
                    NewsImpactScope(
                        row["impact_scope"]
                    )
                ),
                scope_items=tuple(
                    json.loads(
                        row[
                            "scope_items_json"
                        ]
                    )
                ),
                highlights=tuple(
                    json.loads(
                        row[
                            "highlights_json"
                        ]
                    )
                ),
                sentiment=(
                    NewsSentiment(
                        row["sentiment"]
                    )
                ),
            ),
            analysed_at=(
                __import__(
                    "datetime"
                )
                .datetime
                .fromisoformat(
                    row["analysed_at"]
                )
            ),
            expires_at=(
                __import__(
                    "datetime"
                )
                .datetime
                .fromisoformat(
                    row["expires_at"]
                )
            ),
            article_title=(
                row["article_title"]
            ),
            article_url=(
                row["article_url"]
            ),
            published_at=(
                __import__(
                    "datetime"
                )
                .datetime
                .fromisoformat(
                    row["published_at"]
                )
            ),
            relevance_score=(
                row["relevance_score"]
            ),
            source_sentiment_label=(
                row[
                    "source_sentiment_label"
                ]
            ),
            source_sentiment_score=(
                row[
                    "source_sentiment_score"
                ]
            ),
            model_name=row["model_name"],
            prompt_version=(
                row["prompt_version"]
            ),
        )