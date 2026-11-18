@echo off
REM Prueba rapida (unos 3 minutos; la primera vez 10-15 minutos por las descargas)
REM Docker Desktop debe estar abierto.
cd /d "%~dp0"
set REPS=1
set DURATION=15s
set WARMUP=5s
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
