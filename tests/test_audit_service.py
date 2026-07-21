from app.audit_service import AuditService
from app.auth_repository import (
    AuthenticationRepository,
)


def test_records_and_lists_audit_events(
    tmp_path,
) -> None:
    repository = AuthenticationRepository(
        database_path=str(
            tmp_path / "application.db"
        )
    )
    repository.initialize()
    service = AuditService(
        repository=repository
    )

    service.record(
        action="TEST_ACTION",
        outcome="SUCCEEDED",
        username="admin",
        target_id="target-1",
        metadata={"safe": True},
    )

    events = service.list_recent()

    assert len(events) == 1
    assert events[0]["action"] == (
        "TEST_ACTION"
    )
    assert events[0]["username"] == "admin"
