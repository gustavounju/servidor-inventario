# Seguridad Modular Inicial

Este documento explica la primera capa de autorizacion local de Inventario Modular.

## Idea principal

El sistema separa dos responsabilidades:

```text
Active Directory valida identidad.
Inventario Modular decide autorizacion, roles, permisos y modulos.
```

Esto permite que un usuario use su cuenta real de dominio en el trabajo, pero que el
sistema Java decida si ese usuario puede ver `EQUIPOS`, `MUEBLES`, `PATRIMONIO`,
`COMPONENTES`, `USUARIOS`, `REPORTES` u otros modulos.

En casa, donde no hay dominio real, el perfil local simula el login con `admin.local`.
Esa simulacion no reemplaza Active Directory; solo permite desarrollar y estudiar desde
Windows.

## Migracion de base de datos

La primera migracion Flyway esta en:

```text
src/main/resources/db/migration/V1__seguridad_modular.sql
```

Crea estas tablas:

```text
usuarios
roles
modulos
permisos
usuario_roles
rol_modulo_permisos
```

La relacion queda asi:

```text
usuario -> roles -> modulos -> permisos
```

Ejemplo:

```text
admin.local
  -> ADMINISTRADOR
     -> todos los modulos
        -> VER, CREAR, EDITAR, ELIMINAR, EXPORTAR, ADMINISTRAR
```

## Modulos iniciales

La migracion deja cargados estos modulos base:

- `EQUIPOS`
- `ACTAS`
- `MUEBLES`
- `PATRIMONIO`
- `STOCK`
- `COMPONENTES`
- `USUARIOS`
- `REPORTES`
- `TAREAS`

Estos nombres son el punto de partida. Se pueden apagar o prender por permisos asignados
a roles y usuarios.

## Endpoints API

Se agregaron endpoints pensados para API-first y futura app movil:

```text
GET /api/v1/me
GET /api/v1/me/modulos
GET /api/v1/usuarios
POST /api/v1/usuarios
GET /api/v1/usuarios/dominio
POST /api/v1/usuarios/dominio
GET /api/v1/roles
GET /api/v1/equipos
GET /api/v1/equipos/{id}
POST /api/v1/equipos/inventario
```

`GET /api/v1/me` devuelve:

- usuario autenticado;
- nombre visible;
- fuero;
- si esta autorizado localmente;
- modulos habilitados;
- permisos por modulo.

`GET /api/v1/me/modulos` devuelve solo los modulos que el usuario puede ver.

Estos endpoints son importantes porque la futura app movil podra consumir la misma
informacion sin depender de la pantalla web.

### Administracion inicial de usuarios por API

Los endpoints de administracion requieren que el usuario autenticado tenga permiso
`ADMINISTRAR` sobre el modulo `USUARIOS`.

`GET /api/v1/usuarios` devuelve los usuarios cargados localmente en Inventario Modular:

```json
{
  "usuarios": [
    {
      "id": 1,
      "username": "admin.local",
      "nombreVisible": "Administrador Local",
      "fuero": "Desarrollo local",
      "activo": true,
      "roles": ["ADMINISTRADOR"]
    }
  ]
}
```

`POST /api/v1/usuarios` crea un usuario local autorizado. Recibe una clave local, pero
solo guarda hash BCrypt en `credenciales_locales`.

Ejemplo:

```json
{
  "username": "chofer.local",
  "nombreVisible": "Chofer de Guardia",
  "fuero": "Informatica",
  "password": "ClaveTemporal123",
  "activo": true,
  "roles": ["ADMINISTRADOR"]
}
```

`GET /api/v1/usuarios/dominio` lista usuarios de Active Directory si LDAP esta habilitado
y configurado. En modo local devuelve `disponible=false`.

`POST /api/v1/usuarios/dominio` autoriza localmente una identidad AD existente, sin
recibir ni guardar clave de dominio:

```json
{
  "username": "gmurad",
  "nombreVisible": "Gustavo Elias Murad",
  "fuero": "Informatica",
  "activo": true,
  "roles": ["ADMINISTRADOR"]
}
```

