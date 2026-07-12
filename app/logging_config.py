import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    log_file: str = "data/application.log",
    level: int = logging.INFO,
) -> None:
    path = Path(log_file)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove handlers previously created by this function.
    # This prevents duplicate log lines when tests or tools
    # initialise logging more than once.
    for handler in list(root_logger.handlers):
        if getattr(handler, "_trading_bot_handler", False):
            root_logger.removeHandler(handler)
            handler.close()

    formatter = logging.Formatter(
        fmt=(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    console_handler._trading_bot_handler = True  # type: ignore[attr-defined]

    file_handler = RotatingFileHandler(
        filename=path,
        maxBytes=1_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    file_handler._trading_bot_handler = True  # type: ignore[attr-defined]

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logging.captureWarnings(True)