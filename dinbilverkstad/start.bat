@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d %~dp0

set "PY312_LOCAL=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if exist "%PY312_LOCAL%" (
  set "PY=%PY312_LOCAL%"
  goto havepy
)
set "PY312_SYS=%ProgramFiles%\Python312\python.exe"
if exist "%PY312_SYS%" (
  set "PY=%PY312_SYS%"
  goto havepy
)

rem Prefer Python 3.12 explicitly (via py launcher), then fallback
py -3.12 --version >nul 2>nul
if not errorlevel 1 (
  set "PY=py -3.12"
  goto havepy
)
py --version >nul 2>nul
if not errorlevel 1 (
  set "PY=py"
  goto havepy
)
python --version >nul 2>nul
if not errorlevel 1 (
  set "PY=python"
  goto havepy
)
echo Python saknas. Installera Python (64-bit) och försök igen.
pause
exit /b 1

:havepy
%PY% -c "import sys; raise SystemExit(0 if sys.version_info < (3,13) else 1)" >nul 2>nul
if errorlevel 1 (
  echo Din Python-version ar for ny for den har appen (t.ex. 3.13/3.14/3.15).
  echo Installera Python 3.12 (64-bit) fran python.org och forsok igen.
  pause
  exit /b 1
)

%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt
set AUTO_OPEN=1
set PORT=5001
%PY% app.py
endlocal
