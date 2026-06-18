#!/usr/bin/env bash
# =============================================================
#  INVENTARIO GOLD - DEPLOY AUTOMATICO UBUNTU SERVER
#  Corre desde /opt/inventario luego del git pull
#  Solo pide datos si hay algo que no se puede deducir solo.
# =============================================================
set -euo pipefail

# ─── Configuracion conocida ──────────────────────────────────
APP_DIR="/opt/inventario"
SERVICE_NAME="inventario"
SYSTEMD_SRC="$APP_DIR/deployment/inventario.service"
SYSTEMD_DST="/etc/systemd/system/inventario.service"
NGINX_SRC="$APP_DIR/deployment/nginx_inventario.conf"
NGINX_DST_AVAIL="/etc/nginx/sites-available/inventario"
NGINX_DST_ENABLED="/etc/nginx/sites-enabled/inventario"

# Valores ya conocidos (cambialos aqui si cambian en el futuro)
KNOWN_DB_HOST="${1:-10.15.3.20}"   # pasar IP distinta: bash deploy_ubuntu.sh 10.15.3.X
KNOWN_DB_PORT="3306"
KNOWN_DB_NAME="inventario_prod"
KNOWN_DB_USER="gustavo_murad"
KNOWN_DB_PASS="justicia123"
KNOWN_INVENTARIO_IP="10.15.2.251"
KNOWN_INVENTARIO_HTTPS="https://${KNOWN_INVENTARIO_IP}:5000"
KNOWN_INVENTARIO_HTTP="http://${KNOWN_INVENTARIO_IP}:8080"

# ─── Funciones helpers ────────────────────────────────────────
ok()   { echo "  [OK] $*"; }
info() { echo "  --> $*"; }
warn() { echo "  [!]  $*"; }
step() { echo ""; echo "=== $* ==="; }

generar_secret_key() {
    python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null \
        || openssl rand -hex 32 2>/dev/null \
        || echo "$(date +%s)_inventario_secret_$(hostname)"
}

# ─── Header ──────────────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║      INVENTARIO GOLD - DEPLOY AUTOMATICO             ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ─── Verificar directorio ─────────────────────────────────────
if [[ ! -d "$APP_DIR" ]]; then
    echo "ERROR: no existe $APP_DIR. Clona el repo primero:"
    echo "  sudo mkdir -p /opt/inventario"
    echo "  sudo git clone https://gitlab.com/gustavoeliasm/servidorinventario.git /opt/inventario"
    exit 1
fi

cd "$APP_DIR"

# ─── PASO 1: git pull ─────────────────────────────────────────
step "1/7  Actualizando codigo desde GitLab"
git pull
ok "Codigo actualizado."

# ─── PASO 2: Entorno virtual y dependencias ───────────────────
step "2/7  Entorno virtual y dependencias"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
ok "Dependencias instaladas."

# ─── PASO 3: Generar/Verificar .env ──────────────────────────
step "3/7  Configuracion .env"

if [[ -f "$APP_DIR/.env" ]]; then
    ok ".env ya existe. Verificando variables criticas..."

    # Rellenar variables faltantes sin tocar las que ya existen
    source "$APP_DIR/.env" 2>/dev/null || true

    update_env() {
        local KEY="$1"
        local VAL="$2"
        if ! grep -q "^${KEY}=" "$APP_DIR/.env"; then
            echo "${KEY}=${VAL}" >> "$APP_DIR/.env"
            info "Agregado $KEY al .env"
        fi
    }

    update_env "DB_HOST"                         "$KNOWN_DB_HOST"
    update_env "DB_PORT"                         "$KNOWN_DB_PORT"
    update_env "DB_NAME"                         "$KNOWN_DB_NAME"
    update_env "INVENTARIO_PUBLIC_BASE_URL"      "$KNOWN_INVENTARIO_HTTPS"
    update_env "INVENTARIO_PUBLIC_HTTP_FALLBACK_URL" "$KNOWN_INVENTARIO_HTTP"
    update_env "SESSION_COOKIE_SECURE"           "false"
    update_env "AUTH_MODE"                       "local"
    update_env "BOOTSTRAP_ADMIN_USERNAME"        "administrador"
    update_env "BOOTSTRAP_ADMIN_PASSWORD"        "tdg729tdg"

    # Si FLASK_SECRET_KEY vacia o no existe, generar una
    if ! grep -q "^FLASK_SECRET_KEY=." "$APP_DIR/.env"; then
        SECRET=$(generar_secret_key)
        if grep -q "^FLASK_SECRET_KEY=" "$APP_DIR/.env"; then
            sed -i "s|^FLASK_SECRET_KEY=.*|FLASK_SECRET_KEY=${SECRET}|" "$APP_DIR/.env"
        else
            echo "FLASK_SECRET_KEY=${SECRET}" >> "$APP_DIR/.env"
        fi
        info "FLASK_SECRET_KEY generada automaticamente."
    fi

    # Rellenar credenciales MySQL si faltan
    update_env "DB_USER" "$KNOWN_DB_USER"
    update_env "DB_PASS" "$KNOWN_DB_PASS"

