# Bitacora Del Proyecto

Esta bitacora resume la evolucion de Inventario Modular desde su creacion hasta el estado
documentado al 31 de agosto de 2026.

El objetivo no es reemplazar los documentos tecnicos, sino dejar una lectura cronologica
en espanol latino, facil de seguir, que explique que se decidio, que se implemento, que se
valido y que quedo pendiente.

Nota sobre credenciales: esta bitacora muestra las credenciales de laboratorio que ya
estan documentadas en el proyecto, por ejemplo `admin.local` / `AdminLocal123`. Las claves
reales de MySQL, LDAP o tokens productivos no estaban escritas en la documentacion fuente;
por eso se dejan como valores a completar en el servidor, sin inventarlas.

## Resumen ejecutivo

Inventario Modular nace como un sistema nuevo para el Departamento de Informatica del
Centro Judicial San Pedro. La necesidad inicial fue salir de la deuda tecnica del
inventario viejo y de los problemas del experimento Inventario Next, sin perder la logica
operativa que ya funciona en el trabajo diario.

La decision central fue construir un backend Java con Spring Boot, API-first, base MySQL
nueva, seguridad con Spring Security, autenticacion contra Active Directory y autorizacion
local por usuarios, roles, permisos y modulos.

Desde el inicio se separo el proyecto nuevo del inventario viejo. El sistema viejo queda
como referencia funcional: sirve para entender flujos reales como equipos, actas,
OVMelos, patrimonio, stock y reportes, pero no se copia su codigo ni su arquitectura.

## 2026-08-27 - Creacion del proyecto base

Se inicio el repositorio de Inventario Modular como un proyecto Java limpio, separado del
inventario anterior.

Hitos principales:

- Se creo la estructura inicial de Spring Boot.
- Se eligio Java 21 LTS como base tecnica.
- Se definio Maven como herramienta de construccion.
- Se adopto el paquete institucional:

```text
ar.gov.justiciajujuy.sanpedro.inventario
```

La rama inicial de trabajo quedo definida como:

```text
primeros-pasos
```

Desde esta etapa quedo claro que produccion no debia tocarse durante el arranque del
proyecto. El primer trabajo debia hacerse en laboratorio, con documentacion y validaciones
controladas.

Comandos base de creacion y rama:

```powershell
git init
git switch -c primeros-pasos
git status --short
```

Comandos de verificacion Java/Maven:

```powershell
java -version
mvn -version
```

## 2026-08-28 - Enfoque API-first y migracion por modulos

Se documento la decision de disenar Inventario Modular como un sistema API-first.

La razon principal fue preparar el backend para una futura app movil sin tener que rehacer
reglas centrales. La web administrativa se definio como cliente minimo para configurar y
gestionar, no como el lugar donde vive la logica de negocio.

Decisiones tomadas:

- Backend Java con Spring Boot.
- API versionada como contrato principal.
- MySQL como base nueva para desarrollo y laboratorio.
- Flyway para migraciones.
- Spring Security para seguridad.
- LDAP / Active Directory para autenticacion institucional.
- Autorizacion propia en MySQL.
- Thymeleaf solo para panel administrativo minimo.

Tambien se documento que el inventario viejo se usara como referencia funcional. La regla
practica quedo:

```text
Conservar la logica que funciona. Rehacer la implementacion en Java.
```

## 2026-08-28 - Preparacion de Windows y repositorios

El desarrollo inicial se preparo desde Windows, en casa, sin acceso al servidor Ubuntu ni
a bases remotas.

Se registro:

- JDK 21 instalado en Windows.
- Maven instalado localmente en el perfil del usuario.
- MySQL local disponible para desarrollo.
- Tests locales ejecutados con resultado correcto.
- Construccion del `.jar` con Maven.
- Repositorio principal en GitLab.
- Repositorio espejo en GitHub para practica de versionado.

La regla operativa de remotos quedo asi:

- GitLab es el remoto principal de trabajo.
- GitHub funciona como espejo/manual para practica.
- Los commits nuevos se escriben en espanol latino.

Tambien se agrego un pipeline inicial de GitLab CI/CD con dos etapas:

```text
validar -> construir
```

En esta etapa todavia no existia despliegue automatico a produccion.

Comandos usados/documentados para preparar Java y Maven en Windows:

```powershell
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot"
$env:Path = "$env:JAVA_HOME\bin;$env:USERPROFILE\tools\apache-maven-3.9.16\bin;$env:Path"
mvn -version
```

Comandos de validacion local:

```powershell
mvn test
mvn -DskipTests package
```

Comandos de Git y remotos:

```powershell
git remote -v
git remote add origin https://gitlab.com/gustavoeliasm/inventario-modular.git
git remote add github https://github.com/gustavounju/inventario-modular.git
git push -u origin primeros-pasos
git push github primeros-pasos
```

Comando para sincronizar GitHub manualmente:

```powershell
cd "G:\unju2025\google gravity\inventario-modular"
git push github primeros-pasos
```

## 2026-08-28 - Base web y estado del sistema

Se implemento la primera base web de Inventario Modular.

Hitos:

- Aplicacion Spring Boot arrancando correctamente.
- Endpoint de estado del sistema.
- Primer panel administrativo minimo.
- Preparacion para correr en el puerto `8081`, evitando choque con el inventario viejo.

La arquitectura empezo a diferenciar claramente el nuevo sistema del sistema anterior. El
inventario viejo seguia activo y fuera del alcance de cambios.

Comandos para ejecutar y probar localmente:

```powershell
.\mvnw.cmd --batch-mode test
.\mvnw.cmd spring-boot:run -Dspring-boot.run.profiles=local
```

URLs de verificacion:

```text
http://localhost:8081/login
http://localhost:8081/admin
http://localhost:8081/api/v1/sistema/estado
```

Credencial local de laboratorio:

```text
Usuario: admin.local
Clave: AdminLocal123
```

## 2026-08-28 - Instalacion Ubuntu y base MySQL remota

Se preparo el camino de instalacion en Ubuntu usando PuTTY/SSH.

Puntos documentados:

- El nuevo sistema se ubica en `/opt/inventario-modular`.
- El servicio systemd previsto se llama `inventario-modular.service`.
- La configuracion real queda fuera de git en:

```text
/etc/inventario-modular/inventario-modular.env
```

La base de datos de trabajo no vive en el mismo servidor Ubuntu de la aplicacion. La app
debe conectarse al servidor MySQL separado:

```text
10.15.0.62:3306/inventario_modular
```

Esta decision evita confundir el laboratorio nuevo con el inventario viejo y obliga a
documentar variables, permisos y conectividad antes de avanzar.

Comandos documentados para entrar y verificar Ubuntu:

```bash
hostname
pwd
java -version
cd /opt/inventario-modular
git remote -v
git branch --show-current
git status --short
```

Comandos de clonado y compilacion:

```bash
cd /opt
git clone https://gitlab.com/gustavoeliasm/inventario-modular.git inventario-modular
cd /opt/inventario-modular
git checkout primeros-pasos
sh ./mvnw --batch-mode test
sh ./mvnw --batch-mode -DskipTests package
```

Variables guia para el servidor, con secretos reales a completar solamente en
`/etc/inventario-modular/inventario-modular.env`:

```env
SPRING_PROFILES_ACTIVE=local
INVENTARIO_SERVER_PORT=8081
INVENTARIO_DB_PRIMARY_URL=jdbc:mysql://10.15.0.62:3306/inventario_modular
INVENTARIO_DB_PRIMARY_USER=inventario_modular_app
INVENTARIO_DB_PRIMARY_PASSWORD=CAMBIAR_EN_SERVIDOR
INVENTARIO_REPORT_TOKEN=CAMBIAR_TOKEN_LARGO_ALEATORIO
INVENTARIO_LOCAL_AUTH_ENABLED=true
INVENTARIO_LOCAL_DB_AUTH_ENABLED=true
INVENTARIO_LDAP_ENABLED=true
INVENTARIO_LDAP_URL=ldap://10.15.0.41:389
INVENTARIO_LDAP_DOMAIN=podjudsp.local
INVENTARIO_LDAP_BASE_DN=OU=USUARIOS,OU=PODJUDSP,DC=podjudsp,DC=local
INVENTARIO_LDAP_READ_ONLY_USER_DN=CN=lector-inventario,OU=Servicios,DC=podjudsp,DC=local
INVENTARIO_LDAP_READ_ONLY_PASSWORD=CLAVE_REAL_SOLO_EN_SERVIDOR
```

Comandos para proteger el archivo de entorno:

```bash
sudo chown root:root /etc/inventario-modular/inventario-modular.env
sudo chmod 600 /etc/inventario-modular/inventario-modular.env
```

## 2026-08-28 - Login Active Directory solo lectura

Se implemento la primera integracion con Active Directory.

Datos funcionales tomados del sistema viejo:

- Servidor AD: `10.15.0.41`.
- Dominio: `podjudsp.local`.
- Base DN: `OU=USUARIOS,OU=PODJUDSP,DC=podjudsp,DC=local`.
- Atributos utiles: usuario, nombre visible, fuero, telefono y correo.

La decision de seguridad fue que Inventario Modular autentique contra Active Directory,
pero en esta etapa solo lea datos del usuario que inicia sesion.

Reglas fijadas:

- No guardar claves de dominio.
- No modificar usuarios de Active Directory.
- No sincronizar masivamente usuarios en la primera etapa.
- Mostrar en `/admin` datos no sensibles del usuario autenticado.
- Dejar HTTPS para una etapa posterior con reverse proxy.

Variables LDAP documentadas para activar login AD:

```env
INVENTARIO_LDAP_ENABLED=true
INVENTARIO_LDAP_URL=ldap://10.15.0.41:389
INVENTARIO_LDAP_DOMAIN=podjudsp.local
INVENTARIO_LDAP_BASE_DN=OU=USUARIOS,OU=PODJUDSP,DC=podjudsp,DC=local
INVENTARIO_LDAP_DISPLAY_NAME_ATTRIBUTE=displayName
INVENTARIO_LDAP_FUERO_ATTRIBUTE=department
```

Comando de arranque para laboratorio con variables ya cargadas:

```bash
cd /opt/inventario-modular
sh ./mvnw spring-boot:run
```

