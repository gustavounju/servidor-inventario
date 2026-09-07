INSERT INTO modulos (codigo, nombre, descripcion, orden)
SELECT 'UBICACIONES', 'Ubicaciones', 'Oficinas, depositos, salas y racks vinculados al inventario.', 25
WHERE NOT EXISTS (SELECT 1 FROM modulos WHERE codigo = 'UBICACIONES');

INSERT INTO rol_modulo_permisos (rol_id, modulo_id, permiso_id)
SELECT r.id, m.id, p.id
FROM roles r
CROSS JOIN modulos m
CROSS JOIN permisos p
WHERE r.codigo = 'ADMINISTRADOR'
  AND m.codigo IN ('ACTAS', 'UBICACIONES')
  AND p.codigo IN ('VER', 'CREAR', 'EDITAR', 'EXPORTAR', 'ADMINISTRAR')
  AND NOT EXISTS (
    SELECT 1
    FROM rol_modulo_permisos rmp
    WHERE rmp.rol_id = r.id
      AND rmp.modulo_id = m.id
      AND rmp.permiso_id = p.id
  );

INSERT INTO rol_modulo_permisos (rol_id, modulo_id, permiso_id)
SELECT r.id, m.id, p.id
FROM roles r
CROSS JOIN modulos m
CROSS JOIN permisos p
WHERE r.codigo = 'TECNICO'
  AND m.codigo IN ('ACTAS', 'UBICACIONES')
  AND p.codigo IN ('VER', 'CREAR', 'EDITAR')
  AND NOT EXISTS (
    SELECT 1
    FROM rol_modulo_permisos rmp
    WHERE rmp.rol_id = r.id
      AND rmp.modulo_id = m.id
      AND rmp.permiso_id = p.id
  );

INSERT INTO rol_modulo_permisos (rol_id, modulo_id, permiso_id)
SELECT r.id, m.id, p.id
FROM roles r
CROSS JOIN modulos m
CROSS JOIN permisos p
WHERE r.codigo = 'PATRIMONIO'
  AND m.codigo IN ('ACTAS', 'UBICACIONES')
  AND p.codigo IN ('VER', 'CREAR', 'EDITAR', 'EXPORTAR')
  AND NOT EXISTS (
    SELECT 1
    FROM rol_modulo_permisos rmp
    WHERE rmp.rol_id = r.id
      AND rmp.modulo_id = m.id
      AND rmp.permiso_id = p.id
  );

CREATE TABLE actas (
  id BIGINT NOT NULL AUTO_INCREMENT,
  numero VARCHAR(80) NOT NULL,
  tipo VARCHAR(40) NOT NULL DEFAULT 'ENTREGA',
  equipo_id BIGINT NULL,
  fecha_emision DATE NULL,
  destinatario VARCHAR(180) NOT NULL,
  responsable_entrega VARCHAR(120) NULL,
  responsable_recepcion VARCHAR(120) NULL,
  detalle VARCHAR(1000) NOT NULL,
  estado VARCHAR(40) NOT NULL DEFAULT 'BORRADOR',
  observaciones VARCHAR(500) NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT uk_actas_numero UNIQUE (numero),
  CONSTRAINT fk_actas_equipo FOREIGN KEY (equipo_id) REFERENCES equipos (id),
  INDEX idx_actas_tipo_estado (tipo, estado),
  INDEX idx_actas_equipo (equipo_id),
  INDEX idx_actas_fecha_emision (fecha_emision)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ubicaciones (
  id BIGINT NOT NULL AUTO_INCREMENT,
  codigo VARCHAR(80) NOT NULL,
  nombre VARCHAR(180) NOT NULL,
  tipo VARCHAR(40) NOT NULL DEFAULT 'OFICINA',
  fuero VARCHAR(120) NULL,
  responsable VARCHAR(120) NULL,
  edificio VARCHAR(120) NULL,
  piso VARCHAR(40) NULL,
  estado VARCHAR(40) NOT NULL DEFAULT 'ACTIVA',
  observaciones VARCHAR(500) NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT uk_ubicaciones_codigo UNIQUE (codigo),
  INDEX idx_ubicaciones_tipo_estado (tipo, estado),
  INDEX idx_ubicaciones_fuero (fuero)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
