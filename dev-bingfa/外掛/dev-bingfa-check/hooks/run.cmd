@echo off
rem dev-bingfa-check launcher (Windows without Git Bash; Claude Code then runs hooks in PowerShell)
rem   run.cmd post     - run post_check.py (which runs check_silence.py) if Python works; otherwise skip quietly
rem                      exit code is 2 only for a real finding; anything else becomes 0
rem   run.cmd session  - if Python is missing, print the "not enabled" notice (once per session)
rem A candidate counts only if it really runs: the Microsoft Store "python" stub exits non-zero.
rem It must also be Python 3.8 or newer: an older one (2.x, 3.7) counts as "no Python", so the notice shows.
rem "call" keeps working when python is a .bat/.cmd shim (e.g. pyenv-win).
setlocal
set "PY="
call py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1 && set "PY=py -3"
if not defined PY call python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1 && set "PY=python"
if not defined PY call python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1 && set "PY=python3"

if /i "%~1"=="session" goto session
if not defined PY exit /b 0
call %PY% "%~dp0post_check.py"
if errorlevel 3 exit /b 0
if errorlevel 2 exit /b 2
exit /b 0

:session
if not defined PY type "%~dp0no-python.json"
exit /b 0