## 2026-08-28 - Primer arranque real y servicio modular

Luego de validar base, Java y configuracion, el sistema quedo con una primera base real en
Ubuntu.

Estado alcanzado:

- Repositorio clonado en `/opt/inventario-modular`.
- Conexion a MySQL remoto verificada.
- Tests Maven ejecutados en Ubuntu.
- Pagina de inicio y estado del sistema disponibles.
- Login con Active Directory validado.
- Boton de salida y atributos AD visibles.
- Servicio systemd creado para Inventario Modular.

Este hito marco el primer arranque concreto del nuevo sistema en el entorno de trabajo,
sin reemplazar ni tocar el inventario viejo.

Comandos systemd documentados:

```bash
sudo systemctl daemon-reload
sudo systemctl enable inventario-modular.service
sudo systemctl start inventario-modular.service
systemctl status inventario-modular.service --no-pager -l
sudo journalctl -u inventario-modular.service -n 120 --no-pager
```

Comandos HTTP de verificacion desde Ubuntu:

```bash
curl -s http://127.0.0.1:8081/api/v1/sistema/estado
curl -I http://127.0.0.1:8081/login
```

## 2026-08-28 - Modo local sin dominio

Despues de validar Active Directory real en el trabajo, se documento la necesidad de
seguir desarrollando desde casa.

Problema:

- En casa no hay acceso al dominio real.
- Tampoco siempre hay acceso al MySQL institucional.
- Si todo dependia de AD, el desarrollo local quedaba bloqueado.

Decision:

- Crear un modo local explicito por configuracion.
- Apagar LDAP en casa.
- Habilitar login local.
- Usar MySQL local o perfil `casa` con H2.

Este modo no reemplaza la autenticacion real del trabajo. Solo permite estudiar,
desarrollar y probar pantallas en Windows.

Comandos para modo local con MySQL:

```powershell
$env:INVENTARIO_LDAP_ENABLED = "false"
$env:INVENTARIO_LOCAL_AUTH_ENABLED = "true"
$env:INVENTARIO_LOCAL_DB_AUTH_ENABLED = "true"
.\mvnw.cmd spring-boot:run -Dspring-boot.run.profiles=local
```

Comando para perfil `casa` con H2 local:

```powershell
.\mvnw.cmd spring-boot:run -Dspring-boot.run.profiles=casa
```

Credencial local:

```text
Usuario: admin.local
Clave: AdminLocal123
```

## 2026-08-28 - Autorizacion modular inicial

Una vez resuelta la identidad con Active Directory, se ataco el siguiente problema: que
puede hacer cada persona dentro del sistema.

Se creo una capa de autorizacion propia en MySQL:

- Usuarios.
- Roles.
- Modulos.
- Permisos.
- Relacion entre roles, modulos y permisos.

La regla de seguridad quedo expresada asi:

```text
Active Directory autentica identidad.
Inventario Modular decide autorizacion.
```

La primera migracion Flyway cargo un seed inicial con modulos, permisos, roles y el
usuario `admin.local`.

Comandos para correr migraciones y tests mediante el arranque de Spring Boot:

```powershell
.\mvnw.cmd --batch-mode test
.\mvnw.cmd spring-boot:run -Dspring-boot.run.profiles=local
```

Endpoints de autorizacion inicial:

```text
GET /api/v1/me
GET /api/v1/me/modulos
```

## 2026-08-29 - Perfil casa, login local y primer incidente

Se ajusto el perfil `casa` para que el proyecto pudiera levantarse sin MySQL listo,
usando una base H2 local ignorada por git.

Luego aparecio un incidente en Windows/casa: el login local podia funcionar una vez y
fallar en el siguiente intento con `Invalid credentials`.

Causa tecnica:

- Se reutilizaba una misma instancia de `UserDetails`.
- Spring Security borraba las credenciales despues de una autenticacion correcta.
- El segundo login comparaba contra un objeto que ya no tenia credenciales disponibles.

Solucion:

- Conservar la clave codificada internamente.
- Devolver una instancia nueva de usuario en cada busqueda.
- Agregar prueba de regresion para dos logins seguidos.
- Simplificar la clave local a `AdminLocal123`.

Resultado:

- Login local repetido resuelto.
- Tests ejecutados correctamente.
- Incidente documentado para referencia futura.

Comandos de prueba usados/documentados:

```powershell
mvn -Dtest=LocalAuthenticationConfigTests test
mvn test
```

URLs y resultado esperado:

```text
GET http://192.168.1.8:8081/login -> 200
POST /login admin.local/AdminLocal123 -> 302 /admin
GET /admin -> 200
```

## 2026-08-29 - Pantalla inicial de usuarios

Se creo la primera pantalla administrativa para usuarios:

```text
/admin/usuarios
```

La pantalla permitio empezar a salir de la administracion por SQL directo y acercar la
seguridad modular al navegador.

En esta etapa tambien se documento una distincion clave: no es lo mismo identidad,
autenticacion y autorizacion.

Definicion operativa:

- Identidad: quien es la persona o cuenta.
- Autenticacion: quien valida la clave.
- Autorizacion: que puede ver o hacer dentro de Inventario Modular.

URL de trabajo:

```text
http://localhost:8081/admin/usuarios
```

Credencial local de administracion inicial:

```text
Usuario: admin.local
Clave: AdminLocal123
```

## 2026-08-29 - Usuarios locales y usuarios AD

Se implemento la separacion entre identidades `AD` y `LOCAL`.

Para usuarios de Active Directory:

- La clave se valida contra el dominio.
- Inventario Modular no guarda password.
- MySQL solo guarda autorizacion, roles, permisos y modulos.

Para usuarios locales:

- La clave pertenece a Inventario Modular.
- Se guarda un hash BCrypt en `credenciales_locales`.
- Sirve para desarrollo, rescate o tareas temporales controladas.

La pantalla `/admin/usuarios` empezo a separar dos acciones:

- Crear usuario local con clave propia.
- Autorizar usuario existente de Active Directory sin pedir clave de dominio.

Propiedades/variables relacionadas con usuarios locales:

```properties
inventario.local-db-auth.enabled=true
inventario.local-auth.enabled=true
inventario.local-auth.username=admin.local
inventario.local-auth.password=AdminLocal123
```

Variables para busqueda LDAP de usuarios de dominio:

```env
INVENTARIO_LDAP_ENABLED=true
INVENTARIO_LDAP_URL=ldap://10.15.0.41:389
INVENTARIO_LDAP_DOMAIN=podjudsp.local
INVENTARIO_LDAP_BASE_DN=OU=USUARIOS,OU=PODJUDSP,DC=podjudsp,DC=local
INVENTARIO_LDAP_READ_ONLY_USER_DN=CN=lector-inventario,OU=Servicios,DC=podjudsp,DC=local
INVENTARIO_LDAP_READ_ONLY_PASSWORD=CLAVE_REAL_SOLO_EN_SERVIDOR
INVENTARIO_LDAP_USER_SEARCH_BASE=
INVENTARIO_LDAP_USER_SEARCH_FILTER=(&(objectClass=user)(!(objectClass=computer)))
INVENTARIO_LDAP_USER_SEARCH_LIMIT=50
```

## 2026-08-30 - Separacion visual y Sprint de Equipos

Se separo mejor el alta local de la autorizacion AD. Esto preparo el terreno para avanzar
con el primer modulo funcional sin mezclar conceptos de seguridad.

El modulo elegido fue `EQUIPOS`, porque es el corazon del inventario viejo y alimenta
otros flujos: dashboard, tareas, reportes, mapas, stock asignado y actas.

Primer alcance implementado:

- Migracion Flyway para tabla `equipos`.
- API `GET /api/v1/equipos`.
- API `GET /api/v1/equipos/{id}`.
- API `POST /api/v1/equipos/inventario`.
- Pantalla `/admin/equipos`.
- Busqueda por equipo, usuario o fuero.
- Tests de controlador y pantalla.

El modulo quedo protegido por permisos como `EQUIPOS:VER` y `EQUIPOS:EDITAR`.

Endpoints del modulo:

```text
GET  /api/v1/equipos
GET  /api/v1/equipos/{id}
POST /api/v1/equipos/inventario
GET  /scripts/windows/inventario-modular.ps1
GET  /scripts/windows/inventario-modular.ps1.sha256
```

Comando de pruebas del modulo:

```powershell
mvn "-Dtest=EquipoControllerTests,EquipoPageControllerTests,AdminControllerTests" test
```

URL de pantalla:

```text
http://localhost:8081/admin/equipos
```

## 2026-08-30 - Login visual propio

Se detecto un bucle en `/login`:

```text
GET /login -> 302 Location: /login
```

El problema era que la pantalla de login no estaba servida como vista propia del proyecto.

Solucion aplicada:

- Se agrego `LoginController`.
- Se creo `templates/login.html`.
- Se configuro Spring Security con `.loginPage("/login")`.
- Se agrego prueba de regresion para confirmar que `/login` responde `200`.

Resultado:

- Login propio disponible.
- Formulario con usuario, clave y CSRF.
- Acceso correcto a `/admin`, `/admin/usuarios`, `/admin/equipos` y APIs de usuario.

Comandos y verificaciones usadas:

```powershell
.\mvnw.cmd --batch-mode test
```

```text
GET /login -> 200
POST /login admin.local/AdminLocal123 -> 302 /admin
GET /admin -> 200
GET /admin/usuarios -> 200
GET /admin/equipos -> 200
GET /api/v1/me -> 200
GET /api/v1/me/modulos -> 200
GET /api/v1/equipos -> 200
```

## 2026-08-30 - Deteccion de modo local y trabajo

Se agrego una indicacion operativa para saber en que modo esta corriendo el sistema.

La pantalla `/admin` informa:

- `TRABAJO`: Active Directory disponible y MySQL remoto.
- `LOCAL`: Active Directory apagado/no disponible o base local/fallback.

Esto ayuda a evitar confusiones entre pruebas de casa, laboratorio y entorno de trabajo.

URLs donde se ve el modo activo:

```text
http://localhost:8081/admin
http://localhost:8081/admin/usuarios
```

## 2026-08-30 - Script Windows de inventario

Se creo el primer script Windows de inventario:

