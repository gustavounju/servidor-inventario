ALTER TABLE tareas_tecnicas
  ADD COLUMN solicitante_username VARCHAR(120) NULL,
  ADD COLUMN solicitante_nombre VARCHAR(180) NULL,
  ADD COLUMN solicitante_fuero VARCHAR(120) NULL,
  ADD COLUMN creado_por VARCHAR(120) NULL;

UPDATE tareas_tecnicas
SET solicitante_username = COALESCE(solicitante_username, responsable, 'sin-solicitante'),
    solicitante_nombre = COALESCE(solicitante_nombre, responsable, 'Sin solicitante informado'),
    solicitante_fuero = COALESCE(solicitante_fuero, 'Sin fuero informado'),
    creado_por = COALESCE(creado_por, responsable)
WHERE solicitante_username IS NULL;

INSERT INTO equipos (nombre, ultimo_usuario, fuero, ubicacion, sistema_operativo, monitoreo, activo)
SELECT 'PC-GENERICA', 'Sin asignar', 'Sin fuero informado', 'Mesa de ayuda', 'No aplica', 'AUXILIAR_TAREAS', TRUE
WHERE NOT EXISTS (
  SELECT 1
  FROM equipos
  WHERE UPPER(nombre) = 'PC-GENERICA'
);

UPDATE tareas_tecnicas
SET equipo_id = (
  SELECT id
  FROM equipos
  WHERE UPPER(nombre) = 'PC-GENERICA'
  LIMIT 1
)
WHERE equipo_id IS NULL;

CREATE INDEX idx_tareas_tecnicas_solicitante ON tareas_tecnicas (solicitante_username);
