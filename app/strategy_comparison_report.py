from app.strategy_comparison import (
    StrategyComparisonRow,
)


def format_strategy_comparison(
    rows: list[StrategyComparisonRow],
) -> str:
    if not rows:
        raise ValueError(
            "At least one comparison row is required."
        )

    header = (
        "Strategy | Trades | Return % | "
        "Profit Factor | Win Rate % | "
        "Max Drawdown % | Calmar"
    )

    separator = "-" * len(header)

    body = [
        (
            f"{row.name} | "
            f"{row.executed_trades} | "
            f"{row.total_return_percent:.2f} | "
            f"{row.profit_factor:.2f} | "
            f"{row.win_rate_percent:.2f} | "
            f"{row.maximum_drawdown_percent:.2f} | "
            f"{row.calmar_ratio:.2f}"
        )
        for row in rows
    ]

    winner = rows[0]

    return "\n".join(
        [
            header,
            separator,
            *body,
            "",
            f"Winner: {winner.name}",
        ]
    )