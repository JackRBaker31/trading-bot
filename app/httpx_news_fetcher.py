import httpx


class HttpxNewsFetcher:
    def __init__(
        self,
        *,
        timeout_seconds: float = 15.0,
        user_agent: str = "trading-bot/1.0",
    ) -> None:
        self._timeout_seconds = (
            timeout_seconds
        )
        self._user_agent = user_agent

    def fetch(
        self,
        url: str,
    ) -> str:
        response = httpx.get(
            url,
            timeout=self._timeout_seconds,
            headers={
                "User-Agent": self._user_agent,
            },
        )

        response.raise_for_status()

        return response.text