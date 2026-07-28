KAIRO SUPERVISOR UNIFICATION v0.8.1
==================================

PURPOSE
-------
This update replaces the worker-only launcher watchdog with one authoritative
KAIRO Platform Supervisor. The same run_kairo.py process now monitors:

- API
- Frontend
- Job Worker
- Scheduler

It writes the status already consumed by the Dashboard and Operations Centre,
so the Platform Supervisor card reports the supervisor that is actually running.

IMPORTANT: STOP KAIRO FIRST
---------------------------
1. In the existing Start Everything / worker-watchdog window, press Ctrl+C.
   Wait until it says monitoring has stopped.

2. Run:

   C:\Users\Jack\Documents\trading-bot\Stop Everything.bat

3. Confirm the API, Frontend, Worker and Scheduler windows have closed.

INSTALL
-------
Extract this ZIP to a normal folder.

Open PowerShell and run:

cd C:\Users\Jack\Documents\trading-bot

.\.venv\Scripts\python.exe `
  "C:\PATH\TO\KAIRO-Supervisor-Unification-v0.8.1\install_supervisor_unification_v081.py" `
  "C:\Users\Jack\Documents\trading-bot"

Replace C:\PATH\TO with the folder where this bundle was extracted.

The installer creates a source backup under:

source-backups\supervisor-unification-v0.8.1-<timestamp>\

START
-----
Double-click:

C:\Users\Jack\Documents\trading-bot\Start Everything.bat

The main window should now show:

KAIRO PLATFORM SUPERVISOR ACTIVE
Monitoring API, Frontend, Job Worker and Scheduler...

VALIDATE
--------
In a separate PowerShell window:

cd C:\Users\Jack\Documents\trading-bot
.\.venv\Scripts\python.exe .\run_kairo.py --status

Expected service section:

Platform Supervisor   RUNNING
API                   HEALTHY
Frontend              HEALTHY
Job Worker            RUNNING
Scheduler             RUNNING

Then open the KAIRO Dashboard / Operations Centre. The Platform Supervisor card
should show RUNNING, 4 services managed, 4 healthy, and automatic recovery enabled.

RUN TESTS
---------
Backend focused validation:

.\.venv\Scripts\python.exe -m pytest `
  tests\test_run_kairo.py `
  tests\test_infrastructure_status_service.py `
  tests\test_web_infrastructure.py -q

Full validation:

.\.venv\Scripts\python.exe -m pytest -q

cd .\frontend
npm run typecheck
npm run test
npm run build

RECOVERY TEST
-------------
Only after the status is fully healthy:

1. Note the Job Worker PID from Task Manager or PowerShell.
2. End only the Job Worker process.
3. Watch the Platform Supervisor window.
4. It should report SERVICE_LOST / RECOVERING and start a replacement.
5. Operations Centre should briefly show DEGRADED, then return to RUNNING.

Do not kill the API or Frontend until the worker recovery test has passed.

WHAT CHANGED
------------
- Unified supervision for all four platform services.
- Independent restart history and restart limits per service.
- API readiness and Worker/Scheduler heartbeat health checks.
- Frontend HTTP health checks.
- Atomic data\supervisor_status.json updates every monitor cycle.
- Safe prevention of multiple supervisor instances.
- Stop Everything now stops the active monitor before stopping services.
- Restart Everything restarts KAIRO with supervision enabled.
- Dashboard guidance now points to Start Everything.bat rather than the retired
  app.run_process_supervisor command.
- Legacy data\kairo_supervisor.pid is removed during installation.

NOT CHANGED
-----------
- Trading logic
- Risk limits
- Order execution
- Database schema
- Paper-trading permissions
- Intelligence scoring
