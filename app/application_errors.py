from collections.abc import Mapping
from typing import Any


class ApplicationError(Exception):
    """
    Base error for failures crossing an application boundary.

    message is safe for a CLI or authenticated application user.
    code is stable for web responses, jobs, logs, and tests.
    context contains non-secret diagnostic metadata.
    """

    default_code = "APPLICATION_ERROR"
    default_retryable = False

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        retryable: bool | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        cleaned_message = message.strip()

        if not cleaned_message:
            raise ValueError(
                "Application error message is required."
            )

        cleaned_code = (
            code
            or self.default_code
        ).upper().strip()

        if not cleaned_code:
            raise ValueError(
                "Application error code is required."
            )

        super().__init__(
            cleaned_message
        )

        self.message = cleaned_message
        self.code = cleaned_code
        self.retryable = (
            self.default_retryable
            if retryable is None
            else retryable
        )
        self.context = dict(
            context or {}
        )

    def to_dictionary(
        self,
    ) -> dict[str, object]:
        return {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "context": self.context,
        }


class ConfigurationError(
    ApplicationError,
    ValueError,
):
    default_code = "CONFIGURATION_ERROR"


class ProviderUnavailableError(
    ApplicationError,
):
    default_code = "PROVIDER_UNAVAILABLE"
    default_retryable = True


class ResearchRunError(
    ApplicationError,
):
    default_code = "RESEARCH_RUN_FAILED"


class TradingOperationError(
    ApplicationError,
):
    default_code = "TRADING_OPERATION_FAILED"


class DataStoreError(
    ApplicationError,
):
    default_code = "DATA_STORE_ERROR"



class AuthenticationError(
    ApplicationError,
):
    default_code = "AUTHENTICATION_ERROR"


class AuthorizationError(
    ApplicationError,
):
    default_code = "AUTHORIZATION_ERROR"
