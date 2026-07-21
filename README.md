# KAIRO Infrastructure Observability Build

Add:
- app/worker_heartbeat.py
- app/worker_heartbeat_repository.py
- app/infrastructure_status.py
- app/infrastructure_status_service.py
- tests/test_worker_heartbeat_repository.py
- tests/test_infrastructure_status_service.py
- tests/test_web_infrastructure.py

Replace:
- app/job_worker.py
- app/run_job_worker.py
- web/app.py
- web/dependencies.py

New endpoints:
- GET /api/infrastructure/status
- GET /api/workers/job/status

Worker behavior:
- Heartbeat every 5 seconds while idle or busy
- BUSY status includes current job ID and type
- IDLE status confirms the worker is waiting for work
- STOPPED is written during graceful shutdown
- A heartbeat older than 30 seconds is reported as STALE/OFFLINE

Important:
After installing, stop and restart the job worker so it begins writing heartbeats.

Validated:
- Focused tests: 9 passed
- Full suite: 976 passed