```text
src/main/resources/static/scripts/windows/inventario-modular.ps1
```

El script captura datos basicos de una PC y los envia al endpoint:

```text
POST /api/v1/equipos/inventario
```

Datos capturados:

- Nombre de PC.
- Ultimo usuario.
- Fuero opcional.
- IP.
- Sistema operativo.
- Procesador.
- RAM.
- Discos.
- Motherboard.
- Monitores.
- Teclado y mouse.
- Impresora.

La app tambien publica el hash SHA-256 del script para validar que el archivo descargado
coincida con el publicado por el servidor.

Comando local del script con la app en la misma maquina:

```powershell
$u='http://localhost:8081'; $p="$env:TEMP\inventario-modular.ps1"; $h=(iwr "$u/scripts/windows/inventario-modular.ps1.sha256" -UseBasicParsing).Content.Trim(); iwr "$u/scripts/windows/inventario-modular.ps1" -UseBasicParsing -OutFile $p; $sha=[System.Security.Cryptography.SHA256]::Create(); $fs=[System.IO.File]::OpenRead($p); try{$a=([BitConverter]::ToString($sha.ComputeHash($fs))).Replace('-','').ToLowerInvariant()}finally{$fs.Close()}; if($a -ne $h){throw "SHA-256 invalido. Script descargado no coincide con el publicado por el servidor."}; powershell -ExecutionPolicy Bypass -NoProfile -File $p -ServerUrl "$u/api/v1/equipos/inventario"
```

Comando para probar sin enviar datos:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:TEMP\inventario-modular.ps1" -DryRun
```

Variable de token para laboratorio o trabajo, segun corresponda:

```powershell
$env:INVENTARIO_REPORT_TOKEN = "TOKEN_REAL_DE_REPORTE"
```

## 2026-08-30 - Comando copiable desde el login

La pantalla `/login` se amplio para mostrar un comando PowerShell listo para copiar.

Ese comando:

- Toma automaticamente la IP y puerto desde donde se abrio el login.
- Descarga el hash SHA-256.
- Descarga el script.
- Calcula el hash local.
- Ejecuta el script solo si el hash coincide.
- Usa `ExecutionPolicy Bypass` solo para ese proceso.

Esto facilita ejecutar el inventario desde una PC de la red sin instalar servicios ni
modificar configuraciones permanentes de Windows.

Comando copiable usando IP LAN de ejemplo:

```powershell
$u='http://192.168.1.8:8081'; $p="$env:TEMP\inventario-modular.ps1"; $h=(iwr "$u/scripts/windows/inventario-modular.ps1.sha256" -UseBasicParsing).Content.Trim(); iwr "$u/scripts/windows/inventario-modular.ps1" -UseBasicParsing -OutFile $p; $sha=[System.Security.Cryptography.SHA256]::Create(); $fs=[System.IO.File]::OpenRead($p); try{$a=([BitConverter]::ToString($sha.ComputeHash($fs))).Replace('-','').ToLowerInvariant()}finally{$fs.Close()}; if($a -ne $h){throw "SHA-256 invalido. Script descargado no coincide con el publicado por el servidor."}; powershell -ExecutionPolicy Bypass -NoProfile -File $p -ServerUrl "$u/api/v1/equipos/inventario"
```

Comando con fuero explicito:

```powershell
powershell -ExecutionPolicy Bypass -NoProfile -File "$env:TEMP\inventario-modular.ps1" -Fuero "Dpto. Informatica San Pedro"
```

## 2026-08-31 - Busqueda de usuarios de dominio

Se implemento la busqueda de usuarios de Active Directory para autorizacion desde
`/admin/usuarios`.

La pantalla no carga todo el dominio al abrir. Primero pide una busqueda de al menos dos
caracteres y luego consulta LDAP.

Objetivo:

- Buscar por usuario, nombre o apellido.
- Seleccionar una cuenta del dominio.
- Autorizarla localmente en MySQL.
- Asignarle rol.
- No guardar clave de dominio.

Este flujo deja mas clara la administracion real: Inventario Modular no crea usuarios AD,
solo autoriza identidades que ya existen.

URL de busqueda/autorizacion:

```text
http://IP_DEL_SERVIDOR:8081/admin/usuarios
```

Comando HTTP de diagnostico desde Ubuntu:

```bash
curl -s 'http://127.0.0.1:8081/api/v1/usuarios/dominio?q=gmurad'
```

Nota: este endpoint exige sesion autenticada con permiso de administrar usuarios, por eso
con `curl` directo puede redirigir al login. La prueba funcional principal es entrar con
`admin.local`, abrir `/admin/usuarios`, buscar un usuario AD y autorizarlo.

## 2026-08-31 - Incidente de busqueda LDAP incompleta

En produccion se detecto que la seccion de usuarios de dominio mostraba:

```text
No disponible
No se pudo consultar Active Directory.
```

Causa:

- LDAP estaba habilitado.
- Faltaba cuenta lectora configurada.
- Active Directory rechazaba la consulta anonima.

Correccion:

- Configurar cuenta lectora LDAP en `/etc/inventario-modular/inventario-modular.env`.
- Buscar usuarios AD bajo demanda.
- Ordenar la seccion de usuarios de dominio arriba de la pantalla.

Resultado validado el 31 de agosto de 2026:

- Desde `admin.local` se pudo buscar usuarios de dominio.
- Active Directory devolvio resultados.
- Desde cada fila se pudo seleccionar usuario, asignar rol y autorizarlo en MySQL.

Comandos para revisar variables sin imprimir secretos completos:

```bash
sudo grep -E '^(SPRING_PROFILES_ACTIVE|INVENTARIO_SERVER_PORT|INVENTARIO_DB_PRIMARY_URL|INVENTARIO_DB_URL|INVENTARIO_DB_PRIMARY_USER|INVENTARIO_DB_USER|INVENTARIO_LDAP_ENABLED|INVENTARIO_LDAP_URL|INVENTARIO_LDAP_DOMAIN|INVENTARIO_LDAP_BASE_DN|INVENTARIO_LDAP_READ_ONLY_USER_DN)=' /etc/inventario-modular/inventario-modular.env
sudo grep -E '^(INVENTARIO_DB_PRIMARY_PASSWORD|INVENTARIO_DB_PASSWORD|INVENTARIO_LDAP_READ_ONLY_PASSWORD|INVENTARIO_REPORT_TOKEN)=' /etc/inventario-modular/inventario-modular.env | sed 's/=.*/=********/'
```

Comandos de actualizacion y reinicio:

```bash
cd /opt/inventario-modular
git fetch origin
git checkout primeros-pasos
git pull --ff-only origin primeros-pasos
sh ./mvnw --batch-mode test
sh ./mvnw --batch-mode -DskipTests package
sudo systemctl restart inventario-modular.service
systemctl status inventario-modular.service --no-pager -l
sudo journalctl -u inventario-modular.service -n 120 --no-pager
```

## 2026-08-31 - Ajuste de ejecucion del script

Se ajusto el comando de ejecucion del script de inventario para usar bypass local de
PowerShell:

```text
ExecutionPolicy Bypass
```

La aclaracion operativa es importante: no se cambia la politica permanente de Windows. El
bypass aplica solo al proceso que ejecuta el script despues de validar SHA-256.

Comando final recomendado desde una PC cliente:

```powershell
$u='http://IP_DEL_SERVIDOR:8081'; $p="$env:TEMP\inventario-modular.ps1"; $h=(iwr "$u/scripts/windows/inventario-modular.ps1.sha256" -UseBasicParsing).Content.Trim(); iwr "$u/scripts/windows/inventario-modular.ps1" -UseBasicParsing -OutFile $p; $sha=[System.Security.Cryptography.SHA256]::Create(); $fs=[System.IO.File]::OpenRead($p); try{$a=([BitConverter]::ToString($sha.ComputeHash($fs))).Replace('-','').ToLowerInvariant()}finally{$fs.Close()}; if($a -ne $h){throw "SHA-256 invalido. Script descargado no coincide con el publicado por el servidor."}; powershell -ExecutionPolicy Bypass -NoProfile -File $p -ServerUrl "$u/api/v1/equipos/inventario"
```

Comando si se necesita pasar token de reporte:

```powershell
$env:INVENTARIO_REPORT_TOKEN = "TOKEN_REAL_DE_REPORTE"
$u='http://IP_DEL_SERVIDOR:8081'; $p="$env:TEMP\inventario-modular.ps1"; $h=(iwr "$u/scripts/windows/inventario-modular.ps1.sha256" -UseBasicParsing).Content.Trim(); iwr "$u/scripts/windows/inventario-modular.ps1" -UseBasicParsing -OutFile $p; $sha=[System.Security.Cryptography.SHA256]::Create(); $fs=[System.IO.File]::OpenRead($p); try{$a=([BitConverter]::ToString($sha.ComputeHash($fs))).Replace('-','').ToLowerInvariant()}finally{$fs.Close()}; if($a -ne $h){throw "SHA-256 invalido. Script descargado no coincide con el publicado por el servidor."}; powershell -ExecutionPolicy Bypass -NoProfile -File $p -ServerUrl "$u/api/v1/equipos/inventario"
```

## 2026-08-31 - Cierre funcional inicial de Equipos

Se completo el primer cierre funcional del modulo `EQUIPOS` sobre MySQL local.

Acciones realizadas:

- Se agrego actualizacion manual por API con `PUT /api/v1/equipos/{id}`.
- Se agrego formulario de edicion manual en `/admin/equipos/{id}`.
- La edicion requiere permiso `EQUIPOS:EDITAR`.
- Se puede completar hardware, software, perifericos, fuero, usuario, IP y estado activo.
- El nombre del equipo se normaliza a mayusculas y se valida que no se duplique.
- Se permite activar o desactivar equipos sin borrar historial.
- Se conserva `monitoreo` como estado de reporte del script, separado del campo `activo`.
- Se agregaron pruebas de API, pantalla, permisos y duplicados.

Comando de prueba enfocado:

```powershell
.\mvnw.cmd "-Dtest=EquipoControllerTests,EquipoPageControllerTests" test
```

Resultado:

```text
Tests run: 20, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

## 2026-08-31 - Decision de componentes y gemelo digital

