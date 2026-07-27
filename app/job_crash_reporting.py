from __future__ import annotations

import json
import os
import platform
import threading
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


class JobCrashReporter:
    def __init__(
        self,
        *,
        crash_directory: str = "data/runtime/crashes",
    ) -> None:
        self._crash_directory = Path(crash_directory)

    def report(
        self,
        *,
        error: BaseException,
        job_id: str | None,
        job_type: str | None,
        stage: str | None,
        context: dict[str, Any] | None = None,
    ) -> Path:
        self._crash_directory.mkdir(parents=True, exist_ok=True)
        now = datetime.now(timezone.utc)
        report_id = uuid4().hex
        path = self._crash_directory / (
            f"{now.strftime('%Y%m%dT%H%M%S.%fZ')}-{report_id}.json"
        )
        payload = {
            "report_id": report_id,
            "timestamp": now.isoformat(),
            "process_id": os.getpid(),
            "thread": threading.current_thread().name,
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "job_id": job_id,
            "job_type": job_type,
            "stage": stage,
            "exception_type": type(error).__name__,
            "exception_message": str(error),
            "traceback": "".join(
                traceback.format_exception(
                    type(error), error, error.__traceback__
                )
            ),
            "context": dict(context or {}),
        }
        path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return path
