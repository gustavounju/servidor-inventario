CREATE TABLE IF NOT EXISTS configuraciones_sistema (
  clave VARCHAR(120) NOT NULL PRIMARY KEY,
  valor VARCHAR(500) NOT NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO configuraciones_sistema (clave, valor)
SELECT 'sitio_temporalmente_inactivo', 'false'
WHERE NOT EXISTS (
  SELECT 1 FROM configuraciones_sistema WHERE clave = 'sitio_temporalmente_inactivo'
);

INSERT INTO configuraciones_sistema (clave, valor)
SELECT 'sitio_mensaje_inactivo', 'El sistema esta temporalmente inactivo por tareas de mantenimiento.'
WHERE NOT EXISTS (
  SELECT 1 FROM configuraciones_sistema WHERE clave = 'sitio_mensaje_inactivo'
);

INSERT INTO configuraciones_sistema (clave, valor)
SELECT 'sitio_usuario_acceso_emergencia', 'gmurad'
WHERE NOT EXISTS (
  SELECT 1 FROM configuraciones_sistema WHERE clave = 'sitio_usuario_acceso_emergencia'
);
