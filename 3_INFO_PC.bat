@echo off
REM Guarda las caracteristicas de la PC en resultados\info_pc.txt (no cambia nada en la PC)
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\info_pc.ps1"
echo.
echo Terminado. Puedes cerrar esta ventana.
pause
