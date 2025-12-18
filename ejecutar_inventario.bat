@echo off
REM Script de arranque seguro para Inventario en Windows 7/10
REM Bypasses ExecutionPolicy para permitir correr el script sin configuracion previa

echo Iniciando inventario...
echo Si ves errores rojos, por favor toma una foto o captura.
echo.

PowerShell.exe -NoProfile -ExecutionPolicy Bypass -File "inventario.ps1"

echo.
echo ========================================================
echo   El proceso ha finalizado.
echo   Por favor revisa si hubo mensajes de "EXITO" arriba.
echo ========================================================
pause
