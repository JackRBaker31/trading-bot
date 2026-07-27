KAIRO HISTORICAL SIMILARITY V0.7
==================================

PURPOSE
-------
Replace the aggregate "Observed History" view with genuine historical
feature-vector matching backed by KAIRO's existing decision memory and
measured decision outcomes.

WHAT IT ADDS
------------
- HistoricalSimilarityService with deterministic KAIRO-HSIM-1.0 scoring
- authenticated GET /api/copilot/historical-similarity/{symbol}
- live single-symbol thesis generation, rather than rebuilding every symbol
- comparison against older decision_memory capability vectors
- nearest-horizon matching against decision_outcomes
- directional win rate, raw return, directional return, alpha and hold period
- sample-quality labels and explicit small-sample warnings
- closest-case explanations showing matching and differing factors
- true Historical Similarity tab inside Decision Explainability
- lazy loading: provider requests begin only when that tab is opened
- backend and frontend tests

SIMILARITY METHOD
-----------------
KAIRO-HSIM-1.0 weights:
- capability score profile: 36 points
- capability stance alignment: 8 points
- capability availability: 4 points
- overall score: 8 points
- confidence: 8 points
- capability coverage: 5 points
- recommendation: 5 points
- risk tier: 4 points
- time horizon: 4 points
- primary driver: 4 points
- news event type: 8 points
- symbol match: 6 points

A case must reach 65% similarity by default. Matching does not bypass
risk, graduation, approved-symbol or execution gates.

DATABASE
--------
No new database tables are created.

The engine reads:
- decision_memory
- decision_outcomes

KAIRO already stores capability vectors in decision_memory.capabilities_json.
This release turns those stored vectors into a reproducible similarity model.

INSTALL
-------
1. Stop KAIRO completely.

2. Extract this bundle outside the project.

3. Open PowerShell at:

C:\Users\Jack\Documents\trading-bot

4. Run with the real extracted path:

.\.venv\Scripts\python.exe `
    "C:\Path\To\KAIRO-Historical-Similarity-v0.7\install_historical_similarity_v07.py"

The installer backs up every replaced file under:

source-backups\historical-similarity-v0.7-<timestamp>\

BACKEND VALIDATION
------------------
.\.venv\Scripts\python.exe -m pytest `
    tests\test_historical_similarity_service.py `
    tests\test_investment_thesis_service.py `
    tests\test_web_historical_similarity.py `
    -q

Expected focused result:

7 passed

Then run the complete backend suite:

.\.venv\Scripts\python.exe -m pytest -q

Expected result for the supplied source baseline:

1159 passed

FRONTEND VALIDATION
-------------------
cd .\frontend

npm run typecheck
npm run test
npm run build

cd ..

TypeScript validation passed while preparing this bundle. The available
packaging environment contained Windows node_modules and could not execute
Linux Rollup/Vitest native binaries, so run the test and build commands on
your Windows installation.

FUNCTIONAL CHECK
----------------
1. Start KAIRO normally with Start Everything.bat.
2. Open Decision Explainability.
3. Select a ranked symbol.
4. Open Historical Similarity.
5. Confirm:
   - candidate and matched-case counts appear;
   - the sample-quality badge appears;
   - measured cases show directional returns;
   - matching and differing factors appear;
   - warnings remain visible when the sample is small.

EARLY EMPTY STATES ARE CORRECT
------------------------------
A new installation may show no measured matches. That is not a failure.

Similarity needs:
- older records in decision_memory;
- due measurements in decision_outcomes.

Investment Theses captures decision-memory records. The existing Copilot
Decision Outcomes control captures due 1/7/30/90/180/365-day outcomes.

API
---
GET /api/copilot/historical-similarity/AAPL
GET /api/copilot/historical-similarity/AAPL?minimum_similarity_percent=70&limit=10

The endpoint requires authentication.

PERFORMANCE / API USE
---------------------
The frontend does not request similarity on initial page load. It loads only
when Historical Similarity is opened.

The backend builds only the selected symbol's current thesis. This avoids
recalculating technical and macro capabilities for every ranked symbol in
one request. React Query caches each symbol report for 60 seconds.

SAFETY
------
This release is research-only. It does not:
- submit orders;
- change position sizing;
- alter risk limits;
- alter graduation requirements;
- enable real-money trading;
- modify historical decisions or outcomes.
