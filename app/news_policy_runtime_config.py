from dataclasses import dataclass
from pathlib import Path


SUPPORTED_NEWS_POLICY_MODES = {
    "off",
    "shadow",
    "enforce",
}


@dataclass(frozen=True)
class NewsPolicyRuntimeConfig:
    mode: str
    observation_path: Path

    def __post_init__(
        self,
    ) -> None:
        normalised_mode = (
            self.mode.lower().strip()
        )

        if (
            normalised_mode
            not in SUPPORTED_NEWS_POLICY_MODES
        ):
            raise ValueError(
                "Unsupported news policy mode: "
                f"{self.mode}"
            )

        object.__setattr__(
            self,
            "mode",
            normalised_mode,
        )

    @property
    def enabled(
        self,
    ) -> bool:
        return self.mode != "off"

    @property
    def shadow_mode(
        self,
    ) -> bool:
        return self.mode == "shadow"

    @property
    def enforce_mode(
        self,
    ) -> bool:
        return self.mode == "enforce"

    @property
    def observation_enabled(
        self,
    ) -> bool:
        return self.enabled