CREATE TABLE tareas_tecnicas_comentarios (
  id BIGINT NOT NULL AUTO_INCREMENT,
  tarea_id BIGINT NOT NULL,
  autor VARCHAR(120) NOT NULL,
  comentario VARCHAR(1000) NOT NULL,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT fk_tareas_comentarios_tarea FOREIGN KEY (tarea_id) REFERENCES tareas_tecnicas (id),
  INDEX idx_tareas_comentarios_tarea (tarea_id, creado_en)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
