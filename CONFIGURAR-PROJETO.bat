@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo   VALTREN SOLUTIONS - AMBIENTE LOCAL
echo ==============================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_CMD=py -3"
) else (
  where python >nul 2>nul
  if errorlevel 1 (
    echo ERRO: Python nao foi encontrado neste computador.
    echo Instale o Python 3 e execute este arquivo novamente.
    pause
    exit /b 1
  )
  set "PYTHON_CMD=python"
)

echo [1/3] Preparando o projeto...
%PYTHON_CMD% scripts\materialize.py
if errorlevel 1 (
  echo.
  echo ERRO: Falha ao preparar o projeto.
  pause
  exit /b 1
)

echo [2/3] Iniciando servidor local na porta 4173...
start "VALTREN LOCAL SERVER" cmd /k "cd /d \"%~dp0\" && %PYTHON_CMD% -m http.server 4173 --bind 127.0.0.1"

timeout /t 2 /nobreak >nul

echo [3/3] Abrindo o site no navegador...
start "" "http://127.0.0.1:4173/"

echo.
echo Site iniciado em:
echo http://127.0.0.1:4173/
echo.
echo IMPORTANTE: mantenha a janela "VALTREN LOCAL SERVER" aberta enquanto estiver usando o site.
echo Para encerrar o servidor, feche aquela janela.
echo.
pause
