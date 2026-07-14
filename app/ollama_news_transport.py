import logging

import httpx

NEWS_ANALYSIS_SCHEMA: dict[str, object] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "impact_term",
        "impact_scope",
        "scope_items",
        "highlights",
        "sentiment",
    ],
    "properties": {
        "impact_term": {
            "type": "string",
            "enum": [
                "SHORTTERM",
                "LONGTERM",
            ],
        },
        "impact_scope": {
            "type": "string",
            "enum": [
                "GLOBAL",
                "INDUSTRY",
                "STOCK",
            ],
        },
        "scope_items": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "highlights": {
            "type": "array",
            "items": {
                "type": "string",
            },
        },
        "sentiment": {
            "type": "string",
            "enum": [
                "POSITIVE",
                "NEGATIVE",
                "NEUTRAL",
            ],
        },
    },
}

logger = logging.getLogger(__name__)


class OllamaNewsTransport:
    def __init__(
        self,
        model_name: str,
        base_url: str = "http://localhost:11434",
        timeout_seconds: float = 120.0,
    ) -> None:
        cleaned_model_name = model_name.strip()
        cleaned_base_url = base_url.rstrip("/")

        if not cleaned_model_name:
            raise ValueError(
                "Ollama model name is required."
            )

        if not cleaned_base_url:
            raise ValueError(
                "Ollama base URL is required."
            )

        if timeout_seconds <= 0:
            raise ValueError(
                "Ollama timeout must be positive."
            )

        self.model_name = cleaned_model_name
        self.base_url = cleaned_base_url
        self.timeout_seconds = timeout_seconds

    def generate(
        self,
        *,
        prompt: str,
    ) -> str:
        cleaned_prompt = prompt.strip()

        if not cleaned_prompt:
            raise ValueError(
                "Ollama prompt is required."
            )

        logger.info(
            "news_model_request "
            "provider=OLLAMA model=%s",
            self.model_name,
        )

        try:
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": cleaned_prompt,
                    "stream": False,
                    "format": NEWS_ANALYSIS_SCHEMA,
                    "options": {
                        "temperature": 0,
                    },
                },
                timeout=self.timeout_seconds,
            )

            response.raise_for_status()

        except httpx.TimeoutException as error:
            raise RuntimeError(
                "Ollama news-model request timed out."
            ) from error

        except httpx.HTTPStatusError as error:
            raise RuntimeError(
                "Ollama returned HTTP "
                f"{error.response.status_code}."
            ) from error

        except httpx.HTTPError as error:
            raise RuntimeError(
                "Could not connect to Ollama."
            ) from error

        try:
            data = response.json()
        except ValueError as error:
            raise RuntimeError(
                "Ollama returned invalid JSON."
            ) from error

        if not isinstance(data, dict):
            raise RuntimeError(
                "Ollama returned an invalid response."
            )

        raw_output = data.get(
            "response"
        )

        if not isinstance(raw_output, str):
            raise RuntimeError(
                "Ollama response text was missing."
            )

        cleaned_output = raw_output.strip()

        if not cleaned_output:
            raise RuntimeError(
                "Ollama returned an empty response."
            )

        logger.info(
            "news_model_response_received "
            "provider=OLLAMA model=%s",
            self.model_name,
        )

        return cleaned_output