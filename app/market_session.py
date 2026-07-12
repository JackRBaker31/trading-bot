from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class MarketSessionStatus:
    is_open: bool
    reason: str
    local_time: datetime


class MarketSession:
    def __init__(
        self,
        timezone_name: str,
        opening_time: str,
        closing_time: str,
        trading_weekdays: set[int] | None = None,
    ) -> None:
        try:
            self.timezone = ZoneInfo(
                timezone_name
            )
        except Exception as error:
            raise ValueError(
                f"Invalid timezone: {timezone_name}"
            ) from error

        self.opening_time = self._parse_time(
            opening_time
        )

        self.closing_time = self._parse_time(
            closing_time
        )

        if self.opening_time >= self.closing_time:
            raise ValueError(
                "Opening time must be earlier than closing time."
            )

        if trading_weekdays is None:
            trading_weekdays = {
                0,
                1,
                2,
                3,
                4,
            }

        if not trading_weekdays:
            raise ValueError(
                "At least one trading weekday is required."
            )

        if any(
            weekday < 0 or weekday > 6
            for weekday in trading_weekdays
        ):
            raise ValueError(
                "Trading weekdays must be between 0 and 6."
            )

        self.trading_weekdays = set(
            trading_weekdays
        )

    def get_status(
        self,
        current_time: datetime | None = None,
    ) -> MarketSessionStatus:
        if current_time is None:
            local_time = datetime.now(
                self.timezone
            )
        elif current_time.tzinfo is None:
            local_time = current_time.replace(
                tzinfo=self.timezone
            )
        else:
            local_time = current_time.astimezone(
                self.timezone
            )

        if (
            local_time.weekday()
            not in self.trading_weekdays
        ):
            return MarketSessionStatus(
                is_open=False,
                reason="Market is closed today.",
                local_time=local_time,
            )

        current_clock_time = local_time.time().replace(
            tzinfo=None
        )

        if current_clock_time < self.opening_time:
            return MarketSessionStatus(
                is_open=False,
                reason="Market has not opened yet.",
                local_time=local_time,
            )

        if current_clock_time >= self.closing_time:
            return MarketSessionStatus(
                is_open=False,
                reason="Market has closed.",
                local_time=local_time,
            )

        return MarketSessionStatus(
            is_open=True,
            reason="Market session is open.",
            local_time=local_time,
        )

    @staticmethod
    def _parse_time(value: str) -> time:
        try:
            return time.fromisoformat(
                value
            )
        except ValueError as error:
            raise ValueError(
                f"Invalid time '{value}'. "
                "Use HH:MM or HH:MM:SS."
            ) from error