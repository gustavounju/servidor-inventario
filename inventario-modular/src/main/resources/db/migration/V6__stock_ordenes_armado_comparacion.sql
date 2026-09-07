INSERT INTO modulos (codigo, nombre, descripcion, orden)
SELECT 'ORDENES_ARMADO', 'Ordenes de Armado', 'Planificacion de equipos nuevos o mejoras con componentes esperados.', 55
WHERE NOT EXISTS (SELECT 1 FROM modulos WHERE codigo = 'ORDENES_ARMADO');

INSERT INTO rol_modulo_permisos (rol_id, modulo_id, permiso_id)
SELECT r.id, m.id, p.id
FROM roles r
CROSS JOIN modulos m
CROSS JOIN permisos p
WHERE r.codigo = 'ADMINISTRADOR'
  AND m.codigo IN ('STOCK', 'ORDENES_ARMADO')
  AND NOT EXISTS (
    SELECT 1
    FROM rol_modulo_permisos rmp
    WHERE rmp.rol_id = r.id
      AND rmp.modulo_id = m.id
      AND rmp.permiso_id = p.id
  );

CREATE TABLE stock_componentes (
  id BIGINT NOT NULL AUTO_INCREMENT,
  tipo VARCHAR(60) NOT NULL,
  estado VARCHAR(40) NOT NULL,
  descripcion VARCHAR(255) NOT NULL,
  marca VARCHAR(120) NULL,
  modelo VARCHAR(180) NULL,
  serial VARCHAR(180) NULL,
  capacidad VARCHAR(120) NULL,
  ubicacion VARCHAR(120) NULL,
  observaciones VARCHAR(500) NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_stock_componentes_tipo_estado (tipo, estado),
  INDEX idx_stock_componentes_serial (serial)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE ordenes_armado (
  id BIGINT NOT NULL AUTO_INCREMENT,
  equipo_id BIGINT NOT NULL,
  estado VARCHAR(40) NOT NULL,
  descripcion VARCHAR(255) NOT NULL,
  observaciones VARCHAR(500) NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT fk_ordenes_armado_equipo FOREIGN KEY (equipo_id) REFERENCES equipos (id),
  INDEX idx_ordenes_armado_equipo_estado (equipo_id, estado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE orden_armado_componentes (
  id BIGINT NOT NULL AUTO_INCREMENT,
  orden_id BIGINT NOT NULL,
  componente_id BIGINT NOT NULL,
  stock_componente_id BIGINT NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT fk_orden_armado_componentes_orden FOREIGN KEY (orden_id) REFERENCES ordenes_armado (id),
  CONSTRAINT fk_orden_armado_componentes_componente FOREIGN KEY (componente_id) REFERENCES componentes (id),
  CONSTRAINT fk_orden_armado_componentes_stock FOREIGN KEY (stock_componente_id) REFERENCES stock_componentes (id),
  INDEX idx_orden_armado_componentes_orden (orden_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
