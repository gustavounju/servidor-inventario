INSERT INTO modulos (codigo, nombre, descripcion, orden)
SELECT 'AUDITORIA', 'Auditoria', 'Eventos de cambios relevantes del sistema.', 95
WHERE NOT EXISTS (SELECT 1 FROM modulos WHERE codigo = 'AUDITORIA');

INSERT INTO rol_modulo_permisos (rol_id, modulo_id, permiso_id)
SELECT r.id, m.id, p.id
FROM roles r
CROSS JOIN modulos m
CROSS JOIN permisos p
WHERE r.codigo = 'ADMINISTRADOR'
  AND m.codigo = 'AUDITORIA'
  AND p.codigo IN ('VER', 'EXPORTAR', 'ADMINISTRAR')
  AND NOT EXISTS (
    SELECT 1
    FROM rol_modulo_permisos rmp
    WHERE rmp.rol_id = r.id
      AND rmp.modulo_id = m.id
      AND rmp.permiso_id = p.id
  );

CREATE TABLE auditoria_eventos (
  id BIGINT NOT NULL AUTO_INCREMENT,
  usuario VARCHAR(120) NOT NULL,
  modulo VARCHAR(60) NOT NULL,
  accion VARCHAR(80) NOT NULL,
  entidad_tipo VARCHAR(80) NOT NULL,
  entidad_id BIGINT NULL,
  detalle VARCHAR(1000) NOT NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_auditoria_eventos_creado (creado_en),
  INDEX idx_auditoria_eventos_modulo_entidad (modulo, entidad_tipo, entidad_id),
  INDEX idx_auditoria_eventos_usuario (usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
