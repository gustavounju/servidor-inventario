INSERT INTO rol_modulo_permisos (rol_id, modulo_id, permiso_id)
SELECT r.id, m.id, p.id
FROM roles r
CROSS JOIN modulos m
CROSS JOIN permisos p
WHERE r.codigo = 'ADMINISTRADOR'
  AND m.codigo IN ('MUEBLES', 'PATRIMONIO', 'REPORTES')
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
WHERE r.codigo = 'PATRIMONIO'
  AND m.codigo IN ('MUEBLES', 'PATRIMONIO', 'REPORTES')
  AND p.codigo IN ('VER', 'CREAR', 'EDITAR', 'EXPORTAR')
  AND NOT EXISTS (
    SELECT 1
    FROM rol_modulo_permisos rmp
    WHERE rmp.rol_id = r.id
      AND rmp.modulo_id = m.id
      AND rmp.permiso_id = p.id
  );

CREATE TABLE muebles (
  id BIGINT NOT NULL AUTO_INCREMENT,
  codigo VARCHAR(80) NOT NULL,
  tipo VARCHAR(80) NOT NULL,
  descripcion VARCHAR(255) NOT NULL,
  ubicacion VARCHAR(180) NULL,
  fuero VARCHAR(120) NULL,
  responsable VARCHAR(120) NULL,
  estado VARCHAR(40) NOT NULL DEFAULT 'ACTIVO',
  observaciones VARCHAR(500) NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT uk_muebles_codigo UNIQUE (codigo),
  INDEX idx_muebles_estado (estado),
  INDEX idx_muebles_ubicacion (ubicacion),
  INDEX idx_muebles_fuero (fuero)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE bienes_patrimoniales (
  id BIGINT NOT NULL AUTO_INCREMENT,
  numero_patrimonial VARCHAR(80) NOT NULL,
  categoria VARCHAR(80) NOT NULL,
  descripcion VARCHAR(255) NOT NULL,
  ubicacion VARCHAR(180) NULL,
  fuero VARCHAR(120) NULL,
  custodio VARCHAR(120) NULL,
  estado VARCHAR(40) NOT NULL DEFAULT 'EN_USO',
  equipo_id BIGINT NULL,
  observaciones VARCHAR(500) NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT uk_bienes_patrimoniales_numero UNIQUE (numero_patrimonial),
  CONSTRAINT fk_bienes_patrimoniales_equipo FOREIGN KEY (equipo_id) REFERENCES equipos (id),
  INDEX idx_bienes_patrimoniales_estado (estado),
  INDEX idx_bienes_patrimoniales_equipo (equipo_id),
  INDEX idx_bienes_patrimoniales_fuero (fuero)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
