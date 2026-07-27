from app.supervisor_alerting import SupervisorAlertingHook


class FailingTransport:
    def post(self, **kwargs) -> None:
        del kwargs
        raise RuntimeError("webhook unavailable")


def test_no_webhook_is_a_no_op() -> None:
    hook = SupervisorAlertingHook(webhook_url=None)

    assert hook.send(
        event_type="process_crash",
        process_name="api",
        message="failed",
    ) is False


def test_transport_failure_does_not_escape() -> None:
    hook = SupervisorAlertingHook(
        webhook_url="https://example.test",
        transport=FailingTransport(),
    )

    assert hook.send(
        event_type="process_crash",
        process_name="api",
        message="failed",
    ) is False
