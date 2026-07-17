from dataclasses import dataclass

from app.news_policy_environment import (
    load_news_policy_mode,
    load_news_policy_observation_path,
)
from app.news_policy_observation_log import (
    NewsPolicyObservationLog,
)
from app.news_policy_runtime_config import (
    NewsPolicyRuntimeConfig,
)


@dataclass(frozen=True)
class NewsPolicyRuntime:
    config: NewsPolicyRuntimeConfig
    observation_log: (
        NewsPolicyObservationLog | None
    )


def create_news_policy_runtime(
) -> NewsPolicyRuntime:
    config = NewsPolicyRuntimeConfig(
        mode=load_news_policy_mode(),
        observation_path=(
            load_news_policy_observation_path()
        ),
    )

    observation_log = None

    if config.observation_enabled:
        observation_log = (
            NewsPolicyObservationLog(
                file_path=(
                    config.observation_path
                ),
            )
        )

    return NewsPolicyRuntime(
        config=config,
        observation_log=observation_log,
    )