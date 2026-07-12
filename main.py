from datetime import datetime

from app.portfolio import Portfolio


def main() -> None:
    print("Trading system starting...")
    print(f"Current time: {datetime.now()}")
    print("Mode: SAFE DEVELOPMENT MODE")
    print("Real-money trading: DISABLED")

    simulated_prices = {
        "AAPL": 150.00,
        "MSFT": 320.00,
    }

    portfolio = Portfolio(starting_cash=10_000.00)

    print("\nBuying 10 simulated shares of AAPL...")
    portfolio.buy(
        symbol="AAPL",
        quantity=10,
        price=simulated_prices["AAPL"],
    )

    simulated_prices["AAPL"] = 155.00
    portfolio.display(simulated_prices)

    print("\nSelling 4 simulated shares of AAPL...")
    portfolio.sell(
        symbol="AAPL",
        quantity=4,
        price=simulated_prices["AAPL"],
    )

    portfolio.display(simulated_prices)


if __name__ == "__main__":
    main()