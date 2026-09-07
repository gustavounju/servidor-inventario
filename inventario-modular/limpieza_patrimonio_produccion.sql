-- Script de Limpieza para Producción (Módulo Patrimonio)
-- Ejecutar en la base de datos de producción para eliminar las tablas asociadas.

-- 1. Eliminar la tabla principal de bienes patrimoniales.
-- Si hay dependencias de claves foráneas con otras tablas (como auditoría), 
-- asegúrate de verificar o eliminar esos registros en cascada si es necesario.
DROP TABLE IF EXISTS bien_patrimonial;

-- 2. Limpieza de registros de auditoría (Opcional)
-- Si deseas limpiar los logs generados por este módulo para no dejar registros huérfanos:
-- DELETE FROM auditoria WHERE tipo_entidad = 'BienPatrimonial';
-- DELETE FROM auditoria WHERE modulo = 'PATRIMONIO';

-- Nota: Si usas Hibernate auto-ddl = update, la tabla no se volverá a crear 
-- porque ya eliminamos las entidades Java en la nueva versión.
