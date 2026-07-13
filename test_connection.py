import os

from dotenv import load_dotenv

from app.trading212_client import (
    Trading212Client,
)


load_dotenv()

api_key = os.getenv(
    "TRADING212_API_KEY",
    "",
).strip()

api_secret = os.getenv(
    "TRADING212_API_SECRET",
    "",
).strip()

if not api_key:
    raise RuntimeError(
        "No Trading 212 API key found in .env"
    )

if not api_secret:
    raise RuntimeError(
        "No Trading 212 API secret found in .env"
    )

client = Trading212Client(
    api_key=api_key,
    api_secret=api_secret,
    environment="DEMO",
)

print("Connecting to Trading 212 Demo...")

account = client.get_account_summary()

positions = client.get_positions()

print("Connection successful.")
print(f"Currency: {account.currency}")
print(
    "Available to trade: "
    f"{account.available_to_trade:.2f}"
)
print(f"Open positions: {len(positions)}")

for position in positions:
    print(
        f"{position.ticker}: "
        f"{position.quantity} units"
    )