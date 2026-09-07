# ADR-007: Separar Identidades, Autenticacion y Autorizacion

## Estado

Aceptado

## Fecha

2026-08-29

## Contexto

Inventario Modular debe funcionar en dos escenarios:

- En produccion/trabajo, con usuarios validados contra Active Directory.
- En casa/desarrollo, sin dominio disponible, usando una simulacion local.

Durante la primera pantalla `/admin/usuarios` aparecio una duda importante: al crear un
usuario desde el panel no hay campo para cargar password.

Esa duda muestra que hay que separar tres conceptos:

```text
Identidad       -> quien es la persona o cuenta: gmurad, admin.local, tecnico.local.
Autenticacion   -> quien valida la clave: Active Directory o proveedor local.
Autorizacion    -> que puede ver/hacer en Inventario Modular: roles, permisos, modulos.
```

## Decision

La tabla `usuarios` del sistema no representa necesariamente usuarios locales con clave.
Representa identidades autorizadas dentro de Inventario Modular.

Para usuarios de Active Directory:

- La clave se ingresa en `/login`.
- Spring Security valida usuario y clave contra Active Directory.
- Inventario Modular no guarda la clave.
- Inventario Modular usa MySQL solo para decidir roles, permisos y modulos.

Para usuarios locales reales:

- Se implementan como un proveedor de autenticacion separado.
- La clave no debe guardarse en texto plano.
- La base solo puede guardar un hash seguro de la clave.
- El alta o cambio de clave debe quedar auditado.
- En produccion debe estar controlado por configuracion para no abrir accesos por error.

## Consecuencia en la pantalla `/admin/usuarios`

La pantalla debe separar dos acciones distintas.

Crear usuario local:

```text
Crear usuario local
-> username local
-> clave local
-> nombre visible
-> fuero/area
-> estado
-> rol inicial
```

Autorizar usuario AD:

```text
Buscar/listar usuario de Active Directory
-> seleccionar cuenta existente
-> guardar autorizacion local
-> asignar roles, permisos y modulos
-> no pedir ni guardar clave de dominio
```

Por eso el alta directa debe crear solamente usuarios `LOCAL`. Crear manualmente un
usuario con origen `AD` desde el formulario es conceptualmente incorrecto: Inventario
Modular no crea cuentas en el dominio.

## Listado de usuarios de Active Directory

En produccion, la administracion ideal no deberia obligar a escribir el usuario a mano.
Deberia permitir buscar/listar usuarios de Active Directory y luego asignarles roles y
modulos locales.

Flujo deseado:

```text
Administrador abre /admin/usuarios
-> busca usuario en Active Directory
-> selecciona la cuenta correcta
-> Inventario Modular crea o actualiza la autorizacion local
-> asigna rol/modulos
```

Para eso se necesita una integracion LDAP de lectura, distinta del login:

- login LDAP: valida usuario y clave;
- busqueda LDAP: lista o busca usuarios del dominio para administracion.

Esa busqueda queda implementada como lectura opcional. Puede requerir una cuenta tecnica
de lectura configurada por variables de entorno en el servidor, nunca guardada en git.
Cuando LDAP esta apagado, la pantalla muestra la seccion de dominio como no disponible.

## Alternativas consideradas

### Guardar password en `usuarios`

Rechazado para usuarios AD. Seria inseguro e innecesario porque el dominio ya valida la
clave.

### Usar solo usuarios locales

Rechazado como modelo principal. En el trabajo ya existe Active Directory y debe seguir
siendo la fuente de autenticacion.

### Mezclar AD y local en la misma tabla sin distinguir origen

Rechazado como modelo definitivo. Sirve para el primer prototipo, pero para produccion
conviene agregar un campo de origen o una tabla de credenciales locales separada.

## Implementacion inicial

La primera implementacion agrega:

```text
usuarios
-> identidad autorizada
-> username
-> origen: AD o LOCAL
-> activo
-> roles

credenciales_locales
-> solo para origen LOCAL
-> password_hash
-> requiere_cambio_clave
-> actualizado_en
```

La autenticacion local de base se habilita con:

```text
inventario.local-db-auth.enabled=true
```

La lectura de usuarios de dominio se habilita con:

```text
inventario.ldap.enabled=true
inventario.ldap.read-only-user-dn=...
inventario.ldap.read-only-password=...
inventario.ldap.user-search-filter=(&(objectClass=user)(!(objectClass=computer)))
```

## Proxima decision tecnica

Definir la politica operativa de produccion:

- si los usuarios locales estaran habilitados siempre o solo por emergencia;
- quien puede crear usuarios locales;
- cuanto tiempo puede vivir una cuenta local temporal;
- como se auditan altas, cambios de clave y desactivaciones.
