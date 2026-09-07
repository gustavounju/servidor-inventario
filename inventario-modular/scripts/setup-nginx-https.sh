#!/usr/bin/env bash
# ==============================================================================
# Script de configuracion automatica de Nginx como Reverse Proxy HTTPS
# para Inventario Modular (Spring Boot puerto 8081).
# Uso: sudo bash scripts/setup-nginx-https.sh
# ==============================================================================

set -euo pipefail

echo "==> 1. Verificando permisos de superusuario (root)..."
if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Este script debe ejecutarse con privilegios sudo o root." >&2
    exit 1
fi

echo "==> 2. Instalando Nginx y OpenSSL si no estan instalados..."
apt-get update -qq
apt-get install -y -qq nginx openssl

echo "==> 3. Verificando certificados SSL/TLS..."
CERT_DIR="/etc/ssl/certs"
KEY_DIR="/etc/ssl/private"
CERT_FILE="$CERT_DIR/inventario-modular.crt"
KEY_FILE="$KEY_DIR/inventario-modular.key"

if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
    echo "--> Generando certificado autofirmado para intranet (valido por 365 dias)..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$KEY_FILE" \
        -out "$CERT_FILE" \
        -subj "/C=AR/ST=Jujuy/L=San Pedro/O=Poder Judicial/OU=Informatica/CN=serverinventario"
    
    chmod 600 "$KEY_FILE"
    chmod 644 "$CERT_FILE"
    echo "--> Certificado generado en: $CERT_FILE"
else
    echo "--> Certificado existente detectado en $CERT_FILE"
fi

echo "==> 4. Copiando configuracion de Nginx..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONF_SOURCE="$SCRIPT_DIR/nginx/inventario-modular.conf"
CONF_TARGET="/etc/nginx/sites-available/inventario-modular"

if [ ! -f "$CONF_SOURCE" ]; then
    echo "ERROR: No se encontro el archivo $CONF_SOURCE" >&2
    exit 1
fi

cp "$CONF_SOURCE" "$CONF_TARGET"

# Habilitar sitio
ln -sf "$CONF_TARGET" /etc/nginx/sites-enabled/inventario-modular

# Deshabilitar default si existe
if [ -L "/etc/nginx/sites-enabled/default" ] || [ -f "/etc/nginx/sites-enabled/default" ]; then
    echo "--> Deshabilitando sitio default de Nginx..."
    rm -f /etc/nginx/sites-enabled/default
fi

echo "==> 5. Verificando sintaxis de Nginx..."
nginx -t

echo "==> 6. Reiniciando servicio Nginx..."
systemctl enable nginx
systemctl restart nginx

echo "==> 7. Ajustando reglas de Firewall UFW (si esta activo)..."
if command -v ufw >/dev/null 2>&1 && ufw status | grep -qw "active"; then
    ufw allow 80/tcp comment 'HTTP Nginx Redirection'
    ufw allow 443/tcp comment 'HTTPS Nginx Reverse Proxy'
    echo "--> Puertos 80 y 443 permitidos en UFW."
fi

SERVER_IP=$(hostname -I 2>/dev/null | awk '{print $1}' || echo "IP_DEL_SERVIDOR")

echo "=============================================================================="
echo " [OK] Nginx configurado exitosamente como Reverse Proxy HTTPS."
echo " Acceso seguro habilitado en:"
echo "   https://$SERVER_IP"
echo "   https://serverinventario (si esta resuelto por DNS/hosts)"
echo " Redireccion automatica de HTTP (puerto 80) a HTTPS (puerto 443) activa."
echo " Peticiones reenviadas internamente a Spring Boot en 127.0.0.1:8081."
echo "=============================================================================="
