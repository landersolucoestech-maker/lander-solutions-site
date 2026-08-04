@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 scripts\materialize.py
) else (
  python scripts\materialize.py
)
if errorlevel 1 (
  echo.
  echo Falha ao configurar o projeto.
  pause
  exit /b 1
)
echo.
echo Projeto configurado. Abrindo servidor local em http://localhost:4173
start "" http://localhost:4173
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m http.server 4173
) else (
  python -m http.server 4173
)
