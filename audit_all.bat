@echo off
:: Ajustado para apuntar a tu carpeta real: SkillSpector-main
echo Iniciando auditoria de seguridad con SkillSpector...

:: Entramos a la carpeta y activamos el entorno virtual
call SkillSpector-main\.venv\Scripts\activate

:: Ejecutamos el escaneo en la carpeta actual (.) y guardamos el reporte
skillspector scan . --format markdown --output reporte_seguridad_final.md --no-llm

echo.
echo ========================================================
echo Auditoria completa. 
echo El reporte se ha guardado en: reporte_seguridad_final.md
echo ========================================================
pause