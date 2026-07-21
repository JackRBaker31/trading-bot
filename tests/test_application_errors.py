import pytest

from app.application_errors import (
    ApplicationError,
    ConfigurationError,
    DataStoreError,
    ProviderUnavailableError,
    ResearchRunError,
    TradingOperationError,
)


def test_application_error_exposes_stable_metadata() -> None:
    error = ApplicationError(
        "Something failed.",
        code="example_failure",
        retryable=True,
        context={
            "stage": "example",
        },
    )

    assert str(error) == "Something failed."
    assert error.code == "EXAMPLE_FAILURE"
    assert error.retryable is True
    assert error.context == {
        "stage": "example",
    }
    assert error.to_dictionary() == {
        "code": "EXAMPLE_FAILURE",
        "message": "Something failed.",
        "retryable": True,
        "context": {
            "stage": "example",
        },
    }


def test_configuration_error_is_value_error() -> None:
    error = ConfigurationError(
        "Invalid configuration."
    )

    assert isinstance(
        error,
        ApplicationError,
    )
    assert isinstance(
        error,
        ValueError,
    )
    assert (
        error.code
        == "CONFIGURATION_ERROR"
    )
    assert error.retryable is False


def test_provider_error_is_retryable_by_default() -> None:
    error = ProviderUnavailableError(
        "Provider unavailable."
    )

    assert (
        error.code
        == "PROVIDER_UNAVAILABLE"
    )
    assert error.retryable is True


@pytest.mark.parametrize(
    (
        "error_type",
        "expected_code",
    ),
    [
        (
            ResearchRunError,
            "RESEARCH_RUN_FAILED",
        ),
        (
            TradingOperationError,
            "TRADING_OPERATION_FAILED",
        ),
        (
            DataStoreError,
            "DATA_STORE_ERROR",
        ),
    ],
)
def test_application_errors_share_base(
    error_type,
    expected_code: str,
) -> None:
    error = error_type(
        "Example."
    )

    assert isinstance(
        error,
        ApplicationError,
    )
    assert error.code == expected_code


@pytest.mark.parametrize(
    "message",
    [
        "",
        "   ",
    ],
)
def test_rejects_blank_error_message(
    message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match="message is required",
    ):
        ApplicationError(
            message
        )