Se aclaro el sentido operativo del gemelo digital. La idea no es solamente mostrar una
ficha de hardware: el script reporta caracteristicas de los equipos, stock entrega
componentes, el tecnico arma una orden de armado y el sistema compara lo esperado contra
lo que llego, se instalo o fue detectado.

Decision tomada:

```text
Seguir con COMPONENTES + GEMELO DIGITAL DEL EQUIPO.
```

Primera implementacion:

- Tabla `componentes`.
- Tipos de componente: RAM, DISCO, MOTHERBOARD, MONITOR, TECLADO, MOUSE, IMPRESORA, CPU,
  FUENTE, GABINETE y OTRO.
- Origen del dato: SCRIPT, RELEVAMIENTO_INICIAL, STOCK, ORDEN_ARMADO o MANUAL.
- Estado de comparacion: DETECTADO, ESPERADO, COINCIDE, FALTA, SOBRA o REVISAR.
- API para listar componentes por equipo.
- API para crear componentes asociados a un equipo.
- API para actualizar componentes.
- Seccion visual `Gemelo digital / Componentes` en `/admin/equipos/{id}`.
- Formulario para cargar componentes desde el detalle del equipo.

Comando de prueba enfocado:

```powershell
.\mvnw.cmd "-Dtest=ComponenteControllerTests,EquipoPageControllerTests,EquipoControllerTests" test
```

Resultado:

```text
Tests run: 26, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

## 2026-08-31 - Script alimenta componentes detectados

Se confirmo el proceso de trabajo para el gemelo digital:

```text
1. Completar COMPONENTES para que el script pueda guardar piezas detectadas.
2. Agregar RELEVAMIENTO_INICIAL como origen de componentes detectados en maquinas viejas.
3. Crear STOCK para cargar componentes sueltos nuevos.
4. Crear ORDENES_ARMADO.
5. Crear pantalla de comparacion del gemelo digital.
```

Acciones realizadas:

- El endpoint `POST /api/v1/equipos/inventario` ahora actualiza el equipo y registra sus
  componentes detectados.
- El endpoint heredado `POST /submit_inventory` tambien registra componentes detectados.
- Los componentes que vienen del script quedan con `origen = SCRIPT` y
  `estado_comparacion = DETECTADO`.
- Si el mismo equipo reporta de nuevo, se reemplazan los componentes anteriores de origen
  `SCRIPT` para no duplicar lecturas viejas.
- No se borran componentes de origen `RELEVAMIENTO_INICIAL`, `STOCK`, `ORDEN_ARMADO` o
  `MANUAL`.
- Se agrego el origen `RELEVAMIENTO_INICIAL` para representar la base de una maquina
  vieja cuando se empieza el inventario.

Componentes detectados por el script en esta etapa:

- CPU.
- RAM.
- Discos.
- Motherboard.
- Monitores.
- Teclado.
- Mouse.
- Impresora.

Flujo para PC vieja:

```text
Ejecutar script en la PC existente
-> Inventario Modular actualiza EQUIPOS
-> Inventario Modular guarda componentes SCRIPT
-> Tecnico revisa el detalle del equipo
-> Tecnico consolida o carga base como RELEVAMIENTO_INICIAL
-> Esa base queda como primer gemelo digital de la PC vieja
```

Flujo para PC nueva:

```text
Cargar componentes sueltos en STOCK
-> Crear ORDEN_ARMADO para el equipo nuevo
-> Asignar componentes esperados al gemelo digital
-> Formatear/entregar la PC
-> Usuario inicia sesion y se ejecuta el script
-> Comparar esperado contra detectado
```

Comando de prueba enfocado:

```powershell
.\mvnw.cmd "-Dtest=EquipoControllerTests,ComponenteControllerTests,EquipoPageControllerTests" test
```

## 2026-08-31 - Stock, ordenes de armado y comparacion inicial

Se genero una primera version funcional de los pasos que venian despues de
`COMPONENTES`:

- Modulo `STOCK` para cargar componentes sueltos nuevos.
- Modulo `ORDENES_ARMADO` para planificar equipos nuevos o mejoras.
- Comparacion del gemelo digital integrada al detalle del equipo.

Acciones realizadas:

- Se agrego la migracion `V6__stock_ordenes_armado_comparacion.sql`.
- Se creo la tabla `stock_componentes`.
- Se creo la tabla `ordenes_armado`.
- Se creo la tabla `orden_armado_componentes`.
- Se agrego el modulo `ORDENES_ARMADO` a seguridad modular.
- Se crearon endpoints para cargar y listar componentes de stock.
- Se crearon endpoints para crear ordenes de armado y agregar componentes esperados.
- Cuando una orden usa un componente de stock, el stock queda `RESERVADO`.
- El componente esperado se guarda tambien en `componentes` con `origen = ORDEN_ARMADO`
  y `estado_comparacion = ESPERADO`.
- Se creo el endpoint de comparacion del gemelo digital.
- Se agrego la seccion `Comparacion del gemelo digital` en `/admin/equipos/{id}`.

Endpoints nuevos:

```text
GET  /api/v1/stock/componentes
POST /api/v1/stock/componentes
GET  /api/v1/equipos/{equipoId}/ordenes-armado
POST /api/v1/equipos/{equipoId}/ordenes-armado
POST /api/v1/ordenes-armado/{ordenId}/componentes
GET  /api/v1/equipos/{equipoId}/gemelo-digital/comparacion
```

Regla inicial de comparacion:

```text
Esperado  -> ORDEN_ARMADO, STOCK o estado ESPERADO.
Detectado -> SCRIPT o RELEVAMIENTO_INICIAL.
COINCIDE  -> mismo tipo y mismo serial; sin serial, modelo/capacidad/descripcion.
FALTA     -> estaba esperado pero no aparece detectado.
SOBRA     -> aparece detectado pero no estaba esperado.
```

Comando de prueba enfocado:

```powershell
.\mvnw.cmd "-Dtest=EquipoControllerTests,ComponenteControllerTests,EquipoPageControllerTests,StockOrdenArmadoControllerTests,CurrentUserControllerTests" test
```

Resultado:

```text
Tests run: 30, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

Comando de suite completa:

```powershell
.\mvnw.cmd --batch-mode test
```

Resultado:

```text
Tests run: 75, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

## 2026-08-31 - Pantallas visuales de Stock y Ordenes de Armado

Se agregaron pantallas web dedicadas para que el flujo no dependa solo de API:

```text
/admin/stock
/admin/ordenes-armado
```

Acciones realizadas:

- El panel `/admin` muestra accesos a `Stock` y `Ordenes` segun permisos.
- `/admin/stock` lista componentes sueltos y permite cargar componentes nuevos.
- `/admin/ordenes-armado` permite seleccionar equipo, ver ordenes, crear ordenes y cargar
  componentes esperados.
- Desde la pantalla de ordenes se puede reservar un componente disponible de stock.
- El componente reservado queda como esperado en el gemelo digital del equipo.
- Desde ordenes se puede abrir el detalle del equipo para revisar la comparacion.

Comando de prueba enfocado:

```powershell
.\mvnw.cmd "-Dtest=AdminControllerTests,StockOrdenArmadoPageControllerTests,StockOrdenArmadoControllerTests,EquipoPageControllerTests" test
```

Resultado:

```text
Tests run: 17, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

Comando de suite completa luego de agregar pantallas:

```powershell
.\mvnw.cmd --batch-mode test
```

Resultado:

```text
Tests run: 78, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

Comando usado para relanzar servidor con MySQL local:

```powershell
$env:INVENTARIO_DB_PRIMARY_URL='jdbc:mysql://127.0.0.1:3306/inventario_modular'
$env:INVENTARIO_DB_PRIMARY_USER='inventario_local'
$env:INVENTARIO_DB_PRIMARY_PASSWORD='Cambiar_Clave_Local_123!'
.\mvnw.cmd spring-boot:run "-Dspring-boot.run.profiles=local"
```

Resultado de Flyway:

```text
Successfully validated 6 migrations
Current version of schema `inventario_modular`: 6
Schema `inventario_modular` is up to date. No migration necessary.
```

Verificacion autenticada de pantallas:

```powershell
$s = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$login = Invoke-WebRequest -Uri http://localhost:8081/login -WebSession $s -UseBasicParsing
$csrf = [regex]::Match($login.Content, 'name="_csrf" value="([^"]+)"').Groups[1].Value
Invoke-WebRequest -Uri http://localhost:8081/login -Method Post -WebSession $s -Body @{username='admin.local';password='AdminLocal123';_csrf=$csrf} -MaximumRedirection 0 -UseBasicParsing
$stock = Invoke-WebRequest -Uri http://localhost:8081/admin/stock -WebSession $s -UseBasicParsing
$ordenes = Invoke-WebRequest -Uri http://localhost:8081/admin/ordenes-armado -WebSession $s -UseBasicParsing
```

Resultado:

```text
/admin/stock -> 200
/admin/ordenes-armado -> 200
```

## 2026-08-31 - Edicion de stock, ordenes y selector de orden

Se completaron los tres pasos recomendados despues de crear las pantallas:

```text
1. Editar stock cargado.
2. Editar ordenes de armado.
3. Elegir la orden exacta al agregar componentes esperados.
```

Acciones realizadas:

- `/admin/stock` ahora permite editar componentes ya cargados.
- Se pueden corregir tipo, estado, descripcion, marca, modelo, serial, capacidad,
  ubicacion, observaciones y activo.
- `/admin/ordenes-armado` ahora permite editar ordenes existentes.
- Se puede cambiar estado, descripcion y observaciones de cada orden.
- El formulario de componente esperado ya no usa automaticamente la orden mas reciente.
- Ahora se selecciona explicitamente la orden destino antes de agregar el componente al
  gemelo digital.

Comando de prueba enfocado:

```powershell
.\mvnw.cmd "-Dtest=AdminControllerTests,StockOrdenArmadoPageControllerTests,StockOrdenArmadoControllerTests,EquipoPageControllerTests" test
```

Resultado:

```text
Tests run: 19, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

Comando de suite completa:

```powershell
.\mvnw.cmd --batch-mode test
```

Resultado:

