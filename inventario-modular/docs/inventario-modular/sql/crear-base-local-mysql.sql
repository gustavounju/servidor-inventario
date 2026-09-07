CREATE DATABASE IF NOT EXISTS inventario_modular
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'inventario_local'@'localhost'
  IDENTIFIED BY 'Cambiar_Clave_Local_123!';

ALTER USER 'inventario_local'@'localhost'
  IDENTIFIED BY 'Cambiar_Clave_Local_123!';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
  ON inventario_modular.* TO 'inventario_local'@'localhost';

FLUSH PRIVILEGES;
