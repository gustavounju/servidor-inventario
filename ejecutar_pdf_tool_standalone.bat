@echo off
echo Iniciando Editor PDF Local standalone...
echo Punto de acceso: http://127.0.0.1:5090/pdf-local
echo.
set "ROOT=%~dp0"
"%ROOT%.venv\Scripts\python.exe" "%ROOT%standalone_pdf_tool\app.py"
