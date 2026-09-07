CREATE TABLE usuarios (
  id BIGINT NOT NULL AUTO_INCREMENT,
  username VARCHAR(120) NOT NULL,
  nombre_visible VARCHAR(180) NOT NULL,
  fuero VARCHAR(120) NOT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  actualizado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  CONSTRAINT uk_usuarios_username UNIQUE (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE roles (
  id BIGINT NOT NULL AUTO_INCREMENT,
  codigo VARCHAR(60) NOT NULL,
  nombre VARCHAR(120) NOT NULL,
  descripcion VARCHAR(255) NOT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (id),
  CONSTRAINT uk_roles_codigo UNIQUE (codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE modulos (
  id BIGINT NOT NULL AUTO_INCREMENT,
  codigo VARCHAR(60) NOT NULL,
  nombre VARCHAR(120) NOT NULL,
  descripcion VARCHAR(255) NOT NULL,
  orden INT NOT NULL,
  activo BOOLEAN NOT NULL DEFAULT TRUE,
  PRIMARY KEY (id),
  CONSTRAINT uk_modulos_codigo UNIQUE (codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE permisos (
  id BIGINT NOT NULL AUTO_INCREMENT,
  codigo VARCHAR(60) NOT NULL,
  nombre VARCHAR(120) NOT NULL,
  descripcion VARCHAR(255) NOT NULL,
  PRIMARY KEY (id),
  CONSTRAINT uk_permisos_codigo UNIQUE (codigo)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE usuario_roles (
  usuario_id BIGINT NOT NULL,
  rol_id BIGINT NOT NULL,
  PRIMARY KEY (usuario_id, rol_id),
  CONSTRAINT fk_usuario_roles_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
  CONSTRAINT fk_usuario_roles_rol FOREIGN KEY (rol_id) REFERENCES roles (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE rol_modulo_permisos (
  rol_id BIGINT NOT NULL,
  modulo_id BIGINT NOT NULL,
  permiso_id BIGINT NOT NULL,
  PRIMARY KEY (rol_id, modulo_id, permiso_id),
  CONSTRAINT fk_rol_modulo_permisos_rol FOREIGN KEY (rol_id) REFERENCES roles (id),
  CONSTRAINT fk_rol_modulo_permisos_modulo FOREIGN KEY (modulo_id) REFERENCES modulos (id),
  CONSTRAINT fk_rol_modulo_permisos_permiso FOREIGN KEY (permiso_id) REFERENCES permisos (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO permisos (codigo, nombre, descripcion) VALUES
  ('VER', 'Ver', 'Permite consultar informacion del modulo.'),
  ('CREAR', 'Crear', 'Permite crear registros nuevos.'),
  ('EDITAR', 'Editar', 'Permite modificar registros existentes.'),
  ('ELIMINAR', 'Eliminar', 'Permite eliminar o desactivar registros.'),
  ('EXPORTAR', 'Exportar', 'Permite generar salidas o reportes del modulo.'),
  ('ADMINISTRAR', 'Administrar', 'Permite administrar configuracion del modulo.');

INSERT INTO modulos (codigo, nombre, descripcion, orden) VALUES
  ('EQUIPOS', 'Equipos', 'Inventario tecnico de computadoras y dispositivos principales.', 10),
  ('ACTAS', 'Actas', 'Gestion de actas y constancias asociadas al inventario.', 20),
  ('MUEBLES', 'Muebles', 'Gestion fisica de muebles y bienes de oficina.', 30),
  ('PATRIMONIO', 'Patrimonio', 'Control patrimonial institucional y reportes administrativos.', 40),
  ('STOCK', 'Stock', 'Existencias, movimientos y disponibilidad de insumos.', 50),
  ('COMPONENTES', 'Componentes', 'Partes, repuestos y componentes asociados a equipos.', 60),
  ('USUARIOS', 'Usuarios', 'Administracion de usuarios, roles, permisos y modulos.', 70),
  ('REPORTES', 'Reportes', 'Consultas, listados y exportaciones del sistema.', 80),
  ('TAREAS', 'Tareas', 'Seguimiento de tareas tecnicas y operativas.', 90);

INSERT INTO roles (codigo, nombre, descripcion) VALUES
  ('ADMINISTRADOR', 'Administrador', 'Acceso total a los modulos del sistema.'),
  ('TECNICO', 'Tecnico', 'Acceso operativo a modulos tecnicos.'),
  ('PATRIMONIO', 'Patrimonio', 'Acceso a gestion patrimonial, muebles y reportes.'),
  ('LECTOR', 'Lector', 'Acceso de solo consulta.'),
  ('PERSONALIZADO', 'Personalizado', 'Rol para combinaciones manuales de permisos.');

INSERT INTO rol_modulo_permisos (rol_id, modulo_id, permiso_id)
SELECT r.id, m.id, p.id
FROM roles r
CROSS JOIN modulos m
CROSS JOIN permisos p
WHERE r.codigo = 'ADMINISTRADOR';

INSERT INTO usuarios (username, nombre_visible, fuero)
VALUES ('admin.local', 'Administrador Local', 'Desarrollo local');

INSERT INTO usuario_roles (usuario_id, rol_id)
SELECT u.id, r.id
FROM usuarios u
JOIN roles r ON r.codigo = 'ADMINISTRADOR'
WHERE u.username = 'admin.local';
