from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


_SYMBOL_PATTERN = re.compile(r"^[A-Z][A-Z0-9.-]{0,14}$")


@dataclass(frozen=True)
class WatchlistSymbol:
    symbol: str
    group: str
    line_number: int

    def to_dictionary(self) -> dict[str, object]:
        return {
            "symbol": self.symbol,
            "group": self.group,
            "line_number": self.line_number,
        }


@dataclass(frozen=True)
class WatchlistParseResult:
    file_path: str
    symbols: tuple[WatchlistSymbol, ...]
    duplicate_symbols: tuple[str, ...]
    invalid_symbols: tuple[str, ...]

    @property
    def symbol_values(self) -> tuple[str, ...]:
        return tuple(item.symbol for item in self.symbols)

    @property
    def groups(self) -> dict[str, tuple[str, ...]]:
        grouped: dict[str, list[str]] = {}
        for item in self.symbols:
            grouped.setdefault(item.group, []).append(item.symbol)
        return {
            group: tuple(values)
            for group, values in grouped.items()
        }

    def to_dictionary(self) -> dict[str, object]:
        return {
            "file_path": self.file_path,
            "symbol_count": len(self.symbols),
            "symbols": [item.to_dictionary() for item in self.symbols],
            "groups": {
                key: list(value)
                for key, value in self.groups.items()
            },
            "duplicate_symbols": list(self.duplicate_symbols),
            "invalid_symbols": list(self.invalid_symbols),
        }


def parse_watchlist(*, file_path: str) -> WatchlistParseResult:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Watchlist file does not exist: {path}"
        )

    entries: list[WatchlistSymbol] = []
    seen: set[str] = set()
    duplicates: list[str] = []
    invalid: list[str] = []
    current_group = "Uncategorised"

    for line_number, line in enumerate(
        path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        cleaned = line.strip()

        if not cleaned:
            continue

        if cleaned.startswith("#"):
            heading = cleaned.lstrip("#").strip()
            if heading:
                current_group = heading
            continue

        symbol = cleaned.upper()

        if not _SYMBOL_PATTERN.fullmatch(symbol):
            invalid.append(symbol)
            continue

        if symbol in seen:
            duplicates.append(symbol)
            continue

        seen.add(symbol)
        entries.append(
            WatchlistSymbol(
                symbol=symbol,
                group=current_group,
                line_number=line_number,
            )
        )

    if not entries and not invalid:
        raise ValueError(
            "Watchlist must contain at least one symbol."
        )

    return WatchlistParseResult(
        file_path=str(path),
        symbols=tuple(entries),
        duplicate_symbols=tuple(dict.fromkeys(duplicates)),
        invalid_symbols=tuple(dict.fromkeys(invalid)),
    )


def load_watchlist(*, file_path: str) -> list[str]:
    result = parse_watchlist(file_path=file_path)

    if result.invalid_symbols:
        invalid = ", ".join(result.invalid_symbols)
        raise ValueError(
            "Watchlist contains invalid symbol(s): "
            f"{invalid}."
        )

    if not result.symbols:
        raise ValueError(
            "Watchlist must contain at least one symbol."
        )

    return list(result.symbol_values)
