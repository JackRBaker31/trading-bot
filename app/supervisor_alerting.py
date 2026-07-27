from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


class AlertTransport(Protocol):
    def post(
        self,
        *,
        url: str,
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> None:
        ...


class UrllibAlertTransport:
    def post(
        self,
        *,
        url: str,
        payload: dict[str, object],
        timeout_seconds: float,
    ) -> None:
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(
            request,
            timeout=timeout_seconds,
        ) as response:
            response.read()


@dataclass(frozen=True)
class SupervisorAlertingHook:
    webhook_url: str | None = None
    transport: AlertTransport = UrllibAlertTransport()
    timeout_seconds: float = 5.0

    @classmethod
    def from_environment(
        cls,
        *,
        transport: AlertTransport | None = None,
    ) -> "SupervisorAlertingHook":
        return cls(
            webhook_url=(
                os.environ.get("ALERT_WEBHOOK_URL", "").strip()
                or None
            ),
            transport=(transport or UrllibAlertTransport()),
        )

    def send(
        self,
        *,
        event_type: str,
        process_name: str,
        message: str,
        severity: str = "ERROR",
        details: dict[str, object] | None = None,
    ) -> bool:
        if self.webhook_url is None:
            return False

        payload: dict[str, object] = {
            "source": "KAIRO_PROCESS_SUPERVISOR",
            "event_type": event_type,
            "severity": severity,
            "process_name": process_name,
            "message": message,
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "details": dict(details or {}),
        }

        try:
            self.transport.post(
                url=self.webhook_url,
                payload=payload,
                timeout_seconds=self.timeout_seconds,
            )
        except Exception:
            return False

        return True
