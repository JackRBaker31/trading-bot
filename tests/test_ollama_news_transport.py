import httpx
import pytest

from app.ollama_news_transport import (
    NEWS_ANALYSIS_SCHEMA,
    OllamaNewsTransport,
)

class FakeResponse:
    def __init__(
        self,
        data: object,
        status_code: int = 200,
    ) -> None:
        self.data = data
        self.status_code = status_code
        self.request = httpx.Request(
            "POST",
            "http://localhost:11434/api/generate",
        )

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            response = httpx.Response(
                status_code=self.status_code,
                request=self.request,
            )

            raise httpx.HTTPStatusError(
                "Ollama request failed.",
                request=self.request,
                response=response,
            )

    def json(self) -> object:
        return self.data


def test_generates_using_ollama_api(
    monkeypatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_post(
        url,
        json,
        timeout,
    ):
        captured["url"] = url
        captured["json"] = json
        captured["timeout"] = timeout

        return FakeResponse(
            {
                "response": (
                    '{"sentiment":"POSITIVE"}'
                )
            }
        )

    monkeypatch.setattr(
        httpx,
        "post",
        fake_post,
    )

    transport = OllamaNewsTransport(
        model_name="stocks-news",
        timeout_seconds=30.0,
    )

    result = transport.generate(
        prompt="Analyse this article."
    )

    assert result == (
        '{"sentiment":"POSITIVE"}'
    )

    assert captured["url"] == (
        "http://localhost:11434/api/generate"
    )

    assert captured["timeout"] == 30.0

    payload = captured["json"]

    assert isinstance(
        payload,
        dict,
    )

    assert payload["model"] == "stocks-news"
    assert payload["prompt"] == (
        "Analyse this article."
    )
    assert payload["stream"] is False
    assert payload["options"] == {
        "temperature": 0,
    }

    assert payload["format"] == (
        NEWS_ANALYSIS_SCHEMA
    )

    schema = payload["format"]

    assert isinstance(schema, dict)

    properties = schema["properties"]

    assert isinstance(properties, dict)

    assert properties["highlights"] == {
        "type": "array",
        "items": {
            "type": "string",
        },
    }


def test_rejects_empty_prompt() -> None:
    transport = OllamaNewsTransport(
        model_name="stocks-news"
    )

    with pytest.raises(
        ValueError,
        match="prompt",
    ):
        transport.generate(
            prompt="   "
        )


def test_rejects_missing_response_text(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        httpx,
        "post",
        lambda url, json, timeout: (
            FakeResponse({})
        ),
    )

    transport = OllamaNewsTransport(
        model_name="stocks-news"
    )

    with pytest.raises(
        RuntimeError,
        match="response text",
    ):
        transport.generate(
            prompt="Analyse this."
        )


def test_http_error_is_wrapped(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        httpx,
        "post",
        lambda url, json, timeout: (
            FakeResponse(
                {},
                status_code=404,
            )
        ),
    )

    transport = OllamaNewsTransport(
        model_name="missing-model"
    )

    with pytest.raises(
        RuntimeError,
        match="HTTP 404",
    ):
        transport.generate(
            prompt="Analyse this."
        )



    transport = OllamaNewsTransport(
        model_name="missing-model"
    )

    with pytest.raises(
        RuntimeError,
        match="HTTP 404",
    ):
        transport.generate(
            prompt="Analyse this."
        )