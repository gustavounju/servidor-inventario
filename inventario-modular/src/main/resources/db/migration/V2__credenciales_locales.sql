ALTER TABLE usuarios
  ADD COLUMN origen VARCHAR(20) NOT NULL DEFAULT 'AD' AFTER fuero;

UPDATE usuarios
SET origen = 'LOCAL'
WHERE username = 'admin.local';

CREATE TABLE credenciales_locales (
  usuario_id BIGINT NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  requiere_cambio_clave BOOLEAN NOT NULL DEFAULT FALSE,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (usuario_id),
  CONSTRAINT fk_credenciales_locales_usuario
    FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