```text
Tests run: 80, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

Comando usado para levantar el servidor con MySQL local y aplicar migraciones:

```powershell
$env:INVENTARIO_DB_PRIMARY_URL='jdbc:mysql://127.0.0.1:3306/inventario_modular'
$env:INVENTARIO_DB_PRIMARY_USER='inventario_local'
$env:INVENTARIO_DB_PRIMARY_PASSWORD='Cambiar_Clave_Local_123!'
.\mvnw.cmd spring-boot:run "-Dspring-boot.run.profiles=local"
```

Resultado de Flyway en MySQL local:

```text
Successfully validated 6 migrations
Current version of schema `inventario_modular`: 5
Migrating schema `inventario_modular` to version "6 - stock ordenes armado comparacion"
Successfully applied 1 migration to schema `inventario_modular`, now at version v6
```

Verificacion HTTP:

```powershell
Invoke-WebRequest -Uri http://localhost:8081/api/v1/sistema/estado -UseBasicParsing
Invoke-WebRequest -Uri http://localhost:8081/login -UseBasicParsing
```

Resultado:

```text
/api/v1/sistema/estado -> OPERATIVO
/login -> 200
```

## Comandos rapidos de recuperacion

Estos comandos sirven cuando se trabaja desde otra maquina, otro asistente o una IA sin el
contexto completo.

Clonar el proyecto:

```powershell
git clone https://gitlab.com/gustavoeliasm/inventario-modular.git
cd inventario-modular
git checkout primeros-pasos
```

Ver estado y ultimos commits:

```powershell
git status --short
git log --oneline --decorate --max-count=20
git remote -v
```

Actualizar desde GitLab:

```powershell
git fetch origin
git switch primeros-pasos
git pull --ff-only origin primeros-pasos
```

Ejecutar tests:

```powershell
.\mvnw.cmd --batch-mode test
```

Levantar en casa con H2:

```powershell
.\mvnw.cmd spring-boot:run -Dspring-boot.run.profiles=casa
```

Levantar en local con MySQL:

```powershell
.\mvnw.cmd spring-boot:run -Dspring-boot.run.profiles=local
```

Entrar al panel local:

```text
URL: http://localhost:8081/login
Usuario: admin.local
Clave: AdminLocal123
```

Actualizar en Ubuntu:

```bash
cd /opt/inventario-modular
git fetch origin
git checkout primeros-pasos
git pull --ff-only origin primeros-pasos
sh ./mvnw --batch-mode test
sh ./mvnw --batch-mode -DskipTests package
sudo systemctl restart inventario-modular.service
systemctl status inventario-modular.service --no-pager -l
```

Rollback basico:

```bash
cd /opt/inventario-modular
git log --oneline -5
git checkout COMMIT_ANTERIOR
sh ./mvnw --batch-mode -DskipTests package
sudo systemctl restart inventario-modular.service
```

Importante: no ejecutar rollback contra base de datos sin revisar primero las migraciones
aplicadas por Flyway.

## 2026-08-31 - Consolidacion de relevamiento inicial

Se completo el siguiente paso del modulo `COMPONENTES`: permitir que una lectura real del
script se convierta en la base inicial estable de una PC vieja.

Acciones realizadas:

- Se agrego una accion en `/admin/equipos/{id}` para consolidar la lectura del script.
- Se agrego el endpoint `POST /api/v1/equipos/{equipoId}/componentes/consolidar-relevamiento-inicial`.
- La consolidacion copia componentes activos de origen `SCRIPT`.
- El relevamiento inicial anterior del equipo se reemplaza para evitar duplicados.
- La nueva foto queda con `origen = RELEVAMIENTO_INICIAL` y
  `estado_comparacion = DETECTADO`.
- No se modifican componentes de `STOCK`, `ORDEN_ARMADO` o `MANUAL`.

Comando de prueba enfocado:

```powershell
.\mvnw.cmd "-Dtest=ComponenteControllerTests,EquipoPageControllerTests" test
```

Resultado:

```text
Tests run: 14, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

## 2026-08-31 - Salida real desde stock

Se completo la primera version de salida real desde stock dentro del circuito de ordenes
de armado.

Acciones realizadas:

- La pantalla `/admin/ordenes-armado` muestra los componentes cargados en cada orden.
- Cuando un componente tiene stock asociado en estado `RESERVADO`, se puede confirmar su
  salida real.
- Se agrego el endpoint `POST /api/v1/ordenes-armado/componentes/{ordenComponenteId}/confirmar-salida-stock`.
- La confirmacion cambia el stock de `RESERVADO` a `ASIGNADO`.
- El componente esperado del gemelo digital pasa de `origen = ORDEN_ARMADO` a
  `origen = STOCK`, manteniendo `estado_comparacion = ESPERADO`.
- La comparacion esperado contra detectado sigue usando ese componente como esperado.

Comando de prueba enfocado:

```powershell
.\mvnw.cmd "-Dtest=StockOrdenArmadoControllerTests,StockOrdenArmadoPageControllerTests" test
```

Resultado:

```text
Tests run: 7, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

## 2026-08-31 - Comparacion automatica refinada

Se ajusto la comparacion del gemelo digital para que el resultado sea mas fiel cuando hay
varios componentes del mismo tipo.

Acciones realizadas:

- La comparacion ahora cruza esperado contra detectado de forma uno-a-uno.
- Un componente detectado ya no puede cerrar dos componentes esperados.
- Los seriales se normalizan antes de comparar, evitando diferencias por guiones,
  espacios o mayusculas.
- Si no hay seriales en ambos lados, se usan modelo, descripcion y capacidad como datos
  fuertes de coincidencia.
- Cuando hay datos parecidos pero no seguros, el resultado queda como `REVISAR`.
- Los componentes detectados que no fueron usados en ningun cruce quedan como `SOBRA`.

Comando de prueba enfocado:

```powershell
.\mvnw.cmd "-Dtest=ComponenteControllerTests,StockOrdenArmadoControllerTests,EquipoPageControllerTests" test
```

Resultado:

```text
Tests run: 18, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

## 2026-08-31 - Auditoria transversal de cambios

Se completo la primera version de auditoria transversal para los modulos que ya empiezan
a mover datos operativos del gemelo digital.

Acciones realizadas:

- Se agrego la migracion `V7__auditoria_transversal.sql`.
- Se creo la tabla `auditoria_eventos`.
- Se agrego el modulo `AUDITORIA` a seguridad modular.
- Se habilito permiso inicial para que el rol `ADMINISTRADOR` pueda ver y administrar
  auditoria.
- Se creo el servicio transversal `AuditoriaService`.
- Se registran eventos de creacion, actualizacion, consolidacion y lectura por script en
  `COMPONENTES`.
- Se registran eventos de creacion, actualizacion, reserva y asignacion en `STOCK`.
- Se registran eventos de creacion, actualizacion, agregado de componente y confirmacion
  de salida real en `ORDENES_ARMADO`.
- Se agrego la API `GET /api/v1/auditoria/eventos`.
- Se agrego la pantalla `/admin/auditoria`.
- El panel `/admin` muestra el acceso a `Auditoria` solo si el usuario tiene permiso.

Alcance confirmado:

```text
COMPONENTES -> registra cambios principales del gemelo digital.
STOCK -> registra altas, correcciones, reservas y asignaciones.
ORDENES_ARMADO -> registra cambios de orden y salida real de stock.
AUDITORIA -> permite consultar los ultimos eventos relevantes.
```

Comando de prueba enfocado:

```powershell
.\mvnw.cmd "-Dtest=AuditoriaControllerTests,AdminControllerTests,ComponenteControllerTests,StockOrdenArmadoControllerTests,StockOrdenArmadoPageControllerTests" test
```

Resultado:

```text
Tests run: 21, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

## 2026-09-01 - Dashboard de diferencias

Se completo la primera pantalla transversal para ver diferencias del gemelo digital sin
entrar equipo por equipo.

Acciones realizadas:

- Se agrego resumen transversal en `GemeloDigitalService`.
- Se agrego la API `GET /api/v1/gemelo-digital/dashboard-diferencias`.
- Se agrego la pantalla `/admin/dashboard-diferencias`.
- El panel `/admin` muestra el acceso `Diferencias` si el usuario tiene
  `COMPONENTES:VER`.
- El dashboard cuenta componentes por estado `FALTA`, `SOBRA`, `REVISAR` y `COINCIDE`.
- El dashboard lista equipos con diferencias pendientes.
- Cada equipo listado permite entrar directo a `/admin/equipos/{id}` para revisar el
  detalle del gemelo digital.
- Se agregaron pruebas de API, pantalla, permisos y acceso desde el panel.

Comando de prueba enfocado:

```powershell
.\mvnw.cmd "-Dtest=DashboardDiferenciasControllerTests,AdminControllerTests,ComponenteControllerTests" test
```

Resultado:

```text
Tests run: 14, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

## 2026-09-01 - Correccion de arranque local y filtros del dashboard

Se corrigio una validacion hecha contra el perfil equivocado. El flujo funcional de
componentes, stock, ordenes, auditoria y dashboard debe probarse en Windows con perfil
`local` y MySQL local, no con el perfil `casa`.

Problema:

- Se habia levantado el servidor con `spring-boot.run.profiles=casa`.
- Ese perfil usa H2 de archivo y existe solo como fallback cuando MySQL local todavia no
  esta creado.
- La base operativa esperada para este punto del proyecto es MySQL local en
  `127.0.0.1:3306/inventario_modular`.

Solucion aplicada y validada:

- Se detuvo el servidor que estaba corriendo con H2.
- Se confirmo conectividad a MySQL local en `127.0.0.1:3306`.
- Se levanto el servidor con perfil `local` y variables de MySQL local.
- Flyway valido 7 migraciones y aplico `V7__auditoria_transversal.sql` sobre
  `inventario_modular`.
- Se verifico en `/admin` que la aplicacion informa `MySQL local`.

Comando correcto para levantar en Windows con MySQL local:

```powershell
$env:INVENTARIO_DB_PRIMARY_URL='jdbc:mysql://127.0.0.1:3306/inventario_modular'
$env:INVENTARIO_DB_PRIMARY_USER='inventario_local'
$env:INVENTARIO_DB_PRIMARY_PASSWORD='Cambiar_Clave_Local_123!'
$env:INVENTARIO_LDAP_ENABLED='false'
$env:INVENTARIO_LOCAL_AUTH_ENABLED='true'
$env:INVENTARIO_LOCAL_DB_AUTH_ENABLED='true'
.\mvnw.cmd spring-boot:run "-Dspring-boot.run.profiles=local"
```

