from collections.abc import Callable
from dataclasses import dataclass

from app.strategy import Strategy


StrategyFactory = Callable[[], Strategy]


@dataclass(frozen=True)
class StrategyDefinition:
    name: str
    factory: StrategyFactory

    def __post_init__(
        self,
    ) -> None:
        cleaned_name = self.name.strip()

        if not cleaned_name:
            raise ValueError(
                "Strategy name is required."
            )

        object.__setattr__(
            self,
            "name",
            cleaned_name,
        )