@echo off
echo ==============================================
echo   ACTUALIZANDO SERVIDOR INVENTARIO GOLD
echo ==============================================
echo.
echo 1. Descargando ultimos cambios de GitHub...
git pull origin develop
if %ERRORLEVEL% NEQ 0 (
    echo Error al descargar cambios.
    pause
    exit /b
)
echo.

echo 2. Actualizando dependencias (fpdf2, etc)...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo Error al instalar dependencias.
    pause
    exit /b
)
echo.

echo 3. Iniciando Servidor...
echo    (Las tablas de BD se verifican automaticamente al iniciar)
python servidor.py
pause
