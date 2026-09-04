# Inventario Modular

Sistema modular de inventario en Java para el Departamento de Informatica del Centro
Judicial San Pedro.

## Entorno objetivo inicial

Esta instalacion y este repositorio estan documentados para **Windows** como entorno de
desarrollo inicial.

La base de datos de desarrollo en Windows puede ser **MySQL local**, separada de cualquier
base de produccion:

```text
inventario_modular
```

En el entorno del trabajo, la base MySQL no esta en el mismo servidor Ubuntu de la
aplicacion. Debe apuntar al servidor separado `10.15.0.62`, con permisos otorgados al
host/IP del servidor de aplicacion.

## Enfoque

Inventario Modular nace como un backend **API-first** preparado para una futura app movil.
La web administrativa sera un cliente minimo para configuracion y gestion, no el lugar
principal de las reglas de negocio.

## Stack

- Java 21 LTS
- Spring Boot
- Maven
- MySQL
- Flyway
- Spring Security
- LDAP / Active Directory
- Thymeleaf para panel administrativo minimo

## Paquete Java

La estructura base del codigo sigue el dominio institucional
`justiciajujuy.gov.ar`, invertido segun la convencion Java, y agrega la sede San Pedro
porque esta instalacion corresponde a San Pedro de Jujuy:

```text
src/main/java/ar/gov/justiciajujuy/sanpedro/inventario
```

Paquete base:

```java
ar.gov.justiciajujuy.sanpedro.inventario
```

## Rama inicial

La rama de arranque del proyecto es:

```text
primeros-pasos
```

## Desarrollo local

Verificar entorno:

```powershell
java -version
mvn -version
```

En esta maquina, Maven quedo instalado localmente en:

```text
C:\Users\Gustavo\tools\apache-maven-3.9.16
```

Ejecutar tests:

```powershell
.\mvnw.cmd --batch-mode test
```

Si `mvn` no aparece o Maven usa Java 8:

```powershell
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot"
$env:Path = "$env:JAVA_HOME\bin;$env:USERPROFILE\tools\apache-maven-3.9.16\bin;$env:Path"
mvn test
```

`BUILD SUCCESS` es una salida de Maven, no un comando.

Ejecutar app en modo local, preparada para trabajar con MySQL:

```powershell
.\mvnw.cmd spring-boot:run -Dspring-boot.run.profiles=local
```

Ese modo usa el puerto `8081` para no chocar con el inventario viejo:

```text
http://localhost:8081/login
http://localhost:8081/admin
http://localhost:8081/api/v1/sistema/estado
```

El perfil `local` intenta primero la base MySQL del trabajo y, si no hay conexion, cae a
la base MySQL local de Windows:

```text
Trabajo: jdbc:mysql://10.15.0.62:3306/inventario_modular
Casa:    jdbc:mysql://127.0.0.1:3306/inventario_modular
```

`/admin` requiere autenticacion. En laboratorio local/casa se ingresa con:

```text
Usuario: admin.local
Clave: AdminLocal123
```

Al ingresar, el panel `/admin` muestra el modo activo para orientacion operativa:

- `TRABAJO`: Active Directory disponible y MySQL remoto.
- `LOCAL`: Active Directory apagado/no disponible o fallback a MySQL local.

La pantalla `/login` es una vista propia del proyecto para evitar depender de la pagina
generada por Spring Security. En Ubuntu/trabajo, la autenticacion prevista es contra
Active Directory y la autorizacion local queda en MySQL.

El inventario viejo entraba por HTTPS. En Inventario Modular, durante laboratorio, la app
Spring Boot corre por HTTP interno y queda preparada para recibir HTTPS delante mediante
nginx/reverse proxy cuando se defina el despliegue real. No instalar nginx ni systemd para
este laboratorio inicial.

## Base de datos

La base de desarrollo/local y la futura base de laboratorio en el trabajo se llaman:

```text
inventario_modular
```

En Windows puede correr contra MySQL local para estudiar y probar. En el trabajo, la app
Ubuntu debe conectarse a MySQL en `10.15.0.62`, no a `localhost`. Produccion queda fuera
de esta primera etapa.

La guia paso a paso para crear la base local, usuario local y verificar Flyway esta en:

- [Base de datos local Windows](docs/inventario-modular/base-datos-local-windows.md)

La bitacora y el circuito actual de equipos/componentes estan documentados en:

- [Bitacora del proyecto](docs/inventario-modular/bitacora-del-proyecto.md)
- [Modulo Componentes y Gemelo Digital](docs/inventario-modular/modulo-componentes-gemelo-digital.md)
- [Stock, ordenes de armado y comparacion](docs/inventario-modular/stock-ordenes-armado-y-comparacion.md)
- [Modulo Tareas Tecnicas](docs/inventario-modular/modulo-tareas-tecnicas.md)
- [Modulo Muebles](docs/inventario-modular/modulo-muebles.md)
- [Modulo Patrimonio](docs/inventario-modular/modulo-patrimonio.md)
- [Modulo Reportes](docs/inventario-modular/modulo-reportes.md)
- [Modulo Actas](docs/inventario-modular/modulo-actas.md)
- [Modulo Ubicaciones](docs/inventario-modular/modulo-ubicaciones.md)

