# Usuarios Locales y Active Directory

## Objetivo

Inventario Modular permite trabajar con dos tipos de identidad:

```text
AD     -> usuario validado por Active Directory.
LOCAL  -> usuario creado dentro de Inventario Modular con clave propia.
```

Ambos tipos pueden recibir roles, permisos y modulos. La diferencia esta en quien valida la
clave.

## Usuario de Active Directory

Un usuario `AD` es una cuenta existente en el dominio del Poder Judicial.

Flujo:

```text
Usuario ingresa usuario y clave
-> Active Directory valida la clave
-> Inventario Modular consulta MySQL
-> MySQL decide roles, permisos y modulos
```

Reglas:

- Inventario Modular no guarda claves de dominio.
- Inventario Modular no cambia claves de dominio.
- Inventario Modular no crea cuentas de dominio.
- La pantalla de usuarios debe permitir seleccionar una identidad ya existente del dominio y asignarle permisos.
- Si la cuenta existe en AD pero no esta autorizada en MySQL, queda sin modulos.

## Usuario local

Un usuario `LOCAL` es una cuenta creada dentro de Inventario Modular.

Sirve para:

- trabajar desde casa sin Active Directory;
- crear usuarios temporales para tareas puntuales;
- dar acceso controlado a personas que no usan cuenta de dominio todos los dias;
- probar roles y permisos sin depender del servidor AD.

Ejemplo real:

```text
Un chofer no usa computadora todos los dias.
Durante horas sin viajes, se le asigna cargar inventario.
Se crea un usuario local temporal.
Se le asigna un rol limitado.
Cuando termina la tarea, se desactiva o elimina su acceso.
```

## Como se guarda la clave local

La clave local no se guarda en texto plano.

Inventario Modular guarda:

```text
credenciales_locales.password_hash
```

Ese valor es un hash BCrypt. Sirve para comparar la clave ingresada en el login, pero no
permite leer la clave original.

## Tablas involucradas

```text
usuarios
-> identidad autorizada
-> origen: AD o LOCAL
-> activo

credenciales_locales
-> solo para usuarios LOCAL
-> password_hash
-> requiere_cambio_clave

usuario_roles
-> roles asignados a cada identidad

rol_modulo_permisos
-> modulos y permisos que recibe cada rol
```

## Uso desde la pantalla

Abrir:

```text
/admin/usuarios
```

### Crear usuario local

```text
Usuario local: chofer.local
Clave local: cargar una clave temporal de al menos 8 caracteres
Rol inicial: elegir el minimo necesario
```

El formulario de alta crea solamente usuarios `LOCAL`.

### Autorizar usuario de Active Directory

El usuario `AD` debe existir primero en el dominio. Inventario Modular no debe ofrecer
un formulario que parezca crear cuentas en Active Directory.

Flujo correcto esperado:

```text
Buscar usuario del dominio por usuario, nombre o apellido
-> seleccionar una cuenta existente
-> guardar autorizacion local en MySQL
-> asignar roles, permisos y modulos
-> no pedir ni guardar clave de dominio
```

La pantalla `/admin/usuarios` no carga todo el dominio al abrir. Primero muestra un
buscador. Solo cuando se envia una busqueda de al menos 2 caracteres consulta LDAP. Esto
evita respuestas enormes del dominio y permite autorizar puntualmente usuarios como
`gmurad`.

En produccion, el 31 de agosto de 2026 se confirmo el flujo completo: con `admin.local`
se busco un usuario de dominio, Active Directory devolvio resultados y la pantalla mostro
las filas ordenadas arriba, antes de la creacion de usuarios locales y de la tabla de
usuarios autorizados.

En casa este flujo no se puede probar contra el dominio real. En produccion/trabajo se
activa con LDAP de lectura y, si el dominio no permite busqueda anonima, con una cuenta
tecnica lectora configurada por variables de entorno.

Si la seccion muestra `No disponible` despues de buscar, revisar primero que existan estas
variables en `/etc/inventario-modular/inventario-modular.env`:

