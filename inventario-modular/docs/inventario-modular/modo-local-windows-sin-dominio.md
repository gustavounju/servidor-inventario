# Modo Local Windows Sin Dominio

Guia para trabajar desde casa con Inventario Modular cuando no hay acceso al dominio real
del Poder Judicial.

## Objetivo

Permitir desarrollo local en Windows sin Active Directory, sin quitar ni debilitar el modo
real de produccion/trabajo.

En el trabajo:

```text
LDAP/Active Directory real -> usuario y clave de dominio
MySQL remoto -> 10.15.0.62/inventario_modular
```

En casa:

```text
Usuarios locales -> usuario configurado o usuarios creados en MySQL local
MySQL local -> 127.0.0.1/inventario_modular
```

Cuando todavia no esta creada la base MySQL local, se puede usar el perfil `casa`.
Ese perfil levanta una base H2 de archivo dentro de `.local-data/` y permite probar login,
pantallas y API sin tocar MySQL, Active Directory ni produccion.

## Regla de deteccion

El perfil `local` intenta primero la base modular remota del trabajo:

```properties
inventario.datasource.primary.url=jdbc:mysql://10.15.0.62:3306/inventario_modular
```

Si esa base no esta disponible desde la red actual, cambia automaticamente al fallback:

```properties
inventario.datasource.fallback.url=jdbc:mysql://127.0.0.1:3306/inventario_modular
```

La pantalla `/admin` muestra el modo detectado para orientar al usuario:

```text
TRABAJO -> Active Directory disponible y MySQL remoto
LOCAL   -> usuarios locales y base local/fallback
```

El endpoint `GET /api/v1/sistema/estado` tambien informa el modo, la base activa y si
Active Directory esta configurado/disponible, sin mostrar claves.

## Usuario local por defecto

El perfil `local` trae estos valores para estudiar:

```text
Usuario: admin.local
Clave: AdminLocal123
Nombre visible: Administrador Local
Fuero: Desarrollo local
```

Son valores de desarrollo. En una maquina compartida conviene cambiarlos con variables de
entorno antes de iniciar la app.

## Variables recomendadas en PowerShell

Desde Windows:

```powershell
cd "G:\unju2025\google gravity\inventario-modular"

$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot"
$env:Path = "$env:JAVA_HOME\bin;$env:USERPROFILE\tools\apache-maven-3.9.16\bin;$env:Path"

$env:INVENTARIO_DB_URL = "jdbc:mysql://127.0.0.1:3306/inventario_modular"
$env:INVENTARIO_DB_USER = "inventario_local"
$env:INVENTARIO_DB_PASSWORD = "Cambiar_Clave_Local_123!"

$env:INVENTARIO_LDAP_ENABLED = "false"
$env:INVENTARIO_LOCAL_AUTH_ENABLED = "true"
$env:INVENTARIO_LOCAL_AUTH_USERNAME = "admin.local"
$env:INVENTARIO_LOCAL_AUTH_PASSWORD = "AdminLocal123"
$env:INVENTARIO_LOCAL_AUTH_DISPLAY_NAME = "Administrador Local"
$env:INVENTARIO_LOCAL_AUTH_FUERO = "Desarrollo local"
```

## Ejecutar tests

```powershell
mvn test
```

Salida esperada:

```text
BUILD SUCCESS
```

## Iniciar la app

### Opcion recomendada para casa sin MySQL listo

Usar el perfil `casa`:

```powershell
mvn spring-boot:run "-Dspring-boot.run.profiles=casa"
```

Abrir desde la misma PC:

```text
http://localhost:8081/
```

O desde otro equipo/celular de la misma red:

```text
http://192.168.1.8:8081/
```

Ingresar:

```text
Usuario: admin.local
Clave: AdminLocal123
```

La base local de este modo queda en:

```text
.local-data/
```

Ese directorio esta ignorado por git.

### Opcion con MySQL local

Usar el perfil `local` cuando ya exista la base `inventario_modular` y el usuario
`inventario_local` tenga clave y permisos. Este es el modo recomendado cuando MySQL local
ya esta preparado.

```powershell
mvn spring-boot:run
```

Si aparece este error:

```text
Access denied for user 'inventario_local'@'localhost' (using password: NO)
```

significa que Spring Boot intento entrar a MySQL local sin clave. Actualizar el codigo
desde GitLab y verificar que `application-local.properties` tenga este fallback:

```properties
inventario.datasource.fallback.password=${INVENTARIO_DB_FALLBACK_PASSWORD:Cambiar_Clave_Local_123!}
```

Si aparece:

```text
Invalid credentials
```

usar exactamente:

```text
Usuario: admin.local
Clave: AdminLocal123
```

Tambien verificar que el servidor se haya iniciado con perfil `local` o `casa`, y no con
una configuracion vieja.

Nota tecnica: este error tambien puede aparecer si el servidor quedo iniciado con una
version anterior del codigo local. El login simulado debe crear una identidad nueva en cada
intento, porque Spring Security borra las credenciales del usuario autenticado despues de un
ingreso correcto. Si el proceso viejo sigue abierto, detenerlo y volver a iniciar la app.

Abrir:

```text
http://localhost:8081/
```

Ingresar:

```text
Usuario: admin.local
Clave: AdminLocal123
```

## Como esta implementado

- `LocalAuthenticationProperties` lee las propiedades `inventario.local-auth.*`.
- `LocalAuthenticationConfig` crea un usuario local de rescate/desarrollo en memoria.
- `DatabaseLocalAuthenticationProvider` valida usuarios locales guardados en MySQL.
- La clave local se codifica con BCrypt al arrancar.
- La pantalla admin recibe una identidad compatible con la usada por Active Directory.
- Los atributos mostrados indican que la sesion viene de `LOCAL_SIMULADO`.
- El perfil `casa` usa `application-casa.properties`, H2 local de archivo y scripts SQL
  en `src/main/resources/db/casa/`.

## Que no hace

- No consulta Active Directory cuando `inventario.ldap.enabled=false`.
- No guarda claves de dominio.
- No crea usuarios en MySQL cuando se usa el perfil `casa`, porque ese modo usa H2.
- No reemplaza el esquema definitivo de usuarios, roles, permisos y modulos.
- No debe usarse como mecanismo productivo sin una politica institucional de emergencia.

## Diferencia con el trabajo

En el trabajo, la app debe iniciar con:

```bash
INVENTARIO_LDAP_ENABLED="true"
INVENTARIO_LDAP_URL="ldap://10.15.0.41:389"
INVENTARIO_LDAP_DOMAIN="podjudsp.local"
INVENTARIO_LDAP_BASE_DN="OU=USUARIOS,OU=PODJUDSP,DC=podjudsp,DC=local"
```

Y la base debe apuntar a:

```bash
INVENTARIO_DB_PRIMARY_URL="jdbc:mysql://10.15.0.62:3306/inventario_modular"
```

En casa, si esos valores no responden, el sistema cae a MySQL local y la pantalla informa
`LOCAL`.
