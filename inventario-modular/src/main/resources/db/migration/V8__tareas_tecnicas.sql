INSERT INTO rol_modulo_permisos (rol_id, modulo_id, permiso_id)
SELECT r.id, m.id, p.id
FROM roles r
CROSS JOIN modulos m
CROSS JOIN permisos p
WHERE r.codigo = 'ADMINISTRADOR'
  AND m.codigo = 'TAREAS'
  AND p.codigo IN ('VER', 'CREAR', 'EDITAR', 'EXPORTAR', 'ADMINISTRAR')
  AND NOT EXISTS (
    SELECT 1
    FROM rol_modulo_permisos rmp
    WHERE rmp.rol_id = r.id
      AND rmp.modulo_id = m.id
      AND rmp.permiso_id = p.id
  );

CREATE TABLE tareas_tecnicas (
  id BIGINT NOT NULL AUTO_INCREMENT,
  equipo_id BIGINT NULL,
  titulo VARCHAR(180) NOT NULL,
  descripcion VARCHAR(1000) NULL,
  estado VARCHAR(40) NOT NULL DEFAULT 'PENDIENTE',
  prioridad VARCHAR(40) NOT NULL DEFAULT 'MEDIA',
  responsable VARCHAR(120) NULL,
  observaciones_cierre VARCHAR(1000) NULL,
  cerrado_en TIMESTAMP NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_tareas_tecnicas_estado (estado),
  INDEX idx_tareas_tecnicas_equipo (equipo_id),
  INDEX idx_tareas_tecnicas_responsable (responsable),
  CONSTRAINT fk_tareas_tecnicas_equipo FOREIGN KEY (equipo_id) REFERENCES equipos (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
