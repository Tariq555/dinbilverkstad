@echo off
setlocal EnableExtensions
cd /d %~dp0

set "SRC=%~dp0"
set "INSTALL_DIR=%LOCALAPPDATA%\DinBilverkstad"

if not exist "%SRC%DinBilverkstad.exe" (
  echo Hittar inte DinBilverkstad.exe i denna mapp.
  echo Kopiera hela mappen "DinBilverkstad" (med exe och data) till datorn och forsok igen.
  pause
  exit /b 1
)

if not exist "%INSTALL_DIR%" (
  mkdir "%INSTALL_DIR%"
)

xcopy "%SRC%*" "%INSTALL_DIR%\" /E /I /Y >nul

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$desktop=[Environment]::GetFolderPath('Desktop');" ^
  "$startMenu=[Environment]::GetFolderPath('StartMenu');" ^
  "$appDir=Join-Path $env:LOCALAPPDATA 'DinBilverkstad';" ^
  "$exe=Join-Path $appDir 'DinBilverkstad.exe';" ^
  "$name='Din Bilverkstad';" ^
  "$ws=New-Object -ComObject WScript.Shell;" ^
  "$lnk=$ws.CreateShortcut((Join-Path $desktop ($name + '.lnk')));" ^
  "$lnk.TargetPath=$exe;" ^
  "$lnk.WorkingDirectory=$appDir;" ^
  "$lnk.IconLocation=($exe + ',0');" ^
  "$lnk.Save();" ^
  "$programs=Join-Path $startMenu 'Programs';" ^
  "if (!(Test-Path $programs)) { New-Item -ItemType Directory -Path $programs | Out-Null }" ^
  "$lnk2=$ws.CreateShortcut((Join-Path $programs ($name + '.lnk')));" ^
  "$lnk2.TargetPath=$exe;" ^
  "$lnk2.WorkingDirectory=$appDir;" ^
  "$lnk2.IconLocation=($exe + ',0');" ^
  "$lnk2.Save();"

echo.
echo KLAR!
echo Installerad i: %INSTALL_DIR%
echo En genvag har skapats pa Skrivbordet och i Start-menyn.
echo.

start "" "%INSTALL_DIR%\DinBilverkstad.exe"
endlocal
