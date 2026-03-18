#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/inventario"
SERVICE_NAME="inventario"
NGINX_SITE_SRC="$APP_DIR/deployment/nginx_inventario.conf"
NGINX_SITE_DST="/etc/nginx/sites-available/inventario"
SYSTEMD_SRC="$APP_DIR/deployment/inventario.service"
SYSTEMD_DST="/etc/systemd/system/inventario.service"

echo "=============================================="
echo "  INVENTARIO GOLD - DEPLOY UBUNTU"
echo "=============================================="

if [[ ! -d "$APP_DIR" ]]; then
    echo "ERROR: no existe $APP_DIR"
    exit 1
fi

cd "$APP_DIR"

echo "[1/8] Actualizando codigo desde GitLab..."
git pull

echo "[2/8] Verificando entorno virtual..."
python3 -m venv .venv
source .venv/bin/activate

echo "[3/8] Actualizando pip e instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[4/8] Verificando .env..."
if [[ ! -f "$APP_DIR/.env" ]]; then
    echo "ERROR: falta $APP_DIR/.env"
    echo "Copia .env.example a .env y completa las variables antes de continuar."
    exit 1
fi

echo "[5/8] Instalando service de systemd..."
sudo cp "$SYSTEMD_SRC" "$SYSTEMD_DST"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"

echo "[6/8] Instalando config de Nginx..."
sudo cp "$NGINX_SITE_SRC" "$NGINX_SITE_DST"
sudo ln -sf "$NGINX_SITE_DST" "/etc/nginx/sites-enabled/inventario"
sudo nginx -t

echo "[7/8] Reiniciando servicios..."
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl restart nginx

echo "[8/8] Estado final..."
sudo systemctl status "$SERVICE_NAME" --no-pager || true
sudo journalctl -u "$SERVICE_NAME" -n 60 --no-pager || true

echo ""
echo "Deploy finalizado."
echo "Login inicial si app_users esta vacia: administrador / tdg729tdg"