## Active Directory

La primera integracion de seguridad autentica usuarios contra Active Directory en modo
solo lectura. La app no crea, modifica ni borra usuarios del dominio.

Variables previstas fuera de git:

```text
INVENTARIO_LDAP_ENABLED=true
INVENTARIO_LDAP_URL=ldap://SERVIDOR_AD:389
INVENTARIO_LDAP_DOMAIN=DOMINIO
INVENTARIO_LDAP_BASE_DN=DC=ejemplo,DC=local
INVENTARIO_LDAP_DISPLAY_NAME_ATTRIBUTE=displayName
INVENTARIO_LDAP_FUERO_ATTRIBUTE=department
INVENTARIO_LDAP_READ_ONLY_USER_DN=
INVENTARIO_LDAP_READ_ONLY_PASSWORD=
INVENTARIO_LDAP_USER_SEARCH_BASE=
INVENTARIO_LDAP_USER_SEARCH_FILTER=(&(objectClass=user)(!(objectClass=computer)))
INVENTARIO_LDAP_USER_SEARCH_LIMIT=50
```

La administracion de usuarios no carga todo Active Directory al abrir. En
`/admin/usuarios` se busca por usuario, nombre o apellido; desde cada resultado se
autoriza la cuenta AD en MySQL y se le asignan roles/modulos. Si el login AD funciona pero
la busqueda muestra `No disponible`, revisar `INVENTARIO_LDAP_READ_ONLY_USER_DN` y
`INVENTARIO_LDAP_READ_ONLY_PASSWORD`: el login usa la clave ingresada por la persona, pero
la busqueda administrativa necesita una cuenta lectora o consulta anonima habilitada.

Validacion en produccion, 31 de agosto de 2026: despues de configurar la cuenta lectora
LDAP en `/etc/inventario-modular/inventario-modular.env`, la busqueda de usuarios de
dominio respondio correctamente desde `admin.local`. La seccion de dominio quedo ubicada
arriba de la pantalla para buscar, seleccionar y autorizar usuarios AD antes de revisar la
tabla de usuarios autorizados.

Al iniciar sesion, el panel `/admin` muestra:

- Usuario/cuenta usada para autenticarse.
- Nombre visible traido del atributo `displayName`.
- Fuero traido del atributo configurable `INVENTARIO_LDAP_FUERO_ATTRIBUTE`.
- Tabla de atributos no sensibles recibidos desde AD durante el login.
- Boton `Salir`, conectado al logout de Spring Security.

Antes de activar AD en Ubuntu hay que confirmar con Sistemas/AD los valores reales de
dominio, base DN, cuenta lectora opcional y el atributo exacto donde esta cargado el
fuero.

## Modulos implementados

### Seguridad y usuarios

La pantalla `/admin/usuarios` permite listar identidades autorizadas, crear usuarios
locales con clave hasheada, buscar usuarios de Active Directory y autorizarlos sin guardar
claves de dominio.

### Equipos

La primera version del modulo `EQUIPOS` esta disponible en:

```text
http://localhost:8081/admin/equipos
```

API:

```text
GET  /api/v1/equipos
GET  /api/v1/equipos/{id}
POST /api/v1/equipos/inventario
GET  /scripts/windows/inventario-modular.ps1
GET  /scripts/windows/inventario-modular.ps1.sha256
```

El listado soporta busqueda por nombre de equipo, ultimo usuario o fuero. El endpoint de
inventario crea o actualiza equipos por `nombre` y queda preparado para conectar el
script de inventario. Desde `/login` se puede copiar el comando PowerShell para ejecutar
el script en una PC; la IP del servidor se arma automaticamente con la direccion desde
donde se abrio el login.

Guia tecnica:

- [Login Active Directory](docs/inventario-modular/login-active-directory.md)
- [ADR-004: Login Active Directory solo lectura](docs/decisions/ADR-004-login-active-directory-solo-lectura.md)

### Muebles, Patrimonio, Actas, Ubicaciones y Reportes

Las primeras versiones de estos modulos estan disponibles en:

```text
http://localhost:8081/admin/muebles
http://localhost:8081/admin/patrimonio
http://localhost:8081/admin/actas
http://localhost:8081/admin/ubicaciones
http://localhost:8081/admin/reportes
```

APIs principales:

