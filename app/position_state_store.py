import json
from pathlib import Path

from app.position_state import (
    PositionState,
)


class PositionStateStore:
    def __init__(
        self,
        *,
        file_path: Path,
    ) -> None:
        self._file_path = file_path

    def load(
        self,
    ) -> dict[str, PositionState]:
        if not self._file_path.exists():
            return {}

        raw_text = self._file_path.read_text(
            encoding="utf-8"
        ).strip()

        if not raw_text:
            return {}

        raw_data = json.loads(
            raw_text
        )

        if not isinstance(
            raw_data,
            dict,
        ):
            raise ValueError(
                "Position-state file must contain "
                "a JSON object."
            )

        states: dict[
            str,
            PositionState,
        ] = {}

        for symbol, item in raw_data.items():
            if not isinstance(
                item,
                dict,
            ):
                raise ValueError(
                    "Position-state entries must "
                    "be JSON objects."
                )

            state = PositionState(
                symbol=symbol,
                quantity=int(
                    item["quantity"]
                ),
                average_entry_price=float(
                    item[
                        "average_entry_price"
                    ]
                ),
                highest_price=float(
                    item["highest_price"]
                ),
            )

            states[
                state.symbol
            ] = state

        return states

    def save(
        self,
        states: dict[
            str,
            PositionState,
        ],
    ) -> None:
        self._file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        raw_data = {
            symbol.upper().strip(): {
                "quantity": (
                    state.quantity
                ),
                "average_entry_price": (
                    state.average_entry_price
                ),
                "highest_price": (
                    state.highest_price
                ),
            }
            for symbol, state
            in states.items()
        }

        self._file_path.write_text(
            json.dumps(
                raw_data,
                indent=2,
                sort_keys=True,
            ),
            encoding="utf-8",
        )