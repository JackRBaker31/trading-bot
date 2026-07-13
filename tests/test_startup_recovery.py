from app.broker import BrokerOrderResult
from app.order_journal import OrderJournalEntry
from app.order_polling import OrderPollingResult
from app.order_verification import (
    OrderVerificationStatus,
)
from app.startup_recovery import (
    StartupRecoveryService,
    StartupRecoveryState,
)


class FakeOrderJournal:
    def __init__(
        self,
        entries: list[OrderJournalEntry],
    ) -> None:
        self.entries = entries
        self.load_calls = 0

    def load_unfinished_orders(
        self,
    ) -> list[OrderJournalEntry]:
        self.load_calls += 1
        return self.entries


class FakeRecoveryService:
    def __init__(
        self,
        results_by_order_id: dict[
            int,
            OrderPollingResult | Exception,
        ],
    ) -> None:
        self.results_by_order_id = (
            results_by_order_id
        )
        self.recover_calls: list[
            OrderJournalEntry
        ] = []

    def recover(
        self,
        journal_entry: OrderJournalEntry,
    ) -> OrderPollingResult:
        self.recover_calls.append(
            journal_entry
        )

        broker_order_id = (
            journal_entry.broker_order_id
        )

        if broker_order_id is None:
            raise ValueError(
                "Broker order ID is missing."
            )

        result = self.results_by_order_id[
            broker_order_id
        ]

        if isinstance(result, Exception):
            raise result

        return result


def create_journal_entry(
    order_id: int,
    symbol: str = "AAPL",
    event: str = "PENDING",
) -> OrderJournalEntry:
    return OrderJournalEntry(
        timestamp="2026-07-13T10:00:00+00:00",
        reservation_key=(
            f"{symbol}:BUY:2"
        ),
        event=event,
        symbol=symbol,
        side="BUY",
        quantity=2,
        broker_order_id=order_id,
        reason="Startup recovery test.",
    )


def create_polling_result(
    order_id: int,
    status: OrderVerificationStatus = (
        OrderVerificationStatus.PENDING
    ),
) -> OrderPollingResult:
    return OrderPollingResult(
        order=BrokerOrderResult(
            order_id=order_id,
            ticker="AAPL_US_EQ",
            quantity=2.0,
            side="BUY",
            status="NEW",
            order_type="MARKET",
            filled_quantity=0.0,
            filled_value=0.0,
            currency="GBP",
        ),
        status=status,
        reason="Recovered broker state.",
        attempts=1,
        timed_out=False,
    )


def test_recover_unfinished_orders_returns_report() -> None:
    first_entry = create_journal_entry(
        order_id=111,
        symbol="AAPL",
    )
    second_entry = create_journal_entry(
        order_id=222,
        symbol="MSFT",
    )

    journal = FakeOrderJournal(
        entries=[
            first_entry,
            second_entry,
        ]
    )

    first_result = create_polling_result(
        order_id=111
    )
    second_result = create_polling_result(
        order_id=222
    )

    recovery_service = FakeRecoveryService(
        results_by_order_id={
            111: first_result,
            222: second_result,
        }
    )

    service = StartupRecoveryService(
        order_journal=journal,
        recovery_service=recovery_service,
    )

    report = service.recover_unfinished_orders()

    assert journal.load_calls == 1
    assert report.total_orders == 2
    assert report.successful_orders == 2
    assert report.failed_orders == 0

    assert report.items[0].journal_entry == (
        first_entry
    )
    assert report.items[0].polling_result == (
        first_result
    )
    assert report.items[0].error is None

    assert report.items[1].journal_entry == (
        second_entry
    )
    assert report.items[1].polling_result == (
        second_result
    )
    assert report.items[1].error is None


def test_recovery_continues_after_one_failure() -> None:
    failed_entry = create_journal_entry(
        order_id=111,
        symbol="AAPL",
    )
    successful_entry = create_journal_entry(
        order_id=222,
        symbol="MSFT",
    )

    successful_result = create_polling_result(
        order_id=222
    )

    journal = FakeOrderJournal(
        entries=[
            failed_entry,
            successful_entry,
        ]
    )

    recovery_service = FakeRecoveryService(
        results_by_order_id={
            111: RuntimeError(
                "Broker is unavailable."
            ),
            222: successful_result,
        }
    )

    service = StartupRecoveryService(
        order_journal=journal,
        recovery_service=recovery_service,
    )

    report = service.recover_unfinished_orders()

    assert report.total_orders == 2
    assert report.successful_orders == 1
    assert report.failed_orders == 1

    assert report.items[0].succeeded is False
    assert report.items[0].polling_result is None
    assert report.items[0].error == (
        "Broker is unavailable."
    )

    assert report.items[1].succeeded is True
    assert report.items[1].polling_result == (
        successful_result
    )

    assert recovery_service.recover_calls == [
        failed_entry,
        successful_entry,
    ]


def test_empty_journal_returns_empty_report() -> None:
    journal = FakeOrderJournal(
        entries=[]
    )

    recovery_service = FakeRecoveryService(
        results_by_order_id={}
    )

    service = StartupRecoveryService(
        order_journal=journal,
        recovery_service=recovery_service,
    )

    report = service.recover_unfinished_orders()

    assert report.items == ()
    assert report.total_orders == 0
    assert report.successful_orders == 0
    assert report.failed_orders == 0
    assert recovery_service.recover_calls == []

def test_pending_result_is_classified() -> None:
    entry = create_journal_entry(
        order_id=111
    )

    polling_result = create_polling_result(
        order_id=111,
        status=OrderVerificationStatus.PENDING,
    )

    journal = FakeOrderJournal(
        entries=[entry]
    )

    recovery_service = FakeRecoveryService(
        results_by_order_id={
            111: polling_result,
        }
    )

    service = StartupRecoveryService(
        order_journal=journal,
        recovery_service=recovery_service,
    )

    report = service.recover_unfinished_orders()

    assert report.items[0].state == (
        StartupRecoveryState.PENDING
    )

def test_filled_result_is_classified() -> None:
    entry = create_journal_entry(
        order_id=111
    )

    polling_result = create_polling_result(
        order_id=111,
        status=OrderVerificationStatus.FILLED,
    )

    journal = FakeOrderJournal(
        entries=[entry]
    )

    recovery_service = FakeRecoveryService(
        results_by_order_id={
            111: polling_result,
        }
    )

    service = StartupRecoveryService(
        order_journal=journal,
        recovery_service=recovery_service,
    )

    report = service.recover_unfinished_orders()

    assert report.items[0].state == (
        StartupRecoveryState.FILLED
    )

def test_recovery_exception_is_classified() -> None:
    entry = create_journal_entry(
        order_id=111
    )

    journal = FakeOrderJournal(
        entries=[entry]
    )

    recovery_service = FakeRecoveryService(
        results_by_order_id={
            111: RuntimeError(
                "Broker is unavailable."
            ),
        }
    )

    service = StartupRecoveryService(
        order_journal=journal,
        recovery_service=recovery_service,
    )

    report = service.recover_unfinished_orders()

    assert report.items[0].state == (
        StartupRecoveryState.RECOVERY_ERROR
    )