Nota: el perfil `casa` con H2 queda solo como respaldo tecnico para una maquina sin MySQL
local listo. No debe usarse como validacion principal de este sprint.

Tambien se completo el siguiente alcance del dashboard:

- Filtro por estado de comparacion.
- Filtro por nombre de equipo.
- Filtro por fuero.
- Los filtros funcionan tanto en la pantalla `/admin/dashboard-diferencias` como en la
  API `/api/v1/gemelo-digital/dashboard-diferencias`.

Verificacion local autenticada contra MySQL:

```text
/admin -> 200, mostrando MySQL local
/admin/ordenes-armado -> 200
/admin/dashboard-diferencias -> 200
/admin/dashboard-diferencias?estado=FALTA&equipo=PC-INF&fuero=Informatica -> 200
```

Comando de prueba enfocado:

```powershell
.\mvnw.cmd "-Dtest=DashboardDiferenciasControllerTests,AdminControllerTests,StockOrdenArmadoPageControllerTests" test
```

Resultado:

```text
Tests run: 13, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

## 2026-09-01 - Modulo Tareas Tecnicas

Se agrego la primera version del modulo `TAREAS` para registrar trabajo operativo del
equipo de Informatica. El alcance inicial es deliberadamente chico: alta de tareas,
listado con filtros, cambio de estado y asociacion opcional con un equipo.

Archivos principales:

- `src/main/resources/db/migration/V8__tareas_tecnicas.sql`
- `src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/tareas/`
- `src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/web/TareaTecnicaController.java`
- `src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/web/TareaTecnicaPageController.java`
- `src/main/resources/templates/admin/tareas.html`
- `docs/inventario-modular/modulo-tareas-tecnicas.md`

Rutas agregadas:

```text
/admin/tareas
GET   /api/v1/tareas-tecnicas
POST  /api/v1/tareas-tecnicas
PATCH /api/v1/tareas-tecnicas/{id}/estado
```

Verificacion local:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
.\mvnw.cmd --batch-mode "-Dtest=TareaTecnicaControllerTests,TareaTecnicaPageControllerTests" test
.\mvnw.cmd --batch-mode test
.\mvnw.cmd --batch-mode -DskipTests package
.\mvnw.cmd spring-boot:run "-Dspring-boot.run.profiles=casa"
```

Resultado:

```text
Tests run: 96, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
target/inventario-modular-0.0.1-SNAPSHOT.jar generado correctamente
```

Verificacion HTTP local:

```powershell
Invoke-WebRequest -UseBasicParsing -Method Head http://localhost:8081/login
Invoke-WebRequest -UseBasicParsing http://localhost:8081/api/v1/sistema/estado
```

Resultado observado:

```text
/login -> 200 OK
/api/v1/sistema/estado -> 200 OK, estado OPERATIVO
/admin/tareas -> 302 hacia login cuando no hay sesion, esperado por seguridad
```

### Comandos para subir el cambio desde Windows

Ejecutar despues de revisar el diff y confirmar que la rama esta lista:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
git status --short --branch
git add README.md docs/inventario-modular/README.md docs/inventario-modular/proximo-paso-funcional.md docs/inventario-modular/bitacora-del-proyecto.md docs/inventario-modular/modulo-tareas-tecnicas.md src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/tareas src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/web/TareaTecnicaController.java src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/web/TareaTecnicaPageController.java src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/web/AdminController.java src/main/resources/db/migration/V8__tareas_tecnicas.sql src/main/resources/db/casa/data-h2.sql src/main/resources/db/casa/schema-h2.sql src/main/resources/static/css/admin.css src/main/resources/templates/admin/index.html src/main/resources/templates/admin/tareas.html src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/CurrentUserControllerTests.java src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/TareaTecnicaControllerTests.java src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/TareaTecnicaPageControllerTests.java src/test/resources/sql/limpiar-seguridad-modular-test.sql src/test/resources/sql/seguridad-modular-test.sql
git diff --staged --check
git commit -m "feat: agregar modulo de tareas tecnicas"
git push -u origin codex/modulo-tareas-tecnicas
git push -u github codex/modulo-tareas-tecnicas
```

Despues de mergear a `primeros-pasos` en GitLab, sincronizar tambien GitHub:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
git switch primeros-pasos
git pull --ff-only origin primeros-pasos
git push github primeros-pasos
```

### Comandos para actualizar Ubuntu por PuTTY

Inventario Modular en produccion usa `/opt/inventario-modular`, el servicio
`inventario-modular.service`, puerto `8081`, y MySQL remoto `10.15.0.62`. No usar
`/opt/inventario`, `deploy_ubuntu.sh` ni `inventario.service`, porque pertenecen al Flask
legado.

Primero confirmar estado y que el servidor esta parado en el repo correcto:

```bash
cd /opt/inventario-modular
pwd
git remote -v
git branch --show-current
git status --short
git log -1 --oneline
```

Ver que cambios entrarian desde GitLab:

```bash
git fetch origin
git log --oneline HEAD..origin/primeros-pasos
git diff --name-only HEAD..origin/primeros-pasos
```

Si aparece `src/main/resources/db/migration/V8__tareas_tecnicas.sql`, hacer backup antes
de reiniciar porque Flyway aplicara una migracion nueva sobre MySQL.

Backup compatible con el usuario limitado de aplicacion:

```bash
sudo bash -c '
set -euo pipefail
source /etc/inventario-modular/inventario-modular.env

DB_URL="${INVENTARIO_DB_URL:-${INVENTARIO_DB_PRIMARY_URL:-}}"
DB_USER="${INVENTARIO_DB_USER:-${INVENTARIO_DB_PRIMARY_USER:-}}"
DB_PASS="${INVENTARIO_DB_PASSWORD:-${INVENTARIO_DB_PRIMARY_PASSWORD:-}}"

DB_HOST=$(echo "$DB_URL" | sed -E "s#^jdbc:mysql://([^:/]+).*#\1#")
DB_NAME=$(echo "$DB_URL" | sed -E "s#^jdbc:mysql://[^/]+/([^?]+).*#\1#")

BACKUP_DIR="/opt/backups/inventario-modular"
mkdir -p "$BACKUP_DIR"
BACKUP="$BACKUP_DIR/${DB_NAME}_$(date +%Y%m%d_%H%M%S).sql.gz"

mysqldump --single-transaction --skip-lock-tables --no-tablespaces \
  -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" | gzip > "$BACKUP"

gzip -t "$BACKUP"
ls -lh "$BACKUP"
'
```

Actualizar codigo:

```bash
cd /opt/inventario-modular
git pull --ff-only origin primeros-pasos
git log -1 --oneline
```

Compilar y generar `.jar`:

```bash
cd /opt/inventario-modular
sh ./mvnw --batch-mode test
sh ./mvnw --batch-mode -DskipTests package
ls -lh target/*.jar
```

Reiniciar solo el servicio modular:

```bash
sudo systemctl restart inventario-modular.service
systemctl status inventario-modular.service --no-pager -l
sudo journalctl -u inventario-modular.service -n 160 --no-pager
```

Verificar aplicacion y migracion:

```bash
curl -I http://127.0.0.1:8081
curl -s http://127.0.0.1:8081/api/v1/sistema/estado

sudo bash -c '
set -euo pipefail
source /etc/inventario-modular/inventario-modular.env

DB_URL="${INVENTARIO_DB_URL:-${INVENTARIO_DB_PRIMARY_URL:-}}"
DB_USER="${INVENTARIO_DB_USER:-${INVENTARIO_DB_PRIMARY_USER:-}}"
DB_PASS="${INVENTARIO_DB_PASSWORD:-${INVENTARIO_DB_PRIMARY_PASSWORD:-}}"
DB_HOST=$(echo "$DB_URL" | sed -E "s#^jdbc:mysql://([^:/]+).*#\1#")
DB_NAME=$(echo "$DB_URL" | sed -E "s#^jdbc:mysql://[^/]+/([^?]+).*#\1#")

mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" \
  -e "SELECT version, description, success FROM flyway_schema_history ORDER BY installed_rank DESC LIMIT 5; SHOW TABLES LIKE '\''tareas_tecnicas'\'';"
'
```

Verificacion esperada:

```text
HTTP/1.1 302
Location: http://127.0.0.1:8081/admin
Flyway muestra V8 aplicada con success=1
SHOW TABLES LIKE 'tareas_tecnicas' devuelve la tabla
```

Pendientes del modulo:

- Editar titulo, descripcion, prioridad y responsable de tareas existentes.
- Comentarios o novedades por tarea.
- Vistas por responsable y fuero.
- Exportacion CSV.

## 2026-09-01 - Modulos Muebles, Patrimonio y Reportes

Se avanzaron tres modulos verticales de alcance acotado para sumar valor operativo sin
esperar al modulo de actas.

Acciones realizadas:

- Se agrego la migracion `V9__muebles_patrimonio_reportes.sql`.
- Se creo la tabla `muebles`.
- Se creo la tabla `bienes_patrimoniales`.
- Se reforzaron permisos para `MUEBLES`, `PATRIMONIO` y `REPORTES`.
- Se agrego API de muebles:
  - `GET /api/v1/muebles`
  - `POST /api/v1/muebles`
  - `PUT /api/v1/muebles/{id}`
- Se agrego API de patrimonio:
  - `GET /api/v1/patrimonio/bienes`
  - `POST /api/v1/patrimonio/bienes`
  - `PUT /api/v1/patrimonio/bienes/{id}`
- Se agrego API de reportes:
  - `GET /api/v1/reportes/resumen`
  - `GET /api/v1/reportes/muebles.csv`
  - `GET /api/v1/reportes/patrimonio.csv`
  - `GET /api/v1/reportes/tareas.csv`
- Se agregaron pantallas:
  - `/admin/muebles`
  - `/admin/patrimonio`
  - `/admin/reportes`
- El panel `/admin` ahora muestra accesos a Muebles, Patrimonio y Reportes segun permiso.
- Se agregaron pruebas de API, pantalla y permisos.

