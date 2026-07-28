KAIRO RANKING VALIDATION & FORWARD RETURNS v0.11
================================================

PURPOSE
-------
Tests whether KAIRO's highest Opportunity Scores and strongest ranks actually
produce better forward returns than lower-ranked opportunities.

The feature remains advisory only. It does not alter Opportunity Scores, risk
limits, execution readiness, graduation controls, orders or paper trading.

WHAT IT MEASURES
----------------
For the first retained ranking snapshot for each symbol and UTC date, KAIRO
records forward outcomes at:

- 1 trading day
- 5 trading days
- 20 trading days

To avoid look-ahead bias, entry is the NEXT available trading-session open.
The exit is the close after the selected number of trading sessions. Each result
is compared with SPY over the same entry/exit dates.

KAIRO records:

- Absolute forward return
- SPY return and relative alpha
- Maximum favourable excursion
- Maximum drawdown
- Original rank and Opportunity Score
- Calibrated confidence and evidence coverage
- Execution-ready versus blocked state
- Symbol and sector
- Historical-match and measured-case maturity

WHY DAILY HORIZONS
------------------
The current resilient historical-data layer is built around daily bars. v0.11
therefore uses trading-day horizons rather than adding high-frequency provider
requests that could increase Twelve Data rate-limit pressure.

BEFORE INSTALLING
-----------------
1. Commit or back up the current v0.10 project.
2. In the KAIRO Platform Supervisor window, press Ctrl+C.
3. Run:

   C:\Users\Jack\Documents\trading-bot\Stop Everything.bat

4. Wait for API, Frontend, Worker and Scheduler to stop.

INSTALL
-------
Extract this ZIP, then open PowerShell and run:

cd C:\Users\Jack\Documents\trading-bot

.\.venv\Scripts\python.exe `
  "C:\PATH\TO\KAIRO-Ranking-Validation-Forward-Returns-v0.11\install_ranking_validation_v011.py" `
  "C:\Users\Jack\Documents\trading-bot"

Replace C:\PATH\TO with the folder where you extracted this bundle.

The installer backs up every replaced source file under:

source-backups\ranking-validation-v0.11-<timestamp>\

DATABASE
--------
The installer creates this table inside data\application.db:

opportunity_ranking_forward_outcomes

Existing data is preserved. KAIRO can measure eligible v0.10 ranking snapshots
when enough later market bars become available. It does not fabricate outcomes.

START KAIRO
-----------
Double-click:

C:\Users\Jack\Documents\trading-bot\Start Everything.bat

Open:

http://127.0.0.1:5173/ranking-validation

The Opportunity Ranking page also includes a Validate rankings button.

AUTOMATIC CAPTURE
-----------------
After each Intelligence Cycle, KAIRO now runs:

RANKING_FORWARD_RETURNS

The stage:

- Finds daily ranking cohorts that have matured
- Uses the resilient historical-data client and cache
- Records all newly available 1D, 5D and 20D outcomes
- Skips outcomes already recorded
- Isolates provider failures as warnings rather than crashing the cycle

DASHBOARD
---------
The Ranking Validation page includes:

- Measured and pending outcome counts
- Hit rate, average return and average SPY-relative alpha
- Opportunity Score versus return correlation
- Rank versus return correlation
- Top-three versus lower-ranked return comparison
- Execution-ready versus blocked comparison
- Score-band calibration
- Return by original rank
- Symbol and sector performance
- Latest measured outcomes
- 1D, 5D and 20D maturity views
- Strong warnings while samples are immature

INTERPRETING CORRELATION
------------------------
A positive Score correlation means higher Opportunity Scores have tended to
produce stronger returns in the measured sample.

A positive Rank correlation means better numerical ranks (for example #1 rather
than #8) have tended to produce stronger returns. Samples below 10 outcomes are
explicitly marked IMMATURE and should not be used for firm conclusions.

VALIDATION
----------
From the project root:

.\.venv\Scripts\python.exe -m pytest `
  tests/test_opportunity_ranking_validation.py `
  tests/test_web_opportunity_ranking.py `
  tests/test_intelligence_cycle_service.py `
  tests/test_opportunity_ranking_history.py `
  tests/test_opportunity_ranking_service.py -q

.\.venv\Scripts\python.exe -m pytest -q

Then validate the frontend:

cd .\frontend
npm run typecheck
npm run test -- src/__tests__/ranking-validation.test.tsx
npm run test
npm run build

EXPECTED FIRST RUN
------------------
The dashboard may initially show zero mature outcomes. This is correct. A v0.10
snapshot captured today cannot produce a forward result until at least the next
trading session is available. KAIRO will populate the page automatically as the
scheduled Intelligence Cycles continue.
