CREATE TABLE IF NOT EXISTS tareas_aviso_secuencia (
  id INTEGER PRIMARY KEY,
  ultimo_id BIGINT NOT NULL
);
INSERT INTO tareas_aviso_secuencia (id, ultimo_id)
SELECT 1, 0 WHERE NOT EXISTS (SELECT 1 FROM tareas_aviso_secuencia WHERE id = 1);

CREATE TABLE IF NOT EXISTS tareas_avisos (
  id BIGINT PRIMARY KEY,
  tarea_id BIGINT NOT NULL,
  titulo VARCHAR(180) NOT NULL,
  autor VARCHAR(120),
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
