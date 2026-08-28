# Plan De Trabajo

Plan inicial para construir Inventario Modular Java desde cero.

## Fase 0: Preparacion del entorno

Estado: en curso.

Tareas:

- Instalar JDK 21 LTS.
- Instalar Maven.
- Verificar Java y Maven en PATH.
- Verificar MySQL local.
- Crear base local `inventario_modular`.

Resultado esperado:

- La maquina puede compilar y ejecutar proyectos Spring Boot modernos.

## Fase 1: Proyecto base

Tareas:

- Crear carpeta limpia `inventario-modular`.
- Crear proyecto Spring Boot.
- Configurar estructura de paquetes.
- Configurar perfiles `local`, `test` y futuro `prod`.
- Configurar conexion MySQL local.
- Configurar Flyway.

Resultado esperado:

- `mvn test` funciona.
- `mvn spring-boot:run` inicia localmente.
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

Instalar Maven con:

```powershell
choco install maven -y
```

Luego verificar:

```powershell
java -version
mvn -version
```

Si ambos comandos funcionan, crear la base local `inventario_modular` y generar el
proyecto Spring Boot limpio.
