#!/bin/bash
# Script de Migración y Configuración de MySQL para Inventario en Ubuntu

echo "Iniciando instalación y configuración de MySQL Server..."

# 1. Actualizar repositorios e instalar MySQL
sudo apt update
sudo apt install -y mysql-server

# 2. Iniciar el servicio y asegurar que inicie con el sistema
sudo systemctl enable mysql
sudo systemctl start mysql

# 3. Crear base de datos y usuario para el inventario
echo "Creando base de datos 'inventario_prod' y usuario 'usuario_inventario'..."
sudo mysql -e "CREATE DATABASE IF NOT EXISTS inventario_prod CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
sudo mysql -e "CREATE USER IF NOT EXISTS 'usuario_inventario'@'%' IDENTIFIED BY 'inventario_2025_seguro';"
sudo mysql -e "GRANT ALL PRIVILEGES ON inventario_prod.* TO 'usuario_inventario'@'%';"
sudo mysql -e "FLUSH PRIVILEGES;"

# 4. Configurar MySQL para escuchar en todas las interfaces (0.0.0.0)
# Esto es necesario para que la PC del trabajo (Windows) pueda conectarse remotamente
MYSQL_CONF="/etc/mysql/mysql.conf.d/mysqld.cnf"
if [ -f "$MYSQL_CONF" ]; then
    echo "Modificando mysqld.cnf para permitir conexiones externas..."
    sudo sed -i 's/^bind-address\s*=.*/bind-address = 0.0.0.0/' "$MYSQL_CONF"
else
    echo "ADVERTENCIA: No se encontró $MYSQL_CONF. Puede que necesites configurar bind-address manualmente."
fi

# 5. Reiniciar MySQL para aplicar configuración
echo "Reiniciando el servicio MySQL..."
sudo systemctl restart mysql

# 6. Configurar Firewall (UFW)
echo "Abriendo puerto 3306 (MySQL) en el Firewall..."
sudo ufw allow 3306/tcp

# 7. Instalar dependencias del sistema requeridas para Python/MySQL
sudo apt install -y python3-dev default-libmysqlclient-dev build-essential

echo "Instalación completada. Por favor, asegúrate de haber actualizado el archivo .env en el servidor."
echo "DB_HOST=localhost"
echo "DB_USER=usuario_inventario"
echo "DB_PASS=inventario_2025_seguro"
echo "DB_NAME=inventario_prod"
