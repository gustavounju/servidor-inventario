#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/inventario"

cd "$APP_DIR"

echo "=============================================="
echo "   ACTUALIZANDO SERVIDOR INVENTARIO GOLD"
echo "=============================================="

echo "[1/5] Git pull..."
git pull

echo "[2/5] Entorno virtual..."
python3 -m venv .venv
source .venv/bin/activate

echo "[3/5] Dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[4/5] Reiniciando servicio..."
sudo systemctl restart inventario

echo "[5/5] Estado actual..."
sudo systemctl status inventario --no-pager || true

echo "Listo. Si algo falla revisa: sudo journalctl -u inventario -n 100 --no-pager"