else
    # No existe .env → crearlo desde cero pidiendo solo credenciales MySQL
    warn ".env no encontrado. Creando uno nuevo..."

    SECRET=$(generar_secret_key)

    cat > "$APP_DIR/.env" <<EOF
# Generado automaticamente por deploy_ubuntu.sh
FLASK_SECRET_KEY=${SECRET}

DB_HOST=${KNOWN_DB_HOST}
DB_PORT=${KNOWN_DB_PORT}
DB_USER=${KNOWN_DB_USER}
DB_PASS=${KNOWN_DB_PASS}
DB_NAME=${KNOWN_DB_NAME}

SESSION_COOKIE_SECURE=false

INVENTARIO_PUBLIC_BASE_URL=${KNOWN_INVENTARIO_HTTPS}
INVENTARIO_PUBLIC_HTTP_FALLBACK_URL=${KNOWN_INVENTARIO_HTTP}

BOOTSTRAP_ADMIN_USERNAME=administrador
BOOTSTRAP_ADMIN_PASSWORD=tdg729tdg

AUTH_MODE=local

# Active Directory (dejar vacio hasta activarlo)
AD_SERVER=
AD_DOMAIN=
AD_BASE_DN=
AD_USE_SSL=false
AD_CONNECT_TIMEOUT=5
AD_SUPERUSERS=
EOF
    ok ".env creado con las variables del sistema."
fi

ok ".env listo."

# ─── PASO 4: systemd ─────────────────────────────────────────
step "4/7  Servicio systemd"
sudo cp "$SYSTEMD_SRC" "$SYSTEMD_DST"
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME" --quiet
ok "Service instalado y habilitado."

# ─── PASO 5: Nginx ───────────────────────────────────────────
step "5/7  Nginx"
# PRECAUCION: Comentado para no pisar la configuracion manual del dominio (taller-sp)
# que hizo el administrador de redes en produccion.
# sudo cp "$NGINX_SRC" "$NGINX_DST_AVAIL"
# sudo ln -sf "$NGINX_DST_AVAIL" "$NGINX_DST_ENABLED"
if sudo nginx -t 2>/dev/null; then
    ok "Configuracion Nginx valida."
else
    warn "Nginx reporta un error. Revisa la config antes de continuar."
    sudo nginx -t
fi

# ─── PASO 6: Reiniciar servicios ─────────────────────────────
step "6/7  Reiniciando servicios"
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl restart nginx
ok "Servicios reiniciados."

# ─── PASO 7: Estado y logs ───────────────────────────────────
step "7/7  Estado del sistema"
sleep 2   # dar 2 segundos a gunicorn para que levante
sudo systemctl status "$SERVICE_NAME" --no-pager -l
echo ""
info "Ultimas 50 lineas de log:"
sudo journalctl -u "$SERVICE_NAME" -n 50 --no-pager

# ─── Resumen final ───────────────────────────────────────────
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  DEPLOY COMPLETADO                                   ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  HTTPS:    ${KNOWN_INVENTARIO_HTTPS}              ║"
echo "║  HTTP:     ${KNOWN_INVENTARIO_HTTP}               ║"
echo "║  DB:       ${KNOWN_DB_HOST}:${KNOWN_DB_PORT}/${KNOWN_DB_NAME}          ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  Login inicial (si app_users vacia):                 ║"
echo "║    Usuario: administrador                            ║"
echo "║    Clave:   tdg729tdg                                ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
