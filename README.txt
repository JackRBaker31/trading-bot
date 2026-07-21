AUTHENTICATION AND AUDIT CLEAN REPLACEMENT

ADD OR REPLACE app files:
- app/authentication.py
- app/auth_repository.py
- app/auth_service.py
- app/audit.py
- app/audit_service.py
- app/run_create_admin.py
- app/application_errors.py

REPLACE web files:
- web/app.py
- web/dependencies.py

ADD OR REPLACE tests:
- tests/test_auth_service.py
- tests/test_audit_service.py
- tests/test_run_create_admin.py
- tests/test_web_jobs.py
- tests/test_web_paper_trading.py

Validated results:
- Focused tests: 22 passed
- Full suite: 948 passed
