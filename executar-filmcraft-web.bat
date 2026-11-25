@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 "%SCRIPT_DIR%run_filmcraft_web.py" %*
  set "RC=%ERRORLEVEL%"
  if not "%RC%"=="0" pause
  exit /b %RC%
)
where python >nul 2>nul
if not errorlevel 1 (
  python "%SCRIPT_DIR%run_filmcraft_web.py" %*
  set "RC=%ERRORLEVEL%"
  if not "%RC%"=="0" pause
  exit /b %RC%
)
echo Python 3.7+ nao foi encontrado. Instale Python e tente novamente.
pause
exit /b 127