`GET /api/v1/roles` devuelve los roles disponibles para que una pantalla futura pueda
mostrarlos como opciones, sin tener codigos fijos escritos a mano.

Respuestas esperadas:

- `201 Created`: usuario creado correctamente.
- `403 Forbidden`: el usuario autenticado no puede administrar usuarios.
- `409 Conflict`: el usuario ya existe.
- `422 Unprocessable Content`: algun rol solicitado no existe.

### Modulo Equipos por API

Los endpoints de equipos requieren permisos del modulo `EQUIPOS`:

- `GET /api/v1/equipos`: requiere `VER`.
- `GET /api/v1/equipos/{id}`: requiere `VER`.
- `POST /api/v1/equipos/inventario`: requiere `EDITAR`.

El listado acepta `q`, `page` y `pageSize`. La busqueda `q` filtra por nombre de equipo,
ultimo usuario o fuero. El endpoint de inventario crea o actualiza por `nombre`, normaliza
el nombre a mayusculas y registra el ultimo reporte.

## Pantalla administrativa actual

La pantalla `/admin` muestra:

- usuario autenticado;
- cuenta;
- fuero;
- estado `Autorizado` o `Pendiente de autorizacion`;
- modulos habilitados;
- permisos de cada modulo;
- atributos de identidad de AD o del modo local.

La pantalla `/admin/usuarios` ya permite:

- listar usuarios registrados;
- ver estado activo/inactivo;
- ver roles asignados;
- crear usuarios locales con clave hasheada;
- listar usuarios de dominio cuando LDAP esta disponible;
- autorizar usuarios AD con rol inicial, sin pedir clave de dominio.

Para cuentas de Active Directory, la clave la valida el dominio durante el login.
Inventario Modular solo guarda autorizacion local: roles, permisos y modulos. Para cuentas
locales, la pantalla puede cargar una clave propia y el sistema guarda solamente hash
BCrypt en `credenciales_locales`.

Todavia falta busqueda filtrada/paginada de Active Directory, editar roles existentes,
activar/desactivar usuarios desde pantalla y mostrar la matriz completa de
modulos/permisos por rol.

La pantalla `/admin/equipos` ya permite:

- listar equipos;
- buscar por nombre, ultimo usuario o fuero;
- ver estado de monitoreo;
- acceder solo si el usuario tiene `EQUIPOS:VER`.

## Comportamiento actual

Si el usuario existe en `usuarios` y esta activo:

```text
autorizado = true
```

El sistema busca sus roles y devuelve los modulos/permisos asociados.

Si el usuario inicia sesion correctamente por AD pero todavia no existe en `usuarios`:

```text
autorizado = false
```

El sistema mantiene la identidad visible, pero no devuelve modulos. Por ahora esto se usa
para no bloquear accidentalmente el acceso mientras se termina la administracion inicial
de usuarios.

## Lo que falta

Los siguientes pasos son:

- bloquear acceso a modulos cuando `autorizado = false`;
- agregar busqueda filtrada/paginada de Active Directory;
- permitir editar roles de usuarios existentes;
- permitir activar/desactivar usuarios existentes;
- permitir cambiar clave de usuarios locales;
- auditar altas, cambios de clave y desactivaciones;
- permitir activar/desactivar modulos;
- mostrar matriz rol-modulo-permiso;
- seguir aplicando permisos en cada modulo funcional nuevo;
- dejar tests de acceso permitido y denegado por modulo.

## Pruebas

Las pruebas relacionadas estan en:

```text
src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/CurrentUserControllerTests.java
src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/UsuarioAdminControllerTests.java
src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/EquipoControllerTests.java
src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/EquipoPageControllerTests.java
src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/security/LocalAuthenticationConfigTests.java
src/test/resources/sql/seguridad-modular-test.sql
src/test/resources/sql/limpiar-seguridad-modular-test.sql
```

Comando de verificacion:

```powershell
mvn test
```

Salida esperada:

```text
BUILD SUCCESS
```
