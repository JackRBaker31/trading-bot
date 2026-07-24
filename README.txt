KAIRO OPERATIONS TOOLKIT v4
===========================

This version deliberately uses simple batch commands.

Replace:

Start KAIRO.bat
Stop KAIRO.bat
Restart KAIRO.bat

Also copy:

Diagnose KAIRO.bat

TEST ORDER
----------

1. Run Diagnose KAIRO.bat.
2. Run Stop KAIRO.bat.
3. Run Start KAIRO.bat.
4. Confirm two separate windows open:
   - KAIRO Backend Supervisor
   - KAIRO Frontend
5. Open http://127.0.0.1:5173
6. Run Stop KAIRO.bat.
7. Run Restart KAIRO.bat.

All launcher windows pause before closing so any error remains visible.
