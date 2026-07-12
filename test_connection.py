import os

import httpx
from dotenv import load_dotenv


load_dotenv()

api_key = os.getenv("TRADING212_DEMO_API_KEY")
api_secret = os.getenv("TRADING212_DEMO_API_SECRET")

if not api_key:
    raise RuntimeError("No API key found in .env")

if not api_secret:
    raise RuntimeError("No API secret found in .env")

print("Connecting to Trading 212...")

response = httpx.get(
    "https://demo.trading212.com/api/v0/equity/account/summary",
    auth=(api_key, api_secret),
    timeout=10,
)

print("Status code:", response.status_code)
print()
print(response.text)