Comando de prueba enfocado:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
.\mvnw.cmd --batch-mode "-Dtest=MuebleControllerTests,MueblePageControllerTests,PatrimonioControllerTests,PatrimonioPageControllerTests,ReporteControllerTests,ReportePageControllerTests,CurrentUserControllerTests" test
```

Resultado:

```text
Tests run: 14, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

### Comandos para subir el cambio desde Windows

Ejecutar despues de revisar el diff y confirmar que la rama esta lista:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
git status --short --branch
git add README.md docs/inventario-modular/README.md docs/inventario-modular/proximo-paso-funcional.md docs/inventario-modular/bitacora-del-proyecto.md docs/inventario-modular/modulo-muebles.md docs/inventario-modular/modulo-patrimonio.md docs/inventario-modular/modulo-reportes.md src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/muebles src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/patrimonio src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/reportes src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/web/MuebleController.java src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/web/MueblePageController.java src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/web/PatrimonioController.java src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/web/PatrimonioPageController.java src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/web/ReporteController.java src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/web/ReportePageController.java src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/web/AdminController.java src/main/resources/db/migration/V9__muebles_patrimonio_reportes.sql src/main/resources/db/casa/data-h2.sql src/main/resources/db/casa/schema-h2.sql src/main/resources/templates/admin/index.html src/main/resources/templates/admin/muebles.html src/main/resources/templates/admin/patrimonio.html src/main/resources/templates/admin/reportes.html src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/MuebleControllerTests.java src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/MueblePageControllerTests.java src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/PatrimonioControllerTests.java src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/PatrimonioPageControllerTests.java src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/ReporteControllerTests.java src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/ReportePageControllerTests.java src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/CurrentUserControllerTests.java src/test/resources/sql/limpiar-seguridad-modular-test.sql src/test/resources/sql/seguridad-modular-test.sql
git diff --staged --check
git commit -m "feat: agregar muebles patrimonio y reportes"
git push -u origin codex/modulo-tareas-tecnicas
git push -u github codex/modulo-tareas-tecnicas
```

Despues de mergear a `primeros-pasos` en GitLab, sincronizar tambien GitHub:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
git switch primeros-pasos
git pull --ff-only origin primeros-pasos
git push github primeros-pasos
```

### Comandos para actualizar Ubuntu por PuTTY

Inventario Modular en produccion usa `/opt/inventario-modular`, el servicio
`inventario-modular.service`, puerto `8081`, y MySQL remoto `10.15.0.62`. No usar
`/opt/inventario`, `deploy_ubuntu.sh` ni `inventario.service`, porque pertenecen al Flask
legado.

Confirmar estado del repo correcto:

```bash
cd /opt/inventario-modular
pwd
git remote -v
git branch --show-current
git status --short
git log -1 --oneline
```

Ver que cambios entrarian desde GitLab:

```bash
git fetch origin
git log --oneline HEAD..origin/primeros-pasos
git diff --name-only HEAD..origin/primeros-pasos
```

Si aparece `V8__tareas_tecnicas.sql` o `V9__muebles_patrimonio_reportes.sql`, hacer backup
antes de reiniciar porque Flyway aplicara migraciones nuevas sobre MySQL.

```bash
sudo bash -c '
set -euo pipefail
source /etc/inventario-modular/inventario-modular.env

DB_URL="${INVENTARIO_DB_URL:-${INVENTARIO_DB_PRIMARY_URL:-}}"
DB_USER="${INVENTARIO_DB_USER:-${INVENTARIO_DB_PRIMARY_USER:-}}"
DB_PASS="${INVENTARIO_DB_PASSWORD:-${INVENTARIO_DB_PRIMARY_PASSWORD:-}}"

DB_HOST=$(echo "$DB_URL" | sed -E "s#^jdbc:mysql://([^:/]+).*#\1#")
DB_NAME=$(echo "$DB_URL" | sed -E "s#^jdbc:mysql://[^/]+/([^?]+).*#\1#")

BACKUP_DIR="/opt/backups/inventario-modular"
mkdir -p "$BACKUP_DIR"
BACKUP="$BACKUP_DIR/${DB_NAME}_$(date +%Y%m%d_%H%M%S).sql.gz"

mysqldump --single-transaction --skip-lock-tables --no-tablespaces \
  -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" | gzip > "$BACKUP"

gzip -t "$BACKUP"
ls -lh "$BACKUP"
'
```

Actualizar codigo:

```bash
cd /opt/inventario-modular
git pull --ff-only origin primeros-pasos
git log -1 --oneline
```

Compilar y probar en Ubuntu:

```bash
cd /opt/inventario-modular
sh ./mvnw --batch-mode test
sh ./mvnw --batch-mode -DskipTests package
ls -lh target/*.jar
```

Reiniciar solo el servicio modular:

```bash
sudo systemctl restart inventario-modular.service
systemctl status inventario-modular.service --no-pager -l
sudo journalctl -u inventario-modular.service -n 180 --no-pager
```

Verificar aplicacion y migraciones:

```bash
curl -I http://127.0.0.1:8081
curl -s http://127.0.0.1:8081/api/v1/sistema/estado

sudo bash -c '
set -euo pipefail
source /etc/inventario-modular/inventario-modular.env

DB_URL="${INVENTARIO_DB_URL:-${INVENTARIO_DB_PRIMARY_URL:-}}"
DB_USER="${INVENTARIO_DB_USER:-${INVENTARIO_DB_PRIMARY_USER:-}}"
DB_PASS="${INVENTARIO_DB_PASSWORD:-${INVENTARIO_DB_PRIMARY_PASSWORD:-}}"
DB_HOST=$(echo "$DB_URL" | sed -E "s#^jdbc:mysql://([^:/]+).*#\1#")
DB_NAME=$(echo "$DB_URL" | sed -E "s#^jdbc:mysql://[^/]+/([^?]+).*#\1#")

mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" \
  -e "SELECT version, description, success FROM flyway_schema_history ORDER BY installed_rank DESC LIMIT 8; SHOW TABLES LIKE '\''tareas_tecnicas'\''; SHOW TABLES LIKE '\''muebles'\''; SHOW TABLES LIKE '\''bienes_patrimoniales'\'';"
'
```

Verificacion esperada:

```text
Servicio inventario-modular.service activo
Flyway muestra V8 y V9 aplicadas con success=1
SHOW TABLES devuelve tareas_tecnicas, muebles y bienes_patrimoniales
```

### Publicacion en GitLab y GitHub

El avance quedo commiteado y subido a los dos remotos del proyecto:

```text
Commit: 2341b1d feat: agregar tareas muebles patrimonio y reportes
Rama: codex/modulo-tareas-tecnicas
GitLab: https://gitlab.com/gustavoeliasm/inventario-modular
GitHub: https://github.com/gustavounju/inventario-modular
```

Comandos ejecutados:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
git commit -m "feat: agregar tareas muebles patrimonio y reportes"
git push -u origin codex/modulo-tareas-tecnicas
git push -u github codex/modulo-tareas-tecnicas
git branch --set-upstream-to=origin/codex/modulo-tareas-tecnicas codex/modulo-tareas-tecnicas
```

GitLab propuso crear el Merge Request desde:

```text
https://gitlab.com/gustavoeliasm/inventario-modular/-/merge_requests/new?merge_request%5Bsource_branch%5D=codex%2Fmodulo-tareas-tecnicas
```

Sobre el alcance de esta bitacora: esta completa como relato cronologico del proyecto
desde la creacion del repo y los primeros comandos hasta los modulos actuales. No es un
log linea por linea de cada archivo de codigo; para eso se usa el historial Git. La
bitacora documenta decisiones, hitos, comandos, validaciones, rutas, migraciones y
pendientes principales.

### Diagnostico si no aparecen los modulos nuevos

Si el panel `/admin` muestra solo `Equipos`, `Diferencias`, `Stock`, `Ordenes`,
`Auditoria` y `Usuarios`, la aplicacion esta corriendo con una revision anterior a los
modulos `TAREAS`, `MUEBLES`, `PATRIMONIO` y `REPORTES`.

Verificar en Windows:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
git branch --show-current
git log -3 --oneline --decorate
```

El codigo con los modulos nuevos debe estar en `2f2cdda` o posterior. Si se esta en
`primeros-pasos` antes de integrar la rama, solo apareceran los modulos viejos.

Para probar localmente sin esperar el merge:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
git switch codex/modulo-tareas-tecnicas
.\mvnw.cmd spring-boot:run "-Dspring-boot.run.profiles=casa"
```

### Correccion visual del menu principal

Luego de integrar `TAREAS`, `MUEBLES`, `PATRIMONIO` y `REPORTES`, el menu superior del
panel `/admin` podia salirse de la pantalla en resoluciones chicas o medianas.

Solucion aplicada:

- Se amplio el ancho maximo del panel principal.
- Se habilito `flex-wrap` en el encabezado y en las acciones.
- Se agrego un corte responsive a `900px` para convertir las acciones en grilla.
- Se mantuvo el comportamiento movil existente a `640px`.

Archivo modificado:

```text
src/main/resources/static/css/admin.css
```

Comandos de validacion local:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
.\mvnw.cmd --batch-mode "-Dtest=AdminControllerTests" test
.\mvnw.cmd --batch-mode -DskipTests package
```

Comandos Ubuntu por PuTTY para recibir esta correccion despues de subirla:

```bash
cd /opt/inventario-modular
git fetch origin
git pull --ff-only origin primeros-pasos
sh ./mvnw --batch-mode test
sh ./mvnw --batch-mode -DskipTests package
sudo systemctl restart inventario-modular.service
systemctl status inventario-modular.service --no-pager -l
curl -I http://127.0.0.1:8081/admin
```

### Manual de usuario en PDF

Se genero un primer manual de usuario para explicar el uso operativo actual del sistema.
El documento cubre:

- Ingreso al sistema.
- Alta y control de equipos.
- Alta/autorizacion de usuarios.
- Stock y ordenes de armado.
- Significado del tablero `Diferencias`.
- Tareas tecnicas.
- Muebles, patrimonio y reportes.
- Reglas practicas de seguridad.
- Comandos Ubuntu por PuTTY.

Archivo generado:

