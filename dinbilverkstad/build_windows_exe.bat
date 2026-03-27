@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d %~dp0

set "VENV_DIR=venv_win"

set "PY312_LOCAL=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if exist "%PY312_LOCAL%" (
  set "PY=%PY312_LOCAL%"
  goto havepy
)
set "PY312_LOCAL_ARM=%LOCALAPPDATA%\Programs\Python\Python312-arm64\python.exe"
if exist "%PY312_LOCAL_ARM%" (
  set "PY=%PY312_LOCAL_ARM%"
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
for %%I in (py python) do (
  %%I --version >nul 2>nul
  if not errorlevel 1 (
    set "PY=%%I"
    goto havepy
  )
)
echo Python saknas. Installera Python (64-bit) och försök igen.
pause
exit /b 1

:havepy
if exist "%VENV_DIR%" (
  if not exist "%VENV_DIR%\Scripts\python.exe" (
    rmdir /S /Q "%VENV_DIR%" >nul 2>nul
  )
)

if not exist "%VENV_DIR%\Scripts\python.exe" (
  "%PY%" -m venv "%VENV_DIR%"
)

if not exist "%VENV_DIR%\Scripts\python.exe" (
  echo Misslyckades att skapa venv (igen). Installera Python 64-bit från python.org och kryssa i "Add Python to PATH".
  echo Alternativt kör manuellt:  ^"<din python.exe> -m venv venv^"
  pause
  exit /b 1
)

call "%VENV_DIR%\Scripts\python.exe" -c "import sys; raise SystemExit(0 if sys.version_info < (3,13) else 1)" >nul 2>nul
if errorlevel 1 (
  echo Din Python-version ar for ny for PyInstaller/beroenden (t.ex. 3.13/3.14/3.15).
  echo Installera Python 3.12 (64-bit) fran python.org och bygg igen.
  pause
  exit /b 1
)

call "%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
call "%VENV_DIR%\Scripts\python.exe" -m pip install -r requirements.txt
call "%VENV_DIR%\Scripts\python.exe" -m pip install pyinstaller

call "%VENV_DIR%\Scripts\python.exe" -m pyinstaller --noconfirm --clean --onefile --name DinBilverkstad --add-data "templates;templates" --add-data "static;static" app.py

if not exist release\DinBilverkstad\data (
  mkdir release\DinBilverkstad\data
)

if exist dist\DinBilverkstad.exe (
  copy /Y dist\DinBilverkstad.exe release\DinBilverkstad\DinBilverkstad.exe >nul
  if exist install_windows.bat (
    copy /Y install_windows.bat release\DinBilverkstad\Install_DinBilverkstad.bat >nul
  )
  echo.
  echo KLAR!
  echo Skicka mappen: release\DinBilverkstad till kunden (eller kopiera till USB).
  echo Data sparas i: release\DinBilverkstad\data\dinbilverkstad.db
  echo For "installera-kansla": kor Install_DinBilverkstad.bat pa kundens dator (ingen Python kravs).
  echo.
  pause
  endlocal
  exit /b 0
)

echo Bygget misslyckades. Kör kommandot manuellt för att se fel:
echo venv\Scripts\python.exe -m pyinstaller ...
echo och kontrollera utskriften ovan.
echo.
pause
endlocal
exit /b 1
