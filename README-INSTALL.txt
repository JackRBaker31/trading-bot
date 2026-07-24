KAIRO PYTHON LAUNCHER V2
========================

Launcher v2 retains the working v1 startup behaviour
and adds a platform control centre.

FILES
-----
run_kairo.py
Start Everything.bat
KAIRO Status.bat
KAIRO Logs.bat
Stop Everything.bat
Restart Everything.bat
tests\test_run_kairo.py

INSTALL
-------
Copy the files into their matching folders.

Replace the existing root run_kairo.py and batch files.

START
-----
Double-click Start Everything.bat.

It detects existing services, starts only missing ones,
waits for API and frontend readiness, and opens the
dashboard. Process Supervisor is not used.

STATUS
------
Double-click KAIRO Status.bat, or run:

.\.venv\Scripts\python.exe .\run_kairo.py --status

The control centre displays:

- API, frontend, worker and scheduler state
- virtual environment
- frontend project
- application database
- core universe symbol count
- latest Intelligence Cycle
- duration
- articles fetched
- signals stored
- opportunities
- outcomes recorded
- warnings
- next scheduled run
- watchlist path
- provider

LOGS
----
Double-click KAIRO Logs.bat, or run:

.\.venv\Scripts\python.exe .\run_kairo.py --logs

Background-mode logs are stored in data\logs.

STOP / RESTART
--------------
Use Stop Everything.bat and Restart Everything.bat.

The launcher only stops process trees recorded in:

data\runtime\kairo-launcher-state.json

VALIDATE
--------
python -m pytest tests\test_run_kairo.py -q
python -m pytest -q

FIRST TEST
----------
1. Close all KAIRO windows.
2. Delete stale state if present:

Remove-Item `
    .\data\runtime\kairo-launcher-state.json `
    -ErrorAction SilentlyContinue

3. Double-click Start Everything.bat.
4. Confirm four windows and browser launch.
5. Double-click KAIRO Status.bat.
6. Confirm the control-centre information.
7. Run Start Everything.bat again and confirm no
   duplicate services are opened.
