import pytest

from app.broker import BrokerOrderResult
from app.order_verification import (
    OrderVerificationService,
    OrderVerificationStatus,
)


def create_broker_order(
    status: str,
    filled_quantity: float = 0.0,
    filled_value: float = 0.0,
) -> BrokerOrderResult:
    return BrokerOrderResult(
        order_id=123456,
        ticker="AAPL_US_EQ",
        quantity=2.0,
        side="BUY",
        status=status,
        order_type="MARKET",
        filled_quantity=filled_quantity,
        filled_value=filled_value,
        currency="GBP",
    )


@pytest.mark.parametrize(
    "broker_status",
    [
        "NEW",
        "PENDING",
        "PENDING_NEW",
        "ACCEPTED",
    ],
)
def test_pending_statuses_are_classified(
    broker_status: str,
) -> None:
    service = OrderVerificationService()

    result = service.verify(
        create_broker_order(
            status=broker_status
        )
    )

    assert (
        result.status
        == OrderVerificationStatus.PENDING
    )
    assert result.is_terminal is False
    assert (
        result.portfolio_update_allowed
        is False
    )


@pytest.mark.parametrize(
    "broker_status",
    [
        "PARTIALLY_FILLED",
        "PARTIAL",
    ],
)
def test_partial_statuses_are_classified(
    broker_status: str,
) -> None:
    service = OrderVerificationService()

    result = service.verify(
        create_broker_order(
            status=broker_status,
            filled_quantity=1.0,
            filled_value=150.0,
        )
    )

    assert (
        result.status
        == OrderVerificationStatus
        .PARTIALLY_FILLED
    )
    assert result.is_terminal is False
    assert (
        result.portfolio_update_allowed
        is False
    )


@pytest.mark.parametrize(
    "broker_status",
    [
        "FILLED",
        "COMPLETED",
    ],
)
def test_filled_statuses_are_classified(
    broker_status: str,
) -> None:
    service = OrderVerificationService()

    result = service.verify(
        create_broker_order(
            status=broker_status,
            filled_quantity=2.0,
            filled_value=300.0,
        )
    )

    assert (
        result.status
        == OrderVerificationStatus.FILLED
    )
    assert result.is_terminal is True
    assert (
        result.portfolio_update_allowed
        is True
    )


@pytest.mark.parametrize(
    "broker_status",
    [
        "CANCELLED",
        "CANCELED",
        "REJECTED",
        "EXPIRED",
    ],
)
def test_failed_statuses_are_classified(
    broker_status: str,
) -> None:
    service = OrderVerificationService()

    result = service.verify(
        create_broker_order(
            status=broker_status
        )
    )

    assert (
        result.status
        == OrderVerificationStatus.FAILED
    )
    assert result.is_terminal is True
    assert (
        result.portfolio_update_allowed
        is False
    )


def test_unknown_status_is_classified_as_unknown() -> None:
    service = OrderVerificationService()

    result = service.verify(
        create_broker_order(
            status="SOMETHING_NEW"
        )
    )

    assert (
        result.status
        == OrderVerificationStatus.UNKNOWN
    )
    assert "SOMETHING_NEW" in result.reason
    assert result.is_terminal is False


def test_status_is_cleaned() -> None:
    service = OrderVerificationService()

    result = service.verify(
        create_broker_order(
            status=" filled ",
            filled_quantity=2.0,
            filled_value=300.0,
        )
    )

    assert (
        result.status
        == OrderVerificationStatus.FILLED
    )


def test_filled_status_without_quantity_is_unknown() -> None:
    service = OrderVerificationService()

    result = service.verify(
        create_broker_order(
            status="FILLED",
            filled_quantity=0.0,
            filled_value=0.0,
        )
    )

    assert (
        result.status
        == OrderVerificationStatus.UNKNOWN
    )
    assert (
        result.portfolio_update_allowed
        is False
    )