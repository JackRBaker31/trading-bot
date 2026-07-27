from app.job_recovery_service import JobRecoveryService
from app.job_repository import JobRepository


def main() -> None:
    repository = JobRepository(
        database_path="data/application.db"
    )
    repository.initialize()
    summary = JobRecoveryService(
        repository=repository,
        stale_after_seconds=1.0,
    ).reconcile()
    print(
        "Reconciled abandoned jobs:",
        summary.reconciled_count,
    )
    print("Cutoff:", summary.cutoff.isoformat())
    print("Completed:", summary.recovered_at.isoformat())


if __name__ == "__main__":
    main()
