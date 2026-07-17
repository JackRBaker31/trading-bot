from dataclasses import dataclass


@dataclass(frozen=True)
class NewsSourceConfig:
    url_template: str
    timeout_seconds: float
    user_agent: str

    def __post_init__(
        self,
    ) -> None:
        if "{symbol}" not in self.url_template:
            raise ValueError(
                "URL template must contain "
                "{symbol}."
            )

        if self.timeout_seconds <= 0:
            raise ValueError(
                "Timeout must be greater than zero."
            )

    def build_url(
        self,
        symbol: str,
    ) -> str:
        normalised_symbol = (
            symbol.upper().strip()
        )

        return self.url_template.format(
            symbol=normalised_symbol
        )