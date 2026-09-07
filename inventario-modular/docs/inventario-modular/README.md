# Inventario Modular

Documentacion inicial del nuevo sistema de inventario en Java para el Departamento de
Informatica del Centro Judicial San Pedro.

## Objetivo

Crear un sistema nuevo, limpio y modular en Java, sin arrastrar codigo heredado del
inventario original ni del experimento Inventario Next. El sistema debe conservar la
logica operativa que si funciona hoy, pero con una arquitectura preparada para crecer por
modulos y para exponer una futura app movil sin rehacer el backend.

## Decision principal

Inventario Modular se disena como una aplicacion **API-first**:

- Backend Java con Spring Boot.
- Base de datos MySQL nueva para desarrollo/laboratorio: `inventario_modular`.
- En Windows puede usarse MySQL local; en el trabajo la base esta en el servidor separado
  `10.15.0.62`.
- Autenticacion contra Active Directory.
- Autorizacion propia en MySQL mediante usuarios, roles, permisos y modulos.
- Cliente web administrativo solo cuando sea necesario.
- Futura app movil consumiendo la misma API.

## Documentos

- [Instalacion desde cero](./instalacion-desde-cero.md)
- [Bitacora del proyecto](./bitacora-del-proyecto.md)
- [Requerimientos del sistema](./requerimientos-sistema.md)
- [Plan de trabajo](./plan-de-trabajo.md)
- [Versionado Git](./versionado-git.md)
- [CI/CD](./ci-cd.md)
- [Cierre de jornada Windows](./cierre-jornada-windows.md)
- [Runbook Ubuntu por PuTTY](./runbook-manana-ubuntu-putty.md)
- [Modo local Windows sin dominio](./modo-local-windows-sin-dominio.md)
- [Incidente login local repetido](./incidente-login-local-repetido.md)
- [Usuarios locales y Active Directory](./usuarios-locales-y-active-directory.md)
- [Modulo Equipos](./modulo-equipos.md)
- [Modulo Componentes y Gemelo Digital](./modulo-componentes-gemelo-digital.md)
- [Stock, ordenes de armado y comparacion](./stock-ordenes-armado-y-comparacion.md)
- [Auditoria transversal](./auditoria-transversal.md)
- [Modulo Actas](./modulo-actas.md)
- [Modulo Ubicaciones](./modulo-ubicaciones.md)
- [Modulo Tareas Tecnicas](./modulo-tareas-tecnicas.md)
- [Modulo Muebles](./modulo-muebles.md)
- [Modulo Patrimonio](./modulo-patrimonio.md)
- [Modulo Reportes](./modulo-reportes.md)
- [Base de datos local Windows](./base-datos-local-windows.md)
- [Seguridad modular inicial](./seguridad-modular-inicial.md)
- [Decision tecnica API-first y app movil](../decisions/ADR-002-inventario-modular-api-first.md)
- [Decision sobre inventario viejo como referencia funcional](../decisions/ADR-003-inventario-viejo-como-referencia-funcional.md)
- [Decision sobre modo local sin dominio](../decisions/ADR-005-modo-local-sin-dominio.md)
- [Decision sobre autorizacion modular inicial](../decisions/ADR-006-autorizacion-modular-inicial.md)
- [Decision sobre identidades, autenticacion y autorizacion](../decisions/ADR-007-identidades-autenticacion-autorizacion.md)
- [Decision sobre componentes y gemelo digital](../decisions/ADR-008-componentes-y-gemelo-digital-del-equipo.md)

## Alcance inicial

El primer entregable no es actas, muebles ni stock. El primer entregable es el nucleo de
seguridad y modularidad:

1. Login validado contra Active Directory.
2. Usuarios internos vinculados a usuarios de dominio.
3. Roles y permisos administrables.
4. Modulos activables por usuario/rol.
5. API protegida que rechaza accesos sin permiso.
6. Panel minimo para administrar usuarios, roles, permisos y modulos.

Estado actual: ya existe una primera implementacion de usuarios, roles, permisos,
modulos, seed inicial, endpoints de usuario actual, API administrativa para usuarios,
alta local con clave BCrypt, listado/autorizacion inicial de usuarios AD, modulo
`EQUIPOS`, modulo `COMPONENTES`, primera base de `STOCK`, `ORDENES_ARMADO` y comparacion
del gemelo digital, primera auditoria transversal de cambios operativos, dashboard de
diferencias y primeras versiones de `TAREAS`, `MUEBLES`, `PATRIMONIO`, `REPORTES`,
`ACTAS` y `UBICACIONES`.

El modo local de casa ya permite login repetido con `admin.local` sin depender de Active
Directory. El incidente y su solucion quedaron documentados en
[Incidente login local repetido](./incidente-login-local-repetido.md).

La primera pantalla visual de seguridad esta disponible en:

```text
/admin/usuarios
```

Permite listar identidades autorizadas, crear usuarios locales y autorizar cuentas `AD`
sin cargar password porque Active Directory valida la clave. Para cuentas `LOCAL`, la
pantalla permite cargar una clave propia y el sistema guarda solo hash BCrypt en
`credenciales_locales`. La edicion de roles existentes, activar/desactivar usuarios,
busqueda paginada de AD y la matriz completa rol-modulo-permiso quedan como continuacion
de seguridad.

La primera pantalla funcional esta disponible en:

```text
/admin/equipos
```

Permite listar equipos, buscar por nombre/usuario/fuero y consumir la misma base que la
API `/api/v1/equipos`.

## Principio rector

Active Directory confirma identidad. Inventario Modular decide autorizacion.

El sistema no guarda claves del dominio.

## Relacion con el inventario viejo

El inventario viejo se toma como **referencia funcional**, no como base tecnica.

Esto significa que el nuevo sistema Java debe estudiar y respetar los flujos que ya
funcionan en la operacion diaria, por ejemplo equipos, actas, OVMelos, patrimonio, stock
y reportes usados realmente. Pero no debe copiar codigo heredado, estructura desordenada
ni decisiones tecnicas que dificulten mantener el sistema.

La migracion se hara por modulos: primero se entiende como trabaja hoy el modulo viejo,
luego se redefine en Java con Spring Boot, permisos, API, migraciones y pruebas.

## Topologia de base de datos

Para estudiar y desarrollar en casa se puede usar MySQL local. Para la instalacion de
laboratorio en el trabajo, el servidor Ubuntu de la aplicacion y el servidor MySQL son
distintos:

```text
Servidor Ubuntu de aplicacion -> 10.15.0.62:3306 -> inventario_modular
```

Por eso el runbook de Ubuntu configura `INVENTARIO_DB_URL` apuntando a `10.15.0.62`, no
a `127.0.0.1`.

## Modo local de casa

Cuando se trabaja desde casa no hay acceso al dominio real ni al servidor MySQL del
trabajo. Para ese caso, el perfil `local` usa:

- MySQL local en `127.0.0.1:3306`.
- Base `inventario_modular`.
- Login local simulado con `inventario.local-auth.*`.
- LDAP apagado con `inventario.ldap.enabled=false`.

Ese modo no reemplaza la autenticacion real de Active Directory. Solo permite estudiar,
desarrollar y probar pantallas en Windows.

Si MySQL local todavia no esta creado, usar el perfil `casa`:

```powershell
mvn spring-boot:run "-Dspring-boot.run.profiles=casa"
```

Ese perfil usa una base H2 local en `.local-data/`, ignorada por git. La clave local de
desarrollo es `AdminLocal123`.
