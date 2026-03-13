#!/bin/bash
echo "=============================================="
echo "   ACTUALIZANDO SERVIDOR INVENTARIO GOLD (Linux)"
echo "=============================================="
echo ""

echo "1. Descargando cambios de GitLab..."
git pull

echo ""
echo "2. Verificando dependencias (fpdf2, etc)..."
# Si existe entorno virtual, activarlo (ajustar nombre si es necesario)
if [ -d "venv" ]; then
    source venv/bin/activate
fi
pip install -r requirements.txt --break-system-packages

echo ""
echo "=== LISTO ==="
echo "La base de datos se actualizará automáticamente al iniciar."
echo "Ahora ejecuta: python3 servidor.py"
