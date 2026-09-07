# Login Active Directory en Inventario Modular

Esta guia explica la primera integracion de login contra Active Directory del sistema
nuevo. La idea es que sirva para estudiar el codigo y para continuar la aventura sin perder
el hilo.

## Objetivo de esta etapa

Permitir que un usuario del dominio entre a Inventario Modular con su cuenta de red y que
la pantalla inicial muestre datos traidos desde AD:

- usuario/cuenta
- nombre visible
- fuero
- atributos no sensibles recibidos durante el login

Todo es solo lectura. La aplicacion no crea usuarios en AD, no modifica atributos y no
cambia claves.

## Datos reales tomados del sistema viejo

Desde el servidor viejo se confirmo:

```text
AD_SERVER=10.15.0.41
AD_DOMAIN=podjudsp.local
AD_BASE_DN=OU=USUARIOS,OU=PODJUDSP,DC=podjudsp,DC=local
AD_USE_SSL=false
AD_CONNECT_TIMEOUT=5
```

Para Spring Boot se traducen asi:

```bash
INVENTARIO_LDAP_ENABLED="true"
INVENTARIO_LDAP_URL="ldap://10.15.0.41:389"
INVENTARIO_LDAP_DOMAIN="podjudsp.local"
INVENTARIO_LDAP_BASE_DN="OU=USUARIOS,OU=PODJUDSP,DC=podjudsp,DC=local"
INVENTARIO_LDAP_DISPLAY_NAME_ATTRIBUTE="displayName"
INVENTARIO_LDAP_FUERO_ATTRIBUTE="department"
```

## Flujo de login

```text
Navegador
  -> GET /admin
  -> Spring Security detecta que falta login
  -> redirige a /login
  -> usuario ingresa usuario y clave de red
  -> Spring Security consulta Active Directory
  -> si AD valida la clave, crea el usuario autenticado en memoria
  -> AdminController recibe el usuario autenticado
  -> templates/admin/index.html muestra usuario, nombre, fuero y atributos
```

## Archivos principales

### InventarioModularApplication.java

Archivo de arranque de Spring Boot.

La anotacion `@ConfigurationPropertiesScan` permite que Spring lea clases de configuracion
tipadas como `ActiveDirectoryProperties`.

Sin esa anotacion, las propiedades `inventario.ldap.*` no quedarian registradas como objeto
configurable.

### ActiveDirectoryProperties.java

Representa las variables:

```text
inventario.ldap.enabled
inventario.ldap.url
inventario.ldap.domain
inventario.ldap.base-dn
inventario.ldap.display-name-attribute
inventario.ldap.fuero-attribute
```

Ventaja: el resto del codigo no lee strings sueltos desde el entorno. Recibe un objeto con
nombres claros.

### SecurityConfig.java

Define la seguridad web:

- `/`, `/css/**` y `/api/v1/sistema/estado` quedan publicos.
- `/admin` y el resto requieren autenticacion.
- El login usa el formulario estandar de Spring Security.
- El logout sale por `POST /logout`.
- Si `inventario.ldap.enabled=true`, se registra
  `ActiveDirectoryLdapAuthenticationProvider`.

Ese proveedor es el encargado de hablar con AD.

### ActiveDirectoryUserDetailsContextMapper.java

Convierte la respuesta LDAP/AD en un usuario que la aplicacion puede usar.

Lee:

- `displayName`, para nombre visible.
- `department`, o el atributo configurado, para fuero.
- atributos LDAP no vacios para mostrarlos en una tabla de diagnostico.

Tambien bloquea escritura hacia AD. Si alguien intenta mapear datos de la app hacia AD,
lanza una excepcion con este mensaje:

```text
Inventario Modular solo lee usuarios desde Active Directory.
```

### ActiveDirectoryUserDetails.java

Extiende el usuario estandar de Spring Security y agrega:

- `displayName`
- `fuero`
- `attributes`

Esos datos viven en memoria durante la sesion autenticada. No se guardan todavia en MySQL.

### AdminController.java

Recibe el usuario autenticado con `@AuthenticationPrincipal`.

Si el usuario viene desde AD, muestra los datos reales del AD. Si se esta probando en modo
local sin AD, usa valores de respaldo para que la pantalla no se rompa.

### templates/admin/index.html

Pantalla inicial:

- muestra estado del sistema
- muestra identidad del usuario
- muestra tabla de atributos AD
- tiene boton `Salir`

Thymeleaf escapa el texto por defecto con `th:text`, lo que evita renderizar HTML recibido
desde AD como si fuera codigo.

### static/css/admin.css

Estilos simples para que la pantalla sea legible en escritorio y celular.

## Por que no levanto `http://10.15.2.251:8081/`

El navegador mostro:

```text
ERR_CONNECTION_REFUSED
```

Ese error significa que el servidor esta accesible por red, pero no hay ningun proceso
escuchando en el puerto `8081`.

Se confirmo con:

```bash
ps -ef | grep '[j]ava'
ss -ltnp | grep ':8081' || echo "Nada escuchando en 8081"
```

Resultado:

```text
No habia procesos Java.
Nada escuchando en 8081.
```

Conclusion: el `.jar` estaba construido, pero la aplicacion no estaba ejecutandose.

## Arranque manual para laboratorio

Desde PuTTY:

```bash
cd /opt/inventario-modular

INVENTARIO_DB_URL="jdbc:mysql://10.15.0.62:3306/inventario_modular" \
INVENTARIO_DB_USER="inventario_modular_app" \
INVENTARIO_DB_PASSWORD="CLAVE_REAL_MYSQL" \
INVENTARIO_LDAP_ENABLED="true" \
INVENTARIO_LDAP_URL="ldap://10.15.0.41:389" \
INVENTARIO_LDAP_DOMAIN="podjudsp.local" \
INVENTARIO_LDAP_BASE_DN="OU=USUARIOS,OU=PODJUDSP,DC=podjudsp,DC=local" \
INVENTARIO_LDAP_DISPLAY_NAME_ATTRIBUTE="displayName" \
INVENTARIO_LDAP_FUERO_ATTRIBUTE="department" \
INVENTARIO_SERVER_PORT="8081" \
java -jar target/inventario-modular-0.0.1-SNAPSHOT.jar
```

Cuando la app arranca bien, la terminal queda ocupada. Eso es normal.

Buscar en la salida:

```text
Tomcat started on port 8081
Started InventarioModularApplication
```

Despues abrir:

```text
http://10.15.2.251:8081/
```

## Comandos de diagnostico

Ver si Java esta corriendo:

```bash
ps -ef | grep '[j]ava'
```

Ver si el puerto esta abierto:

```bash
ss -ltnp | grep ':8081' || echo "Nada escuchando en 8081"
```

Ver variables cargadas sin mostrar claves:

```bash
env | grep '^INVENTARIO_' | sed 's/PASSWORD=.*/PASSWORD=******** OCULTA ********/'
```

## Seguridad

- No commitear `.env`.
- No pegar claves reales en README, issues, commits ni capturas publicas.
- No activar HTTPS tocando nginx del sistema viejo en esta etapa.
- No usar `AD_SYNC_PASSWORD` para esta prueba de login.
- No autorizar escritura sobre AD.

