# Incidente de actualizacion en produccion - Inventario Modular

Fecha: 2026-08-31

## Para la proxima IA o agente

Si el usuario pide actualizar produccion del proyecto `inventario-modular`, leer primero este documento completo.

Resumen de busqueda rapida:

- No usar `/opt/inventario`: ese es el Flask legado.
- Usar `/opt/inventario-modular`: ese es el Java/Spring modular.
- No usar `deploy_ubuntu.sh`: pertenece al Flask legado.
- Servicio correcto: `inventario-modular.service`.
- Puerto directo Spring Boot: `8081`.
- App Ubuntu: `10.15.2.251`.
- MySQL remoto del modular: `10.15.0.62`.
- Base del modular: `inventario_modular`.
- Usuario MySQL del modular: `inventario_modular_app`.
- La clave MySQL esta en `INVENTARIO_DB_PASSWORD`, dentro de `/etc/inventario-modular/inventario-modular.env`.
- El codigo nuevo de `DataSourceConfig.java` espera tambien `INVENTARIO_DATASOURCE_PRIMARY_URL`, `INVENTARIO_DATASOURCE_PRIMARY_USERNAME`, `INVENTARIO_DATASOURCE_PRIMARY_PASSWORD`.
- En casa/desarrollo el sistema puede usar MySQL local; en produccion debe forzar la base remota de `10.15.0.62`.
- Usuario local de emergencia observado por defecto en codigo: `admin.local`. La password por defecto esta en `LocalAuthenticationProperties.java`, pero no debe promoverse como secreto permanente de produccion.
- Despues del primer ingreso local, revisar la pantalla de administracion de usuarios: si el login AD funciona pero el usuario entra sin modulos, hace falta autorizarlo y asignarle roles/modulos.

## Resumen

Durante la actualizacion manual por PuTTY se mezclaron inicialmente dos aplicaciones distintas:

- Sistema Flask legado: `/opt/inventario`, repo `servidorinventario.git`, servicio `inventario.service`.
- Sistema Java/Spring modular: `/opt/inventario-modular`, repo `inventario-modular.git`, servicio `inventario-modular.service`.

Para cambios del proyecto `inventario-modular`, no se debe usar `/opt/inventario` ni `deploy_ubuntu.sh`.

## Estado confirmado del modular

Datos observados en produccion:

- Directorio: `/opt/inventario-modular`
- Repo remoto: `git@gitlab.com:gustavoeliasm/inventario-modular.git`
- Rama activa: `primeros-pasos`
- Servicio systemd: `inventario-modular.service`
- Comando del servicio: `/usr/bin/java -jar /opt/inventario-modular/target/inventario-modular-0.0.1-SNAPSHOT.jar`
- Archivo de entorno: `/etc/inventario-modular/inventario-modular.env`
- Java instalado: OpenJDK 21
- Maven no estaba instalado al inicio del incidente; se instalo con `sudo apt install -y maven`
- Puerto directo de Spring Boot: `8081`

Base configurada en el archivo de entorno:

- URL: `INVENTARIO_DB_URL=jdbc:mysql://10.15.0.62:3306/inventario_modular`
- Usuario: `INVENTARIO_DB_USER=inventario_modular_app`
- Password: `INVENTARIO_DB_PASSWORD`, guardado solo en `/etc/inventario-modular/inventario-modular.env`

No documentar la clave real en el repositorio. Si el administrador necesita verla en el servidor:

```bash
sudo grep '^INVENTARIO_DB_PASSWORD=' /etc/inventario-modular/inventario-modular.env
```

## Problema encontrado con backups

El primer intento de backup fallo por usar host y usuario de ejemplo:

```bash
mysqldump -h 127.0.0.1 -u TU_USUARIO -p inventario_modular
```

Errores observados:

- `Can't connect to MySQL server on '127.0.0.1:3306'`: la base no esta en localhost, esta en `10.15.0.62`.
- `Access denied for user 'inventario_modular_app'@'10.15.2.251'`: password manual incorrecta o distinta de la del servicio.
- Se generaron archivos `.sql.gz` vacios o casi vacios en `/opt/backups/inventario-modular`; no deben considerarse backups validos.

Luego, usando las credenciales del servicio, MySQL acepto el login pero rechazo el dump por permisos limitados:

- Falta privilegio `PROCESS` para tablespaces.
- Falta permiso para `LOCK TABLES`.

Esto es normal para un usuario de aplicacion con privilegios acotados.

## Problema encontrado despues del deploy

Despues de compilar y reiniciar, el servicio `inventario-modular.service` entro en loop de reinicio. El log mostraba:

```text
Base de datos principal (MySQL 10.15.0.62:3306) ALCANZABLE. Conectando a: jdbc:mysql://10.15.0.62:3306/inventario_modular
Fallo el login o establecimiento de sesion en MySQL de produccion (Access denied for user 'inventario_modular_app'@'10.15.2.251' (using password: NO)).
Usando base de datos MySQL local como fallback. Conectando a: jdbc:mysql://127.0.0.1:3306/inventario_modular
```

