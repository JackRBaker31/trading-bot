from app.environment import load_environment
from app.logging_config import setup_logging
from app.run_history_repository import RunHistoryRepository
from app.run_history_service import RunHistoryService
from app.trading_application import TradingApplicationRequest
from app.trading_application_service import (
    TradingApplicationService,
)


def main() -> None:
    setup_logging()
    load_environment()

    history_service = RunHistoryService(
        repository=RunHistoryRepository(
            database_path="data/application.db"
        )
    )
    history_service.initialize()

    TradingApplicationService(
        run_history_service=history_service
    ).run(
        request=TradingApplicationRequest()
    )


if __name__ == "__main__":
    main()