```text
output/pdf/manual-usuario-inventario-modular.pdf
```

Comando para regenerarlo desde Windows:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
C:\Users\gmurad\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe docs\inventario-modular\generar_manual_usuario.py
```

Comando usado para renderizar y revisar visualmente el PDF:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
C:\Users\gmurad\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler\Library\bin\pdftoppm.exe -png -r 130 output\pdf\manual-usuario-inventario-modular.pdf tmp\pdfs\manual_usuario_page
```

### Modulos Actas y Ubicaciones

Se avanzo con dos modulos funcionales completos de bajo riesgo operativo:

- `ACTAS`, para registrar constancias de entrega, recepcion, devolucion, traslado, baja u
  otra actuacion interna.
- `UBICACIONES`, para registrar oficinas, depositos, salas y racks donde luego podran
  asignarse equipos, muebles, patrimonio y stock.

Alcance implementado:

- Migracion Flyway `V10__actas_ubicaciones.sql`.
- Entidades, repositorios y servicios para actas y ubicaciones.
- API REST protegida por permisos:

```text
GET  /api/v1/actas
POST /api/v1/actas
PUT  /api/v1/actas/{id}
GET  /api/v1/ubicaciones
POST /api/v1/ubicaciones
PUT  /api/v1/ubicaciones/{id}
```

- Pantallas administrativas:

```text
/admin/actas
/admin/ubicaciones
```

- Alta, listado, filtros y edicion desde pantalla.
- Accesos desde `/admin` condicionados por permisos.
- Auditoria al crear y actualizar registros.
- Conteos en `REPORTES`.
- Exportaciones CSV:

```text
GET /api/v1/reportes/actas.csv
GET /api/v1/reportes/ubicaciones.csv
```

- Seeds de H2 para perfil `casa` y tests.
- Documentacion:
  - `docs/inventario-modular/modulo-actas.md`
  - `docs/inventario-modular/modulo-ubicaciones.md`

Comando de pruebas focalizadas ejecutado:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
.\mvnw.cmd --batch-mode "-Dtest=ActaControllerTests,UbicacionControllerTests,AdminControllerTests,ReporteControllerTests" test
```

Resultado:

```text
Tests run: 12, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

Comando de suite completa ejecutado despues de ajustar la expectativa de modulos en
`CurrentUserControllerTests`:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
.\mvnw.cmd --batch-mode test
```

Resultado:

```text
Tests run: 114, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

Comando de empaquetado ejecutado:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
.\mvnw.cmd --batch-mode -DskipTests package
```

Resultado:

```text
BUILD SUCCESS
```

Smoke local con perfil `casa`:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
.\mvnw.cmd spring-boot:run "-Dspring-boot.run.profiles=casa"
```

Verificacion manual automatizada contra `http://localhost:8081`:

- `/admin` contiene enlaces a `/admin/actas` y `/admin/ubicaciones`.
- `/admin/actas` renderiza `Actas registradas`.
- `/admin/ubicaciones` renderiza `Ubicaciones registradas`.

Comandos para actualizar Ubuntu por PuTTY:

```bash
cd /opt/inventario-modular
git fetch origin
git pull --ff-only origin primeros-pasos
./mvnw --batch-mode test
./mvnw --batch-mode -DskipTests package
sudo systemctl restart inventario-modular.service
systemctl status inventario-modular.service --no-pager -l
curl -s http://127.0.0.1:8081/api/v1/sistema/estado
```

## Estado actual documentado

Al cierre de esta bitacora, Inventario Modular cuenta con:

- Proyecto Spring Boot Java 21.
- Rama `primeros-pasos`.
- GitLab como remoto principal.
- GitHub como espejo manual.
- Pipeline inicial de CI/CD.
- Configuracion local Windows.
- Guia de instalacion Ubuntu por PuTTY.
- Servicio systemd documentado.
- MySQL remoto de trabajo en `10.15.0.62`.
- Login Active Directory solo lectura.
- Modo local/casa sin dominio.
- Autorizacion modular inicial en MySQL.
- Usuarios `AD` y `LOCAL` separados.
- Alta local con clave hasheada BCrypt.
- Busqueda LDAP de usuarios de dominio para autorizacion.
- Panel `/admin`.
- Pantalla `/admin/usuarios`.
- Primer modulo funcional `/admin/equipos`.
- API de equipos.
- Modulo `COMPONENTES` iniciado.
- Seccion de gemelo digital en el detalle del equipo.
- Primera API de `STOCK`.
- Primera API de `ORDENES_ARMADO`.
- Pantalla `/admin/stock`.
- Pantalla `/admin/ordenes-armado`.
- Comparacion inicial del gemelo digital en el detalle del equipo.
- Dashboard de diferencias en `/admin/dashboard-diferencias`.
- API de dashboard en `/api/v1/gemelo-digital/dashboard-diferencias`.
- Filtros de dashboard por estado, equipo y fuero.
- Modulo `AUDITORIA`.
- Tabla `auditoria_eventos`.
- API de eventos recientes en `/api/v1/auditoria/eventos`.
- Filtros de auditoria por usuario, modulo y accion.
- Exportacion CSV de auditoria en `/api/v1/auditoria/eventos.csv`.
- Pantalla `/admin/auditoria`.
- Registro transversal de cambios en componentes, stock y ordenes de armado.
- Modulo `TAREAS`.
- Pantalla `/admin/tareas`.
- API de tareas tecnicas en `/api/v1/tareas-tecnicas`.
- Modulo `MUEBLES`.
- Pantalla `/admin/muebles`.
- API de muebles en `/api/v1/muebles`.
- Modulo `PATRIMONIO`.
- Pantalla `/admin/patrimonio`.
- API de bienes patrimoniales en `/api/v1/patrimonio/bienes`.
- Modulo `REPORTES`.
- Pantalla `/admin/reportes`.
- API de resumen y CSV en `/api/v1/reportes`.
- Modulo `ACTAS`.
- Pantalla `/admin/actas`.
- API de actas en `/api/v1/actas`.
- Exportacion CSV de actas en `/api/v1/reportes/actas.csv`.
- Modulo `UBICACIONES`.
- Pantalla `/admin/ubicaciones`.
- API de ubicaciones en `/api/v1/ubicaciones`.
- Exportacion CSV de ubicaciones en `/api/v1/reportes/ubicaciones.csv`.
- Exportacion CSV del dashboard de diferencias en
  `/api/v1/gemelo-digital/dashboard-diferencias.csv`.
- Script Windows de inventario servido por la app.
- Verificacion SHA-256 del script.
- Documentacion de actualizacion de produccion.

## Pendientes principales

Pendientes de seguridad y usuarios:

- Aplicar bloqueo estricto para usuarios AD no autorizados cuando exista administrador real
  de dominio cargado.
- Editar roles de usuarios existentes desde pantalla.
- Activar o desactivar usuarios desde pantalla.
- Cambiar clave de usuarios locales desde pantalla.
- Auditar altas, cambios de clave, desactivaciones y autorizaciones AD.
- Definir politica operativa de usuarios locales en produccion.

Pendientes del modulo Equipos:

- Conectar el script real con despliegue controlado en equipos de la red.
- Definir token real de reporte fuera de git.
- Importar datos iniciales desde el inventario viejo.
- Relacionar equipos con stock, componentes, ubicaciones y actas.
- Evaluar cola de reenvio automatico para reportes pendientes.

Pendientes del gemelo digital:

- Auditoria especifica de cambios de usuarios, roles y autorizaciones AD.

Pendientes del modulo Tareas:

- Edicion completa de tareas existentes.
- Comentarios/historial por tarea.
- Vistas por responsable y fuero.

Pendientes de muebles, patrimonio y reportes:

- Respuestas HTTP 409 claras para codigos o numeros patrimoniales duplicados.
- Paginacion y filtros avanzados cuando crezca el volumen de datos.
- Reportes administrativos mas completos.

Pendientes de actas y ubicaciones:

- Generar PDF/impresion formal de actas.
- Numeracion automatica de actas por anio o dependencia.
- Usar ubicaciones como selector en equipos, muebles, patrimonio y stock.
- Reportes por ubicacion/fuero.

Pendientes de plataforma:

- Definir reverse proxy/HTTPS para un despliegue real.
- Formalizar rollback con revision de migraciones Flyway.
- Definir despliegue automatico solo cuando el flujo manual este maduro.

## Fuentes internas consultadas

- `README.md`
- `docs/designs/inventario-modular-java.md`
- `docs/inventario-modular/README.md`
- `docs/inventario-modular/cierre-jornada-windows.md`
- `docs/inventario-modular/runbook-manana-ubuntu-putty.md`
- `docs/inventario-modular/proximo-paso-funcional.md`
- `docs/inventario-modular/usuarios-locales-y-active-directory.md`
- `docs/inventario-modular/modulo-equipos.md`
- `docs/inventario-modular/modulo-componentes-gemelo-digital.md`
- `docs/inventario-modular/stock-ordenes-armado-y-comparacion.md`
- `docs/inventario-modular/auditoria-transversal.md`
- `docs/inventario-modular/script-inventario-windows.md`
- `docs/inventario-modular/actualizacion-produccion-inventario-modular.md`
- `docs/inventario-modular/modulo-tareas-tecnicas.md`
- `docs/inventario-modular/modulo-muebles.md`
- `docs/inventario-modular/modulo-patrimonio.md`
- `docs/inventario-modular/modulo-reportes.md`
- `docs/inventario-modular/modulo-actas.md`
- `docs/inventario-modular/modulo-ubicaciones.md`
- `docs/inventario-modular/incidente-login-local-repetido.md`
- `docs/decisions/ADR-002-inventario-modular-api-first.md`
- `docs/decisions/ADR-003-inventario-viejo-como-referencia-funcional.md`
- `docs/decisions/ADR-004-login-active-directory-solo-lectura.md`
- `docs/decisions/ADR-005-modo-local-sin-dominio.md`
- `docs/decisions/ADR-006-autorizacion-modular-inicial.md`
- `docs/decisions/ADR-007-identidades-autenticacion-autorizacion.md`
- `docs/decisions/ADR-008-componentes-y-gemelo-digital-del-equipo.md`
- Historial Git de la rama `primeros-pasos`.