La prueba manual con las variables del `EnvironmentFile` si funcionaba:

```bash
sudo bash -c '
set -euo pipefail
source /etc/inventario-modular/inventario-modular.env

DB_URL="${INVENTARIO_DB_URL}"
DB_HOST=$(echo "$DB_URL" | sed -E "s#^jdbc:mysql://([^:/]+).*#\1#")
DB_NAME=$(echo "$DB_URL" | sed -E "s#^jdbc:mysql://[^/]+/([^?]+).*#\1#")

mysql -h "$DB_HOST" -u "$INVENTARIO_DB_USER" -p"$INVENTARIO_DB_PASSWORD" "$DB_NAME" \
  -e "SELECT DATABASE(), CURRENT_USER(); SHOW TABLES;"
'
```

Resultado confirmado:

- `DATABASE()`: `inventario_modular`
- `CURRENT_USER()`: `inventario_modular_app@10.15.2.251`
- Tabla existente: `flyway_schema_history`

La causa raiz no era red, host, usuario ni password incorrecta. Era un desajuste de nombres de variables:

- El archivo de entorno tenia `INVENTARIO_DB_URL`, `INVENTARIO_DB_USER`, `INVENTARIO_DB_PASSWORD`.
- `DataSourceConfig.java` esperaba las propiedades Spring `inventario.datasource.primary.url`, `inventario.datasource.primary.username`, `inventario.datasource.primary.password`.
- Por relaxed binding de Spring, esas propiedades se pueden alimentar con variables de entorno `INVENTARIO_DATASOURCE_PRIMARY_URL`, `INVENTARIO_DATASOURCE_PRIMARY_USERNAME`, `INVENTARIO_DATASOURCE_PRIMARY_PASSWORD`.
- Al no existir `INVENTARIO_DATASOURCE_PRIMARY_PASSWORD`, `primaryPassword` quedaba vacio y MySQL reportaba `using password: NO`.

Correccion operativa sin exponer secretos:

```bash
sudo bash -c '
set -euo pipefail
ENV_FILE=/etc/inventario-modular/inventario-modular.env
cp "$ENV_FILE" "$ENV_FILE.bak-$(date +%Y%m%d-%H%M%S)"
source "$ENV_FILE"

grep -q "^INVENTARIO_DATASOURCE_PRIMARY_URL=" "$ENV_FILE" \
  || echo "INVENTARIO_DATASOURCE_PRIMARY_URL=${INVENTARIO_DB_URL}" >> "$ENV_FILE"

grep -q "^INVENTARIO_DATASOURCE_PRIMARY_USERNAME=" "$ENV_FILE" \
  || echo "INVENTARIO_DATASOURCE_PRIMARY_USERNAME=${INVENTARIO_DB_USER}" >> "$ENV_FILE"

grep -q "^INVENTARIO_DATASOURCE_PRIMARY_PASSWORD=" "$ENV_FILE" \
  || echo "INVENTARIO_DATASOURCE_PRIMARY_PASSWORD=${INVENTARIO_DB_PASSWORD}" >> "$ENV_FILE"
'

sudo systemctl reset-failed inventario-modular
sudo systemctl restart inventario-modular
sleep 15
sudo systemctl status inventario-modular --no-pager -l
sudo journalctl -u inventario-modular -n 100 --no-pager
curl -I http://127.0.0.1:8081 || true
```

Resultado final confirmado despues de aplicar la correccion:

```text
HikariPool-1 - Start completed.
Conexion establecida exitosamente a la base de datos principal MySQL.
Database: jdbc:mysql://10.15.0.62:3306/inventario_modular (MySQL 8.0)
Successfully validated 4 migrations
Successfully applied 4 migrations to schema `inventario_modular`, now at version v4
Tomcat started on port 8081 (http) with context path '/'
Started InventarioModularApplication
HTTP/1.1 302
Location: http://127.0.0.1:8081/admin
```

Ese `302` es respuesta valida: la aplicacion esta viva y redirige a `/admin`.

## Hallazgo posterior: usuarios AD sin modulos

Despues del deploy exitoso se ingreso con el usuario local administrador y se observo la pantalla `Administracion de usuarios`.

Estado observado:

- El usuario local `admin.local` aparece como autorizado con rol `ADMINISTRADOR`.
- La seccion `Usuarios de dominio` muestra `No disponible`.
- Mensaje visible: `No se pudo consultar Active Directory`.
- El usuario de dominio del administrador puede iniciar sesion, pero queda en modo lectura o sin modulos asignados porque aun no aparece como usuario autorizado con roles/modulos.

Interpretacion:

- El login AD puede funcionar para autenticar identidad.
- La consulta/listado de usuarios de dominio para administracion no esta disponible o no esta resolviendo correctamente la busqueda LDAP.
- No conviene mostrar un listado completo de usuarios del dominio si el dominio es grande; la experiencia correcta es un buscador.

Requerimiento funcional recomendado:

1. En `Administracion de usuarios`, reemplazar o complementar `Usuarios de dominio` con un buscador de usuarios AD.
2. El buscador debe aceptar username, nombre o apellido y consultar Active Directory bajo demanda.
3. Debe mostrar resultados acotados, por ejemplo 10 a 20 usuarios.
4. Desde cada resultado se debe poder seleccionar el usuario, asignarle rol inicial y modulos/permisos.
5. Despues de guardar, el usuario AD debe aparecer en `Usuarios autorizados`.
6. Desde ese momento, al iniciar sesion con AD, debe ver los modulos asignados.

Comandos utiles para diagnosticar esta parte en produccion:

```bash
cd /opt/inventario-modular

sudo grep -Ei "LDAP|AD_|DOMAIN|BASE_DN|READ_ONLY" /etc/inventario-modular/inventario-modular.env \
  | sed -E 's/=.*/=[OCULTO]/'

sudo journalctl -u inventario-modular -n 150 --no-pager | grep -Ei "ldap|active directory|usuario|domain|denied|error" || true
```

Comandos utiles para confirmar que el usuario AD ya fue creado/autorizado en MySQL:

```bash
sudo bash -c '
source /etc/inventario-modular/inventario-modular.env
mysql -h 10.15.0.62 \
  -u "$INVENTARIO_DB_USER" \
  -p"$INVENTARIO_DB_PASSWORD" \
  inventario_modular \
  -e "SHOW TABLES; SELECT id, username, nombre_visible, origen, activo FROM usuarios_sistema ORDER BY username LIMIT 50;"
'
```

Si los nombres reales de tablas/columnas cambian, revisar las migraciones en:

```bash
ls -1 /opt/inventario-modular/src/main/resources/db/migration/
```

## Backup correcto con usuario limitado

Usar las variables reales del servicio y flags compatibles con permisos limitados:

```bash
sudo bash -c '
set -euo pipefail
source /etc/inventario-modular/inventario-modular.env

DB_URL="${INVENTARIO_DB_URL:-${SPRING_DATASOURCE_URL:-}}"
DB_USER="${INVENTARIO_DB_USER:-${SPRING_DATASOURCE_USERNAME:-}}"
DB_PASS="${INVENTARIO_DB_PASSWORD:-${SPRING_DATASOURCE_PASSWORD:-}}"

DB_HOST=$(echo "$DB_URL" | sed -E "s#^jdbc:mysql://([^:/]+).*#\1#")
DB_NAME=$(echo "$DB_URL" | sed -E "s#^jdbc:mysql://[^/]+/([^?]+).*#\1#")

BACKUP_DIR="/opt/backups/inventario-modular"
mkdir -p "$BACKUP_DIR"

BACKUP="$BACKUP_DIR/${DB_NAME}_$(date +%Y%m%d_%H%M%S).sql.gz"

mysqldump \
  --single-transaction \
  --skip-lock-tables \
  --no-tablespaces \
  -h "$DB_HOST" \
  -u "$DB_USER" \
  -p"$DB_PASS" \
  "$DB_NAME" \
  | gzip > "$BACKUP"

gzip -t "$BACKUP"
ls -lh "$BACKUP"
'
```

El backup solo se considera valido si:

- `mysqldump` termina sin error.
- `gzip -t` termina sin error.
- El archivo resultante tiene un tamano razonable, no 20 bytes ni unos pocos cientos de bytes.

## Flujo correcto de actualizacion

Antes de actualizar:

```bash
cd /opt/inventario-modular
pwd
git remote -v
git branch --show-current
git status --short

git fetch origin
BRANCH=$(git branch --show-current)
git log -1 --oneline
git log --oneline HEAD..origin/$BRANCH
git diff --name-only HEAD..origin/$BRANCH
```

Si hay migraciones Flyway en `src/main/resources/db/migration/`, hacer backup antes de reiniciar.

Actualizar codigo:

```bash
cd /opt/inventario-modular
git pull --ff-only origin primeros-pasos
git log -1 --oneline
```

Compilar:

```bash
sudo apt update
sudo apt install -y maven

cd /opt/inventario-modular
mvn clean package -DskipTests
ls -lh target/*.jar
```

Reiniciar solo el servicio modular:

```bash
sudo systemctl restart inventario-modular
sudo systemctl status inventario-modular --no-pager -l
sudo journalctl -u inventario-modular -n 120 --no-pager
```

Verificar:

```bash
curl -I http://127.0.0.1:8081 || true
curl -I http://10.15.2.251:8081 || true
```

Verificacion esperada:

```text
HTTP/1.1 302
Location: http://127.0.0.1:8081/admin
```

## No hacer

- No correr `deploy_ubuntu.sh` para `inventario-modular`; pertenece al sistema Flask de `/opt/inventario`.
- No reiniciar `inventario.service` para cambios del modular; ese servicio es Flask/Gunicorn.
- No considerar validos backups generados despues de un error de `mysqldump`.
- No escribir credenciales reales en documentos versionados.