```text
GET  /api/v1/muebles
POST /api/v1/muebles
PUT  /api/v1/muebles/{id}
GET  /api/v1/patrimonio/bienes
POST /api/v1/patrimonio/bienes
PUT  /api/v1/patrimonio/bienes/{id}
GET  /api/v1/actas
POST /api/v1/actas
PUT  /api/v1/actas/{id}
GET  /api/v1/ubicaciones
POST /api/v1/ubicaciones
PUT  /api/v1/ubicaciones/{id}
GET  /api/v1/reportes/resumen
GET  /api/v1/reportes/muebles.csv
GET  /api/v1/reportes/patrimonio.csv
GET  /api/v1/reportes/tareas.csv
GET  /api/v1/reportes/actas.csv
GET  /api/v1/reportes/ubicaciones.csv
```

### Stock, Ordenes de Armado y Taller

Permite gestionar el stock de piezas sueltas y el ensamblado de estaciones en el laboratorio:

- **Stock de componentes**: Registro y control de estado (`DISPONIBLE`, `RESERVADO`, `ASIGNADO`, `BAJA`).
- **Trazabilidad de compras**: Soporta **Remito**, **Orden de Compra / Expediente** y **Proveedor** tanto en componentes de stock como en el gemelo digital del equipo.
- **Taller de Informática en 1 clic**: Desde `/admin/equipos`, el botón `⚡ Iniciar PC en Taller` crea una estación provisoria (`ARMADO-001`, `ARMADO-002`, etc.) y abre su Orden de Armado en borrador de inmediato.
- **Propagación automática**: Al confirmar la salida física de una pieza de stock reservada a una orden, sus datos de compra (remito, OC y proveedor) se transfieren automáticamente al gemelo digital.
- **Resolución canónica de Fueros**: Servicio `FueroService` con catálogo precargado de juzgados y salas del Centro Judicial San Pedro y soporte de unidades organizacionales de Active Directory.

APIs principales:

```text
GET  /api/v1/stock/componentes
POST /api/v1/stock/componentes
PUT  /api/v1/stock/componentes/{id}
GET  /api/v1/ordenes-armado
POST /api/v1/ordenes-armado
POST /admin/equipos/nuevo-taller
```

Guia tecnica:
- [Stock, Ordenes de Armado y Gemelo Digital](docs/inventario-modular/stock-ordenes-armado-y-comparacion.md)

## Documentacion

La documentacion del estudio inicial esta en `docs/inventario-modular`.

Documentos principales:

- [Instalacion desde cero](docs/inventario-modular/instalacion-desde-cero.md)
- [Bitacora del proyecto](docs/inventario-modular/bitacora-del-proyecto.md)
- [Requerimientos del sistema](docs/inventario-modular/requerimientos-sistema.md)
- [Plan de trabajo](docs/inventario-modular/plan-de-trabajo.md)
- [Versionado Git](docs/inventario-modular/versionado-git.md)
- [CI/CD](docs/inventario-modular/ci-cd.md)
- [Login Active Directory](docs/inventario-modular/login-active-directory.md)
- [Proximo paso funcional](docs/inventario-modular/proximo-paso-funcional.md)
- [Modulo Equipos](docs/inventario-modular/modulo-equipos.md)
- [Modulo Componentes y Gemelo Digital](docs/inventario-modular/modulo-componentes-gemelo-digital.md)
- [Modulo Tareas Tecnicas](docs/inventario-modular/modulo-tareas-tecnicas.md)
- [Modulo Actas](docs/inventario-modular/modulo-actas.md)
- [Modulo Ubicaciones](docs/inventario-modular/modulo-ubicaciones.md)
- [Cierre de jornada Windows](docs/inventario-modular/cierre-jornada-windows.md)
- [Runbook Ubuntu por PuTTY](docs/inventario-modular/runbook-manana-ubuntu-putty.md)
- [Modo local Windows sin dominio](docs/inventario-modular/modo-local-windows-sin-dominio.md)
- [Base de datos local Windows](docs/inventario-modular/base-datos-local-windows.md)
- [Script de inventario Windows](docs/inventario-modular/script-inventario-windows.md)
- [Actualizacion produccion Inventario Modular](docs/inventario-modular/actualizacion-produccion-inventario-modular.md)
- [Incidente login local repetido](docs/inventario-modular/incidente-login-local-repetido.md)

## Repositorios

- GitLab: `https://gitlab.com/gustavoeliasm/inventario-modular`
- GitHub: `https://github.com/gustavounju/inventario-modular`

Decision de trabajo:

- GitLab lo puede gestionar el asistente de forma automatica cuando haga falta.
- GitHub lo gestiona Gustavo por comandos para practicar versionado.
- Desde esta decision, los commits nuevos se escriben en español latino.

La rama inicial `primeros-pasos` ya fue subida a ambos remotos.

Para subir a GitHub los commits que el asistente ya subio a GitLab:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
git push github primeros-pasos
```
