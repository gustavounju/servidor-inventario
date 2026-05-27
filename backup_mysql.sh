#!/bin/bash

# 1. Configuración de Rutas
BACKUP_DIR="/opt/inventario/backups"
LOG_FILE="$BACKUP_DIR/backup.log"
DATE=$(date +"%Y-%m-%d_%H%M")
BACKUP_FILE="$BACKUP_DIR/inventario_$DATE.sql.gz"
RETENTION_DAYS=15

# 2. Configuración de Base de Datos
# CORREGIDO: Ruta directa a /opt/inventario
APP_DIR="/opt/inventario"

mkdir -p "$BACKUP_DIR"

if [ -f "$APP_DIR/.env" ]; then
    export $(grep -v '^#' "$APP_DIR/.env" | xargs)
else
    echo "[$DATE] ERROR: No se encontró el archivo .env en $APP_DIR" >> "$LOG_FILE"
    exit 1
fi

echo "=================================================" >> "$LOG_FILE"
echo "[$DATE] INICIANDO BACKUP MYSQL" >> "$LOG_FILE"

# 3. Realizar el volcado
mysqldump -h "$DB_HOST" -P "$DB_PORT" -u "$DB_USER" -p"$DB_PASS" --single-transaction --quick --lock-tables=false --no-tablespaces "$DB_NAME" | gzip -9 > "$BACKUP_FILE"

if [ ${PIPESTATUS[0]} -eq 0 ]; then
    FILE_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
    echo "[$DATE] EXITOSO: Backup guardado como $BACKUP_FILE (Tamaño: $FILE_SIZE)" >> "$LOG_FILE"
else
    echo "[$DATE] ERROR: Falló la ejecución de mysqldump" >> "$LOG_FILE"
    rm -f "$BACKUP_FILE"
    exit 1
fi

# 4. Rotación
find "$BACKUP_DIR" -name "inventario_*.sql.gz" -type f -mtime +$RETENTION_DAYS -exec rm -f {} \; -print >> "$LOG_FILE"
echo "[$DATE] PROCESO FINALIZADO" >> "$LOG_FILE"
echo "=================================================" >> "$LOG_FILE"
