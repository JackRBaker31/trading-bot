KAIRO OPPORTUNITY HISTORY & RANK DRIFT v0.10
==============================================

PURPOSE
-------
Adds durable history to the v0.9 Opportunity Ranking engine so KAIRO can show
whether a symbol is improving, weakening or moving only because competing
opportunities changed.

The update records:

- Opportunity score and absolute rank
- Calibrated confidence and expected return
- Evidence coverage and data quality
- Historical-match and measured-case maturity
- Execution readiness and blockers
- Full component-value breakdown
- First-seen and last-observed timestamps
- Meaningful contributor, blocker and readiness changes

The feature remains advisory only. It does not submit orders or change any risk,
execution, graduation, approval or paper-trading rule.

IMPORTANT BASELINE FIX
----------------------
This package also preserves the Windows-safe Supervisor PID check that prevents
the Operations Centre from falsely reporting "Supervisor Stale" while the
unified Platform Supervisor is running.

BEFORE INSTALLING
-----------------
1. Commit or back up the current v0.9 project.
2. In the KAIRO Platform Supervisor window, press Ctrl+C.
3. Run:

   C:\Users\Jack\Documents\trading-bot\Stop Everything.bat

4. Wait for API, Frontend, Worker and Scheduler to stop.

INSTALL
-------
Extract this ZIP, then open PowerShell and run:

cd C:\Users\Jack\Documents\trading-bot

.\.venv\Scripts\python.exe `
  "C:\PATH\TO\KAIRO-Opportunity-History-Rank-Drift-v0.10\install_opportunity_history_v010.py" `
  "C:\Users\Jack\Documents\trading-bot"

Replace C:\PATH\TO with the folder where you extracted this bundle.

The installer backs up every replaced source file under:

source-backups\opportunity-history-v0.10-<timestamp>\

DATABASE
--------
No manual migration command is required. KAIRO automatically creates:

opportunity_ranking_snapshots

inside data\application.db when the ranking service starts.

Existing data is not changed. History begins after v0.10 is installed; the
system does not invent or backfill rankings that were never captured.

START KAIRO
-----------
Double-click:

C:\Users\Jack\Documents\trading-bot\Start Everything.bat

Open:

http://127.0.0.1:5173/opportunity-ranking

HOW CAPTURE WORKS
-----------------
- A ranking snapshot is requested after every Intelligence Cycle.
- Viewing or refreshing Opportunity Ranking also keeps last-observed timestamps
  current.
- Identical observations are not duplicated.
- A new snapshot is always written when rank, category, readiness or blockers
  change.
- Score changes of at least 0.25 points are recorded.
- Component changes of at least 0.25 points are recorded even when the total
  score is broadly unchanged.

PAGE FEATURES
-------------
- 24-hour largest risers and fallers
- 24-hour, 7-day and 30-day symbol views
- Opportunity-score and rank chart
- Separate score movement and rank movement
- First-seen, last-observed and snapshot count
- Improving/weakening streak direction
- Component contribution changes
- Blocker-added and blocker-resolved history
- Execution-readiness transition history
- Meaningful-change timeline

VALIDATION
----------
From the project root:

.\.venv\Scripts\python.exe -m pytest `
  tests/test_opportunity_ranking_history.py `
  tests/test_opportunity_ranking_service.py `
  tests/test_web_opportunity_ranking.py `
  tests/test_intelligence_cycle_service.py `
  tests/test_supervisor_status_repository.py -q

.\.venv\Scripts\python.exe -m pytest -q

Then validate the frontend:

cd .\frontend
npm run typecheck
npm run test -- src/__tests__/opportunity-ranking.test.tsx
npm run test
npm run build

EXPECTED FIRST RUN
------------------
The history panel may initially show only one snapshot. This is correct. A chart
requires at least two meaningful snapshots. Let the next scheduled Intelligence
Cycle run, or allow the underlying evidence/rank to change, then refresh the page.

EXPECTED INTELLIGENCE CYCLE
---------------------------
New cycles include an OPPORTUNITY_RANKING_HISTORY stage. A history-capture issue
is isolated as a warning and does not crash or invalidate the rest of the cycle.
