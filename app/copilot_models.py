from dataclasses import dataclass
from typing import Literal


CopilotSuggestionKind = Literal[
    "warning",
    "info",
    "success",
    "action",
]


@dataclass(frozen=True)
class CopilotSuggestion:
    title: str
    message: str
    kind: CopilotSuggestionKind = "info"


@dataclass(frozen=True)
class CopilotResponse:
    summary: str
    suggestions: tuple[CopilotSuggestion, ...]