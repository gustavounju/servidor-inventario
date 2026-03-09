#!/bin/bash

# ==============================================================================
# SCRIPT DE BACKUP AUTOMATICO PARA MYSQL - INVENTARIO GOLD
# Genera un dump lógico de la base de datos completa y elimina copias antiguas
# ==============================================================================

# 1. Configuración de Rutas
BACKUP_DIR="/opt/inventario/backups"
LOG_FILE="$BACKUP_DIR/backup.log"
DATE=$(date +"%Y-%m-%d_%H%M")
BACKUP_FILE="$BACKUP_DIR/inventario_$DATE.sql.gz"
RETENTION_DAYS=15

# 2. Configuración de Base de Datos
# Lee las variables del archivo .env de producción
APP_DIR="/opt/inventario/servidorinventario"
if [ -f "$APP_DIR/.env" ]; then
    source "$APP_DIR/.env"
else
    echo "[$DATE] ERROR: No se encontró el archivo .env en $APP_DIR" >> "$LOG_FILE"
    exit 1
fi

# Crear directorio si no existe
mkdir -p "$BACKUP_DIR"

echo "=================================================" >> "$LOG_FILE"
echo "[$DATE] INICIANDO BACKUP MYSQL" >> "$LOG_FILE"

# 3. Realizar el volcado (dump) y comprimir on-the-fly a Gzip
# Esto bloquea temporalmente las tablas muy rápido para asegurar consistencia e ignora la BD de test
mysqldump -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" --single-transaction --quick --lock-tables=false "$DB_NAME" | gzip -9 > "$BACKUP_FILE"

# Verificar si el backup fue exitoso
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    FILE_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
    echo "[$DATE] EXITOSO: Backup guardado como $BACKUP_FILE (Tamaño: $FILE_SIZE)" >> "$LOG_FILE"
else
    echo "[$DATE] ERROR: Falló la ejecución de mysqldump" >> "$LOG_FILE"
    # Borrar el archivo defectuoso si se creó a medias
    rm -f "$BACKUP_FILE"
    exit 1
fi

# 4. Rotación (Limpieza de backups antiguos)
echo "[$DATE] Limpiando backups de más de $RETENTION_DAYS días..." >> "$LOG_FILE"
find "$BACKUP_DIR" -name "inventario_*.sql.gz" -type f -mtime +$RETENTION_DAYS -exec rm -f {} \; -print >> "$LOG_FILE"

echo "[$DATE] PROCESO FINALIZADO" >> "$LOG_FILE"
echo "=================================================" >> "$LOG_FILE"
