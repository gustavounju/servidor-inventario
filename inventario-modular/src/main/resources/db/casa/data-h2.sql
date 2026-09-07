MERGE INTO permisos (id, codigo, nombre, descripcion) KEY(codigo) VALUES
  (1, 'VER', 'Ver', 'Permite consultar informacion del modulo.'),
  (2, 'CREAR', 'Crear', 'Permite crear registros nuevos.'),
  (3, 'EDITAR', 'Editar', 'Permite modificar registros existentes.'),
  (4, 'ELIMINAR', 'Eliminar', 'Permite eliminar o desactivar registros.'),
  (5, 'EXPORTAR', 'Exportar', 'Permite generar salidas o reportes del modulo.'),
  (6, 'ADMINISTRAR', 'Administrar', 'Permite administrar configuracion del modulo.');

MERGE INTO modulos (id, codigo, nombre, descripcion, orden, activo) KEY(codigo) VALUES
  (1, 'EQUIPOS', 'Equipos', 'Inventario tecnico de computadoras y dispositivos principales.', 10, TRUE),
  (2, 'ACTAS', 'Actas', 'Gestion de actas y constancias asociadas al inventario.', 20, TRUE),
  (3, 'MUEBLES', 'Muebles', 'Gestion fisica de muebles y bienes de oficina.', 30, TRUE),
  (4, 'PATRIMONIO', 'Patrimonio', 'Control patrimonial institucional y reportes administrativos.', 40, TRUE),
  (5, 'STOCK', 'Stock', 'Existencias, movimientos y disponibilidad de insumos.', 50, TRUE),
  (10, 'ORDENES_ARMADO', 'Ordenes de Armado', 'Planificacion de equipos nuevos o mejoras con componentes esperados.', 55, TRUE),
  (6, 'COMPONENTES', 'Componentes', 'Partes, repuestos y componentes asociados a equipos.', 60, TRUE),
  (7, 'USUARIOS', 'Usuarios', 'Administracion de usuarios, roles, permisos y modulos.', 70, TRUE),
  (8, 'REPORTES', 'Reportes', 'Consultas, listados y exportaciones del sistema.', 80, TRUE),
  (9, 'TAREAS', 'Tareas', 'Seguimiento de tareas tecnicas y operativas.', 90, TRUE),
  (11, 'AUDITORIA', 'Auditoria', 'Eventos de cambios relevantes del sistema.', 95, TRUE),
  (12, 'UBICACIONES', 'Ubicaciones', 'Oficinas, depositos, salas y racks vinculados al inventario.', 25, TRUE);

MERGE INTO roles (id, codigo, nombre, descripcion, activo) KEY(codigo) VALUES
  (1, 'ADMINISTRADOR', 'Administrador', 'Acceso total a los modulos del sistema.', TRUE),
  (2, 'TECNICO', 'Tecnico', 'Acceso operativo a modulos tecnicos.', TRUE),
  (3, 'PATRIMONIO', 'Patrimonio', 'Acceso a gestion patrimonial, muebles y reportes.', TRUE),
  (4, 'LECTOR', 'Lector', 'Acceso de solo consulta.', TRUE),
  (5, 'PERSONALIZADO', 'Personalizado', 'Rol para combinaciones manuales de permisos.', TRUE);

MERGE INTO usuarios (id, username, nombre_visible, fuero, origen, activo) KEY(username) VALUES
  (1, 'admin.local', 'Administrador Local', 'Desarrollo local', 'LOCAL', TRUE);

MERGE INTO usuario_roles (usuario_id, rol_id) KEY(usuario_id, rol_id)
SELECT u.id, r.id
FROM usuarios u
JOIN roles r ON r.codigo = 'ADMINISTRADOR'
WHERE u.username = 'admin.local';

MERGE INTO rol_modulo_permisos (rol_id, modulo_id, permiso_id) KEY(rol_id, modulo_id, permiso_id)
SELECT r.id, m.id, p.id
FROM roles r
CROSS JOIN modulos m
CROSS JOIN permisos p
WHERE r.codigo = 'ADMINISTRADOR';

