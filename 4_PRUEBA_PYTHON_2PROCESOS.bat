@echo off
REM Comprobacion: Python (FastAPI) con 2 procesos de uvicorn, mismos limites (1 CPU, 512 MB).
REM 10 repeticiones, unos 15 minutos. Docker Desktop debe estar abierto. No uses la PC mientras corre.
cd /d "%~dp0"
set SOLO=python2
set REPS=10
set DURATION=60s
set WARMUP=15s
set "GITBASH=%ProgramFiles%\Git\bin\bash.exe"
if not exist "%GITBASH%" set "GITBASH=%LOCALAPPDATA%\Programs\Git\bin\bash.exe"
if not exist "%GITBASH%" (
  echo No se encontro Git Bash. Instala Git para Windows.
  pause
  exit /b 1
)
"%GITBASH%" -c "bash scripts/ejecutar_pruebas.sh 2>&1 | tee resultados/log_python2.txt"
echo.
echo Terminado. Puedes cerrar esta ventana.
pause
