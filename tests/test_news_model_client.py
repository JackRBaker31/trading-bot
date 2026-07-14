import pytest

from app.news_model_client import (
    NewsModelClient,
)


class FakeTransport:
    def __init__(
        self,
        output: str,
    ) -> None:
        self.output = output
        self.prompts: list[str] = []

    def generate(
        self,
        *,
        prompt: str,
    ) -> str:
        self.prompts.append(prompt)
        return self.output


def test_builds_prompt_and_returns_raw_output() -> None:
    transport = FakeTransport(
        output='{"sentiment":"POSITIVE"}'
    )

    client = NewsModelClient(
        transport=transport
    )

    result = client.analyse(
        "Apple reported stronger revenue."
    )

    assert result == (
        '{"sentiment":"POSITIVE"}'
    )

    assert len(transport.prompts) == 1

    prompt = transport.prompts[0]

    assert "JSON only" in prompt
    assert "impact_term" in prompt
    assert "impact_scope" in prompt
    assert "scope_items" in prompt
    assert "highlights" in prompt
    assert "sentiment" in prompt
    assert (
        "Apple reported stronger revenue."
        in prompt
    )
    assert '"scope_items": []' in prompt
    assert '"scope_items": ["TICKER"]' not in prompt
    assert "Never output placeholder words" in prompt

def test_rejects_empty_article() -> None:
    client = NewsModelClient(
        transport=FakeTransport(
            output="{}"
        )
    )

    with pytest.raises(
        ValueError,
        match="article text",
    ):
        client.analyse("   ")