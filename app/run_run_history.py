import argparse

from app.environment import load_environment
from app.run_history import RunType
from app.run_history_repository import (
    RunHistoryRepository,
)
from app.run_history_service import (
    RunHistoryService,
)


def parse_args(
    argv: list[str] | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Display recent application run history."
        )
    )
    parser.add_argument(
        "--database",
        default="data/application.db",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
    )
    parser.add_argument(
        "--type",
        choices=[
            run_type.value
            for run_type in RunType
        ],
        default=None,
    )
    return parser.parse_args(argv)


def main() -> None:
    load_environment()
    args = parse_args()

    service = RunHistoryService(
        repository=RunHistoryRepository(
            database_path=args.database
        )
    )
    service.initialize()

    run_type = (
        None
        if args.type is None
        else RunType(args.type)
    )

    records = service.list_recent(
        limit=args.limit,
        run_type=run_type,
    )

    print("RUN HISTORY")

    if not records:
        print("No runs recorded.")
        return

    for record in records:
        finished = (
            "-"
            if record.finished_at is None
            else record.finished_at.isoformat()
        )
        print(
            f"{record.run_id} | "
            f"{record.run_type.value} | "
            f"{record.status.value} | "
            f"{record.started_at.isoformat()} | "
            f"{finished}"
        )


if __name__ == "__main__":
    main()