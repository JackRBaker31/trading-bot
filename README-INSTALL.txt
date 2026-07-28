KAIRO OPPORTUNITY RANKING v0.9
================================

PURPOSE
-------
Adds a new advisory-only Opportunity Ranking engine and page. It combines:

- Investment thesis quality
- Conservatively calibrated confidence
- Evidence/capability coverage
- Technical and macro alignment
- True historical similarity
- Measured expected return
- Symbol and sector performance
- Risk tier
- Execution readiness
- Market-data health and freshness

The ranking does NOT submit orders or weaken any execution, risk, approval,
graduation or paper-trading gate.

BEFORE INSTALLING
-----------------
1. Commit or back up the current v0.8.1 project.
2. In the KAIRO Platform Supervisor window, press Ctrl+C.
3. Run:

   C:\Users\Jack\Documents\trading-bot\Stop Everything.bat

4. Wait for API, Frontend, Worker and Scheduler to stop.

INSTALL
-------
Extract this ZIP, then open PowerShell and run:

cd C:\Users\Jack\Documents\trading-bot

.\.venv\Scripts\python.exe `
  "C:\PATH\TO\KAIRO-Opportunity-Ranking-v0.9\install_opportunity_ranking_v09.py" `
  "C:\Users\Jack\Documents\trading-bot"

Replace C:\PATH\TO with the folder where you extracted this bundle.

The installer backs up every replaced source file under:

source-backups\opportunity-ranking-v0.9-<timestamp>\

START KAIRO
-----------
Double-click:

C:\Users\Jack\Documents\trading-bot\Start Everything.bat

Open:

http://127.0.0.1:5173/opportunity-ranking

The sidebar will also contain a new Opportunity Ranking link.

VALIDATION
----------
From the project root:

.\.venv\Scripts\python.exe -m pytest `
  tests/test_opportunity_ranking_service.py `
  tests/test_web_opportunity_ranking.py -q

.\.venv\Scripts\python.exe -m pytest -q

Then validate the frontend:

cd .\frontend
npm run typecheck
npm run test -- src/__tests__/opportunity-ranking.test.tsx
npm run test
npm run build

EXPECTED BEHAVIOUR
------------------
The page should show:

- Ranked current opportunities
- Opportunity score out of 100
- Priority Ready / High Potential Blocked / Promising Immature / Watch states
- Raw and calibrated confidence
- Measured expected return, or a clear unavailable state
- Evidence quality and coverage
- Historical matches and measured-case maturity
- Full ten-component score breakdown
- Positive contributors, penalties and improvement actions
- Links into Decision Explainability and KAIRO Copilot

NOTES
-----
- The current shortlist is based on KAIRO's existing top opportunities.
- Missing measured data scores as unavailable; it is never fabricated.
- Early samples are deliberately maturity-weighted and conservative.
- The ranking uses a 90-day measured-performance review window.
- No database migration is required.
