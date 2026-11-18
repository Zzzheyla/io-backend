@echo off
REM Medicion oficial: 10 repeticiones x 3 lenguajes (unos 45 minutos).
REM Docker Desktop debe estar abierto. No uses la PC mientras corre.
cd /d "%~dp0"
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
"%GITBASH%" -c "bash scripts/ejecutar_pruebas.sh 2>&1 | tee resultados/log_ejecucion.txt"
echo.
echo Terminado. Puedes cerrar esta ventana.
pause
