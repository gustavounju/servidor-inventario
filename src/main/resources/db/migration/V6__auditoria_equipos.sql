CREATE TABLE movimientos_equipo (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    equipo_id BIGINT NOT NULL,
    tipo_movimiento VARCHAR(60) NOT NULL,
    usuario_destino VARCHAR(120),
    ubicacion_origen VARCHAR(120),
    ubicacion_destino VARCHAR(120),
    registrado_por VARCHAR(120) NOT NULL,
    observaciones VARCHAR(500),
    fecha_movimiento DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_movimientos_equipo FOREIGN KEY (equipo_id) REFERENCES equipos(id) ON DELETE CASCADE
);
