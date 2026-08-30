# Plan De Trabajo

Plan inicial para construir Inventario Modular Java desde cero.

## Fase 0: Preparacion del entorno

Estado: parcialmente completada.

Tareas:

- Instalar JDK 21 LTS. Completado: Java 21 esta en PATH.
- Instalar Maven. Pendiente global, pero el proyecto ya incluye Maven Wrapper (`mvnw.cmd`).
- Verificar Java y Maven en PATH.
- Verificar MySQL local.
- Crear base local `inventario_modular`.

Resultado esperado:

- La maquina puede compilar y ejecutar proyectos Spring Boot modernos.

## Fase 1: Proyecto base

Estado: primer corte creado.

Tareas:

- Crear carpeta limpia `inventario-modular`. Completado.
- Crear proyecto Spring Boot. Completado con Spring Boot 4.0.0 y Java 21.
- Configurar estructura de paquetes. Completado con paquete base
  `ar.gob.justicia.sanpedro.inventario`.
- Configurar perfiles `local`, `test` y futuro `prod`.
- Configurar conexion MySQL local. Pendiente.
- Configurar Flyway. Pendiente; dependencia agregada, auto-config temporalmente excluida
  hasta crear la base y migraciones.
- Configurar puerto local `8081` y healthcheck `/api/v1/health`. Completado.

Resultado esperado:

- `.\mvnw.cmd test` funciona.
- `.\mvnw.cmd spring-boot:run` inicia localmente.
- No hay dependencia con produccion.

## Fase 2: Modelo de seguridad modular

Tareas:

- Crear tablas de usuarios internos.
- Crear tablas de roles.
- Crear tablas de permisos.
- Crear tablas de modulos.
- Crear relacion usuario-rol.
- Crear relacion rol-permiso-modulo.
- Crear seed inicial de modulos.

Resultado esperado:

- El sistema puede representar que modulos ve cada usuario y que acciones puede realizar.

## Fase 3: Active Directory

Tareas:

- Configurar LDAP por variables locales.
- Validar credenciales contra AD.
- Manejar error de AD no disponible.
- No guardar claves.
- No loguear claves.

Resultado esperado:

- La identidad se valida contra dominio y la autorizacion se resuelve en MySQL.

## Fase 4: API-first

Tareas:

- Crear API versionada `/api/v1`.
- Crear endpoint de login.
- Crear endpoint de usuario actual.
- Crear endpoint de modulos permitidos.
- Crear respuestas 401 y 403 consistentes.

Resultado esperado:

- Una futura app movil puede consumir el nucleo sin depender de pantallas HTML.

## Fase 5: Panel administrativo minimo

Tareas:

- Crear login visual.
- Crear pantalla de usuarios.
- Crear pantalla de roles.
- Crear pantalla de permisos por modulo.
- Crear pantalla de modulos activables.

Resultado esperado:

- Un administrador puede dar acceso real a usuarios de dominio.

## Fase 6: Primer modulo funcional

Candidato recomendado: ACTAS o MUEBLES.

La decision queda pendiente hasta terminar seguridad y permisos.

## Fase 7: Migracion progresiva

Tareas futuras:

- Analizar tablas del inventario original.
- Identificar logica funcional que debe copiarse.
- Migrar por modulo.
- Mantener sistema original funcionando hasta validar reemplazo.

## Riesgos conocidos

- Configuracion real de Active Directory incompleta o cambiante.
- Diferencias entre red de casa y red del trabajo.
- Permisos institucionales para consultar AD.
- Instaladores bloqueados por politicas del trabajo.
- Intentar migrar demasiados modulos antes de cerrar seguridad.

## Proxima accion recomendada

Crear la base local `inventario_modular`, agregar la configuracion local de datasource con
placeholders y crear las primeras migraciones Flyway para usuarios, roles, permisos y
modulos.
