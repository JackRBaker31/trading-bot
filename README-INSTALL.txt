KAIRO PERFORMANCE INTELLIGENCE V1
=================================

PURPOSE
-------
Turn KAIRO's existing SQLite history into reusable daily,
weekend, weekly and monthly operational/intelligence reviews.

WHAT IT ADDS
------------
- PerformanceReviewService over data/application.db
- authenticated GET /api/performance/review
- date-range query support using start/end ISO timestamps
- deterministic executive summary and recommendations
- system health, research, decision, outcome and confidence metrics
- exportable Markdown report
- frontend Performance Intelligence page
- presets: Last 24 Hours, Weekend Review, Last 7 Days, Last 30 Days
- navigation entry in the KAIRO sidebar
- backend and frontend tests

NO DATABASE MIGRATION
---------------------
This release is read-only against the existing database.
It creates no tables and modifies no historical records.

INSTALL
-------
1. Stop KAIRO completely.

2. Extract this bundle outside the project.

3. Open PowerShell at:

C:\Users\Jack\Documents\trading-bot

4. Run with the real extracted path:

.\.venv\Scripts\python.exe `
    "C:\Path\To\KAIRO-Performance-Intelligence-v1\install_performance_intelligence_v1.py"

The installer backs up every replaced source file under:

source-backups\performance-intelligence-v1-<timestamp>\

BACKEND VALIDATION
------------------
.\.venv\Scripts\python.exe -m pytest `
    tests\test_performance_review_service.py `
    -q

.\.venv\Scripts\python.exe -m pytest -q

Expected full backend result for the supplied baseline:

1153 passed

FRONTEND VALIDATION
-------------------
cd .\frontend
npm run typecheck
npm run test
npm run build
cd ..

The build environment used to prepare this bundle did not have
frontend node_modules available, so run these three commands on
your PC before committing.

START
-----
Start KAIRO normally with Start Everything.bat.

Open the new sidebar item:

Performance Intelligence

The Weekend Review preset begins at 17:00 on the most recent
Friday and ends at the current time.

API
---
GET /api/performance/review
GET /api/performance/review?start=<ISO>&end=<ISO>

The endpoint requires authentication.

METRICS
-------
System Health:
- total jobs and intelligence cycles
- success/warning/failure/abandoned counts
- healthy completion percentage
- average and longest successful cycle duration
- stages producing warnings

Research Activity:
- runs, created, skipped and failed items
- skip rate
- articles fetched and signals stored by intelligence cycles
- provider cycle counts

Decision Intelligence:
- shadow decisions
- eligible decisions
- confidence
- actions and most-active symbols
- opportunities and skipped decisions

Shadow Performance:
- total and measured decisions
- directional success
- profitable-after-cost percentage
- captured outcomes/snapshots
- price-operation failures

Confidence Calibration:
- average/latest snapshot confidence
- stale snapshot share where the stored status supports it
- shadow-decision confidence bands

INTERPRETATION
--------------
The report deliberately warns when the decision sample is too
small. Do not treat a few weekend outcomes as evidence of a
profitable strategy.

The report is deterministic and evidence-based. It does not use
an external language model or invent missing data.

COMMIT
------
After backend and frontend checks pass:

git add -A
git diff --cached --check
git commit -m "Add performance intelligence reviews"
git push
