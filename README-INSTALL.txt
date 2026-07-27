KAIRO MARKET DATA RESILIENCE v0.8
================================

PURPOSE
-------
This release prevents Twelve Data rate limits and temporary provider failures
from cascading into generic HTTP 500 responses and unavailable intelligence
panels.

It adds:

- persistent local historical-bar caching;
- fresh-cache reuse;
- stale-cache fallback during provider failures;
- identical-request deduplication;
- per-minute and per-day request budgets;
- a provider circuit breaker with cooldown;
- structured HTTP 503 responses when no cache is available;
- market-data metadata on technical, macro and advanced intelligence APIs;
- cached/degraded warning banners in the frontend;
- a Market Data Resilience panel in Operations Centre;
- focused resilience tests.

No database migration is required.
No order, risk, graduation, position-sizing or execution rule is changed.

INSTALLATION
------------
1. Stop KAIRO.

2. Extract this package OUTSIDE the trading-bot project.

3. Open PowerShell at:

   C:\Users\Jack\Documents\trading-bot

4. Run the installer using the real extracted path:

   .\.venv\Scripts\python.exe `
       "C:\Path\To\KAIRO-Market-Data-Resilience-v0.8\install_market_data_resilience_v08.py"

The installer backs up every replaced file under:

   source-backups\market-data-resilience-v0.8-<timestamp>\

The runtime cache is created under:

   data\runtime\market-data-cache\

DEFAULT BEHAVIOUR
-----------------
- Fresh cache lifetime: 15 minutes
- Stale fallback maximum age: 7 days
- Provider request budget: 6 requests per minute
- Provider request budget: 750 requests per rolling day
- Circuit opens after 2 consecutive provider failures
- Circuit cooldown: 60 seconds
- A Twelve Data 429 opens the circuit immediately

OPTIONAL .ENV SETTINGS
----------------------
The defaults are suitable for the current platform. These settings are optional:

   KAIRO_MARKET_DATA_CACHE_DIR=data/runtime/market-data-cache
   KAIRO_MARKET_DATA_CACHE_TTL_SECONDS=900
   KAIRO_MARKET_DATA_STALE_MAX_AGE_SECONDS=604800
   KAIRO_MARKET_DATA_MAX_REQUESTS_PER_MINUTE=6
   KAIRO_MARKET_DATA_MAX_REQUESTS_PER_DAY=750
   KAIRO_MARKET_DATA_CIRCUIT_FAILURE_THRESHOLD=2
   KAIRO_MARKET_DATA_CIRCUIT_COOLDOWN_SECONDS=60

Do not increase the request budgets beyond the allowance provided by your
Twelve Data plan.

BACKEND VALIDATION
------------------
From the project root:

   .\.venv\Scripts\python.exe -m pytest `
       tests\test_market_data_resilience.py `
       tests\test_twelve_data_historical_data.py `
       tests\test_infrastructure_status_service.py `
       tests\test_web_infrastructure.py `
       -q

Expected focused result:

   23 passed

Then run the complete backend suite:

   .\.venv\Scripts\python.exe -m pytest -q

The complete suite passed during this build:

   1166 passed

FRONTEND VALIDATION
-------------------
Run:

   cd .\frontend
   npm run typecheck
   npm run test
   npm run build
   cd ..

TypeScript validation passed during this build. Vitest and Vite must be run on
your Windows machine because the supplied node_modules contains Windows-native
Rollup packages and cannot execute in the Linux packaging environment.

RUNTIME CHECKS
--------------
After validation, restart KAIRO and open Operations Centre.

Confirm the Market Data Resilience card shows:

- provider status;
- cache hit rate;
- current minute budget usage;
- cached symbol count;
- stale fallback count;
- rate-limit event count;
- circuit-breaker state;
- last live success.

The authenticated health endpoint is:

   GET /api/market-data/health

When Twelve Data returns 429 and a usable cache exists, intelligence pages
continue using cached data and show an amber warning. When no usable cache
exists, KAIRO returns a structured HTTP 503 response instead of an unhandled
HTTP 500 traceback.
