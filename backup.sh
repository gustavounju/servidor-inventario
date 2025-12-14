#!/bin/bash

# Configuración
DB_PATH="/opt/inventario/inventario.db"
BACKUP_DIR="/opt/inventario/backups"
DATE=$(date +"%Y-%m-%d_%H%M")
BACKUP_FILE="$BACKUP_DIR/inventario_$DATE.db"

# Crear directorio si no existe
mkdir -p "$BACKUP_DIR"

# Realizar copia (usando sqlite3 .backup para seguridad si está en uso, o cp simple)
# Opcion 1: cp simple (si el tráfico es bajo es suficiente)
cp "$DB_PATH" "$BACKUP_FILE"

# Opcion 2: sqlite3 (más seguro si hay muchas escrituras concurrentes)
# sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"

# Log
echo "[$DATE] Backup creado en: $BACKUP_FILE" >> "$BACKUP_DIR/backup.log"

# Rotación: Borrar backups mayores a 30 días
find "$BACKUP_DIR" -name "inventario_*.db" -mtime +30 -delete
