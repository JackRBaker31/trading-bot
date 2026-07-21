from pathlib import Path


def load_watchlist(
    *,
    file_path: str,
) -> list[str]:
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"Watchlist file does not exist: {path}"
        )

    symbols: list[str] = []
    seen: set[str] = set()

    for line in path.read_text(
        encoding="utf-8",
    ).splitlines():
        cleaned = line.strip()

        if (
            not cleaned
            or cleaned.startswith("#")
        ):
            continue

        symbol = cleaned.upper()

        if symbol in seen:
            continue

        seen.add(symbol)
        symbols.append(symbol)

    if not symbols:
        raise ValueError(
            "Watchlist must contain at least "
            "one symbol."
        )

    return symbols