MERGE INTO equipos (
  id, nombre, ultimo_usuario, fuero, ip, sistema_operativo, procesador, ram_mb,
  ram_detalles, ram_seriales, discos_modelos, discos_seriales, motherboard_modelo,
  motherboard_serial, monitores, teclado, mouse, impresora, monitoreo, activo) KEY(nombre) VALUES
  (1, 'PC-INF-001', 'gmurad', 'Informatica', '10.15.2.10', 'Windows 11 Pro', 'Intel Core i5', 16384,
   '2x8GB DDR4', 'RAMSN-001 | RAMSN-002', 'KINGSTON SA400', 'DISK-001', 'Dell 0ABC',
   'MB-001', 'Dell 22 SN MON-001', 'Logitech Keyboard', 'Logitech Mouse', 'HP LaserJet', 'REPORTADO', TRUE),
  (2, 'PC-MESA-002', 'mesa.entrada', 'Mesa de ayuda', '10.15.2.11', 'Windows 10 Pro', 'Intel Core i3', 8192,
   NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, 'REPORTADO', TRUE);

MERGE INTO componentes (id, equipo_id, tipo, origen, estado_comparacion, descripcion, marca, modelo, serial, capacidad, ubicacion, observaciones, activo) KEY(id) VALUES
  (1, 1, 'RAM', 'SCRIPT', 'COINCIDE', 'Modulo RAM instalado', 'Kingston', 'DDR4 2666', 'RAMSN-001', '8GB', 'Slot 1', 'Detectado por script', TRUE),
  (2, 1, 'DISCO', 'ORDEN_ARMADO', 'ESPERADO', 'Disco esperado por orden de armado', 'Kingston', 'SA400', 'DISK-001', '480GB', 'SATA 1', 'Debe coincidir con el reporte', TRUE);

MERGE INTO stock_componentes (id, tipo, estado, descripcion, marca, modelo, serial, capacidad, ubicacion, observaciones, activo) KEY(id) VALUES
  (1, 'RAM', 'DISPONIBLE', 'Memoria RAM nueva para armado', 'Kingston', 'DDR4 2666', 'STOCK-RAM-001', '8GB', 'Deposito Informatica', 'Disponible para orden de armado', TRUE);

MERGE INTO tareas_tecnicas (id, equipo_id, titulo, descripcion, estado, prioridad, responsable) KEY(id) VALUES
  (1, 1, 'Revisar mantenimiento preventivo', 'Tarea de ejemplo para validar el modulo desde casa.', 'PENDIENTE', 'MEDIA', 'admin.local');

MERGE INTO muebles (id, codigo, tipo, descripcion, ubicacion, fuero, responsable, estado, observaciones, activo) KEY(codigo) VALUES
  (1, 'MUE-SEED-001', 'SILLA', 'Silla operativa de Informatica', 'Informatica', 'Informatica', 'admin.local', 'ACTIVO', 'Seed local casa', TRUE);

MERGE INTO bienes_patrimoniales (id, numero_patrimonial, categoria, descripcion, ubicacion, fuero, custodio, estado, equipo_id, observaciones, activo) KEY(numero_patrimonial) VALUES
  (1, 'PAT-SEED-001', 'PC', 'PC patrimonial seed', 'Informatica', 'Informatica', 'admin.local', 'EN_USO', 1, 'Seed local casa', TRUE);

MERGE INTO actas (id, numero, tipo, equipo_id, fecha_emision, destinatario, responsable_entrega, responsable_recepcion, detalle, estado, observaciones, activo) KEY(numero) VALUES
  (1, 'ACT-SEED-001', 'ENTREGA', 1, DATE '2026-09-01', 'Mesa de Entradas', 'admin.local', 'mesa.entrada', 'Entrega inicial de equipo seed.', 'EMITIDA', 'Seed local casa', TRUE);

MERGE INTO ubicaciones (id, codigo, nombre, tipo, fuero, responsable, edificio, piso, estado, observaciones, activo) KEY(codigo) VALUES
  (1, 'UBI-SEED-001', 'Oficina Informatica', 'OFICINA', 'Informatica', 'admin.local', 'Centro Judicial San Pedro', 'PB', 'ACTIVA', 'Seed local casa', TRUE);