```bash
INVENTARIO_LDAP_ENABLED=true
INVENTARIO_LDAP_URL=ldap://SERVIDOR_AD:389
INVENTARIO_LDAP_DOMAIN=podjudsp.local
INVENTARIO_LDAP_BASE_DN=OU=USUARIOS,OU=PODJUDSP,DC=podjudsp,DC=local
INVENTARIO_LDAP_READ_ONLY_USER_DN=CN=lector-inventario,OU=Servicios,DC=podjudsp,DC=local
INVENTARIO_LDAP_READ_ONLY_PASSWORD=CLAVE_REAL_SOLO_EN_SERVIDOR
```

El login AD puede funcionar aunque la busqueda administrativa falle, porque son caminos
distintos: el login valida con la clave ingresada por el usuario, mientras que la busqueda
de usuarios para administracion necesita una cuenta lectora o permisos de consulta anonima
en LDAP.

## Configuracion y fallback

El proveedor de usuarios locales de base se controla con:

```properties
inventario.local-db-auth.enabled=true
```

En Windows/casa queda habilitado por defecto en los perfiles `local` y `casa`.

El usuario local de rescate/desarrollo por configuracion se controla con:

```properties
inventario.local-auth.enabled=true
inventario.local-auth.username=admin.local
```

En el perfil `local`, los proveedores locales quedan disponibles para que el sistema pueda
seguir funcionando cuando Active Directory no esta disponible. En produccion/trabajo, si
se decide no permitir usuarios locales de emergencia, debe desactivarse explicitamente:

```bash
INVENTARIO_LOCAL_AUTH_ENABLED=false
INVENTARIO_LOCAL_DB_AUTH_ENABLED=true
```

La lectura de usuarios de dominio se controla con:

```bash
INVENTARIO_LDAP_ENABLED=true
INVENTARIO_LDAP_URL=ldap://10.15.0.41:389
INVENTARIO_LDAP_DOMAIN=podjudsp.local
INVENTARIO_LDAP_BASE_DN=OU=USUARIOS,OU=PODJUDSP,DC=podjudsp,DC=local
INVENTARIO_LDAP_READ_ONLY_USER_DN=CN=lector-inventario,OU=Servicios,DC=podjudsp,DC=local
INVENTARIO_LDAP_READ_ONLY_PASSWORD=...
INVENTARIO_LDAP_USER_SEARCH_BASE=
INVENTARIO_LDAP_USER_SEARCH_FILTER=(&(objectClass=user)(!(objectClass=computer)))
INVENTARIO_LDAP_USER_SEARCH_LIMIT=50
```

`INVENTARIO_LDAP_READ_ONLY_PASSWORD` es secreto y no debe commitearse. Si LDAP esta
apagado, `/admin/usuarios` muestra la seccion de dominio como no disponible sin romper el
alta local.

La pantalla `/admin` informa el modo de trabajo:

```text
TRABAJO -> Active Directory disponible y MySQL remoto.
LOCAL   -> Active Directory apagado/no disponible o base local/fallback.
```

## Recomendacion operativa

Para usuarios locales temporales:

1. Crear el usuario con origen `LOCAL`.
2. Asignar el rol minimo necesario.
3. Usar una clave temporal.
4. Desactivar el usuario cuando termina la tarea.
5. No reutilizar claves entre personas.

## Estado actual

Implementado:

- origen `AD` o `LOCAL` en usuarios;
- tabla `credenciales_locales`;
- alta de usuario local con password desde API y pantalla;
- autenticacion de usuario local contra hash BCrypt;
- separacion visual entre crear usuarios locales y autorizar usuarios AD;
- busqueda LDAP filtrada de usuarios de dominio cuando `inventario.ldap.enabled=true`;
- busqueda de usuarios AD ubicada arriba de la pantalla de administracion para acelerar la autorizacion;
- autorizacion local de usuarios AD desde API y pantalla, sin pedir clave de dominio;
- indicador visual de modo de trabajo, base activa y autenticacion;
- pruebas automatizadas para verificar que no se guarde password plano.

Pendiente:

- cambio de clave desde pantalla;
- activar/desactivar usuario desde pantalla;
- eliminar credencial local o desactivar usuario temporal;
- auditoria de altas/cambios de clave;
- auditoria visual/historica de autorizaciones de usuarios AD.
