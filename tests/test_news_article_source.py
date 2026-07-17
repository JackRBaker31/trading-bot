from app.news_article_source import (
    InMemoryNewsArticleSource,
)


def test_returns_latest_article_for_symbol() -> None:
    source = InMemoryNewsArticleSource(
        articles={
            "AAPL": (
                "Apple reported stronger revenue."
            ),
        }
    )

    assert source.get_latest_article(
        "AAPL"
    ) == (
        "Apple reported stronger revenue."
    )


def test_normalises_symbol_before_lookup() -> None:
    source = InMemoryNewsArticleSource(
        articles={
            "AAPL": (
                "Apple reported stronger revenue."
            ),
        }
    )

    assert source.get_latest_article(
        " aapl "
    ) == (
        "Apple reported stronger revenue."
    )


def test_returns_none_when_no_article_exists() -> None:
    source = InMemoryNewsArticleSource(
        articles={}
    )

    assert (
        source.get_latest_article("MSFT")
        is None
    )