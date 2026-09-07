# Runbook Para Manana: Ubuntu Por PuTTY

Guia para continuar en el trabajo desde el servidor Ubuntu, usando PuTTY/SSH.

## Alcance

Este runbook es para preparar una instalacion de laboratorio/staging del nuevo
Inventario Modular Java en el servidor Ubuntu o en una ubicacion separada autorizada.

No reemplaza el inventario actual. No toca la base `inventario_prod`. No reinicia servicios
existentes.

Dato importante de infraestructura: la base MySQL del trabajo no esta en el mismo servidor
Ubuntu donde va a correr la aplicacion. La base esta en el servidor separado
`10.15.0.62`.
Por eso, en el servidor Ubuntu de la app no se debe asumir `localhost` para MySQL.

## Reglas de seguridad

Antes de ejecutar comandos en PuTTY:

1. Confirmar que se esta en el servidor correcto.
2. Confirmar que no se esta dentro de `/opt/inventario` del sistema actual.
3. Confirmar que no se va a tocar `inventario_prod`.
4. Confirmar que la carpeta nueva sera separada, por ejemplo `/opt/inventario-modular`.
5. Si un comando requiere `sudo`, leerlo completo antes de ejecutarlo.

## Objetivo de manana

Dejar el proyecto clonado desde GitLab en una carpeta nueva y comprobar:

- Que el servidor Ubuntu tiene Java 21 o puede instalarlo.
- Que puede clonar el repositorio GitLab.
- Que puede compilar el proyecto.
- Que puede generar el `.jar`.
- Que se entiende donde se veran los pipelines de CI/CD en GitLab.

No se busca dejarlo en produccion.

## Resumen ejecutivo desde cero

Secuencia completa esperada para manana:

1. Entrar al Ubuntu por PuTTY.
2. Verificar usuario, host y carpeta actual.
3. Crear una carpeta nueva separada: `/opt/inventario-modular`.
4. Clonar desde GitLab la rama `primeros-pasos`.
5. Verificar o instalar Java 21.
6. Compilar con Maven Wrapper.
7. Confirmar conectividad desde el servidor Ubuntu de la app hacia MySQL en `10.15.0.62`.
8. Crear una base MySQL nueva llamada `inventario_modular` en `10.15.0.62`, si el DBA/admin lo autoriza.
9. Crear un usuario MySQL propio para la aplicacion, autorizado desde el servidor Ubuntu de la app.
10. Configurar variables locales sin commitear secretos.
11. Probar el `.jar` solo como laboratorio.
12. Revisar el pipeline de CI/CD en GitLab.

GitHub no es el origen operativo para instalar en Ubuntu. GitHub queda como copia de
seguridad y practica de versionado.

## Estado preparado antes de continuar

Acciones ya verificadas el 2026-08-28:

- Se creo una copia local en Windows en:

```text
C:\Users\gmurad\Documents\ChatGPT\inventario-modular
```

- La copia local quedo en rama `primeros-pasos`.
- Los remotos locales quedaron alineados con la decision del proyecto:

```text
origin -> https://gitlab.com/gustavoeliasm/inventario-modular.git
github -> https://github.com/gustavounju/inventario-modular.git
```

- En Windows se verifico Java 21 con `JAVA_HOME` apuntando temporalmente a:

```text
C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot
```

- Se ejecuto `.\mvnw.cmd --batch-mode test` y termino con `BUILD SUCCESS`.
- Se ejecuto `.\mvnw.cmd --batch-mode -DskipTests package` y genero:

```text
target\inventario-modular-0.0.1-SNAPSHOT.jar
```

- El `.jar` local generado midio aproximadamente 67 MB.
- El estado de Git quedo limpio antes de documentar esta bitacora.

## Aviso permanente sobre CI/CD

Cada vez que durante la instalacion aparezca una oportunidad concreta para revisar,
explicar o mejorar CI/CD, hay que avisarlo antes de seguir. Puntos obligatorios:

- Despues de clonar desde GitLab, revisar `.gitlab-ci.yml`.
- Despues de confirmar el ultimo commit, revisar en GitLab `Build -> Pipelines`.
- Confirmar que las etapas esperadas sean `validar` y `construir`.
- Confirmar que `validar` corre tests y que `construir` genera el `.jar`.
- No agregar secretos ni conexiones a MySQL real en CI sin una politica formal.

## Paso 1: Conectar por PuTTY

Conectarse al servidor Ubuntu usando la sesion habitual de PuTTY.

Al entrar, verificar usuario y host:

```bash
whoami
hostname
pwd
```

Si el usuario no tiene permisos para `sudo`, pedir a un administrador que ejecute los
pasos que crean carpetas en `/opt` o instalan paquetes.

La creacion de base/usuario MySQL probablemente no se hace en este Ubuntu, sino en el
servidor de base `10.15.0.62` o por el DBA/admin responsable de ese servidor.

## Paso 1.1: Confirmar que no se esta tocando el sistema viejo

Antes de crear nada:

```bash
pwd
ls -ld /opt/inventario /opt/inventario-modular 2>/dev/null
```

Regla:

- `/opt/inventario` pertenece al sistema actual.
- `/opt/inventario-modular` sera el nuevo laboratorio Java.
- No ejecutar comandos de prueba dentro de `/opt/inventario`.

## Paso 2: Elegir carpeta separada

La carpeta sugerida para laboratorio es:

```text
/opt/inventario-modular
```

Antes de crearla, verificar que no exista:

```bash
ls -ld /opt/inventario-modular
```

Si no existe, crearla:

```bash
sudo mkdir -p /opt/inventario-modular
sudo chown "$USER":"$USER" /opt/inventario-modular
```

Si ya existe y no se sabe que contiene, no borrarla. Revisar primero:

```bash
ls -la /opt/inventario-modular
```

## Paso 3: Clonar desde GitLab

Entrar a `/opt`:

```bash
cd /opt
```

Clonar la rama `primeros-pasos` desde GitLab:

```bash
git clone --branch primeros-pasos https://gitlab.com/gustavoeliasm/inventario-modular.git inventario-modular
```

Si la carpeta `/opt/inventario-modular` ya fue creada vacia en el paso anterior, usar:

```bash
cd /opt/inventario-modular
git clone --branch primeros-pasos https://gitlab.com/gustavoeliasm/inventario-modular.git .
```

Entrar al proyecto:

```bash
cd /opt/inventario-modular
```

Verificar rama y ultimo commit:

```bash
git status
git log --oneline -5
```

El ultimo commit esperado debe coincidir con el ultimo subido a GitLab.

### Paso 3.1: Acceso SSH a GitLab desde el servidor Ubuntu

Si el clone por HTTPS pide usuario y clave, recordar que GitLab no acepta la clave normal
de la cuenta para operaciones Git por HTTPS. Para el servidor Ubuntu conviene usar SSH con
una clave propia del servidor, o un Personal Access Token si se decide mantener HTTPS.

Accion realizada el 2026-08-28 en `serverinventario`:

- Se confirmo que el servidor podia llegar a `gitlab.com`.
- Se acepto la huella ED25519 de `gitlab.com` en `~/.ssh/known_hosts`.
- El intento `ssh -T git@gitlab.com` fallo con `Permission denied (publickey)`, porque el
  usuario `administrador` todavia no tenia una clave autorizada en GitLab.
- Se genero una clave SSH ED25519 para GitLab en:

```text
~/.ssh/id_ed25519_gitlab
~/.ssh/id_ed25519_gitlab.pub
```

Comando usado:

```bash
ssh-keygen -t ed25519 -C "serverinventario gitlab inventario-modular" -f ~/.ssh/id_ed25519_gitlab
```

La clave publica debe agregarse en GitLab, dentro de **User Settings -> SSH Keys**. La
clave privada `~/.ssh/id_ed25519_gitlab` no debe mostrarse, copiarse al repo ni compartirse.

Despues de agregar la clave publica en GitLab, configurar SSH para que use esa clave con
`gitlab.com`:

```bash
cat > ~/.ssh/config <<'EOF'
Host gitlab.com
  HostName gitlab.com
  User git
  IdentityFile ~/.ssh/id_ed25519_gitlab
  IdentitiesOnly yes
EOF

chmod 600 ~/.ssh/config
ssh -T git@gitlab.com
```

Si GitLab responde con un mensaje de bienvenida, clonar con la URL SSH:

```bash
cd /opt/inventario-modular
git clone --branch primeros-pasos git@gitlab.com:gustavoeliasm/inventario-modular.git .
```

## Paso 4: Verificar Java

Verificar Java:

```bash
java -version
```

Debe ser Java 21.

Si aparece Java 8, Java 11, o el comando no existe, no continuar con despliegue. Primero
hay que instalar o configurar JDK 21 en Ubuntu.

Comando orientativo para Ubuntu/Debian, solo si esta autorizado:

```bash
sudo apt update
sudo apt install -y openjdk-21-jdk
```

Este paso requiere permisos de administrador en Ubuntu.

Verificar de nuevo:

```bash
java -version
```

## Paso 5: Compilar con Maven Wrapper

En Ubuntu se puede usar el Maven Wrapper del proyecto. No hace falta instalar Maven global
si el wrapper descarga Maven correctamente.

Desde:

```bash
cd /opt/inventario-modular
```

Ejecutar tests:

```bash
sh ./mvnw --batch-mode test
```

Construir el `.jar`:

```bash
sh ./mvnw --batch-mode -DskipTests package
```

Salida esperada:

```text
BUILD SUCCESS
```

Artefacto esperado:

```text
target/inventario-modular-0.0.1-SNAPSHOT.jar
```

Si el wrapper falla por permisos de ejecucion, usar siempre `sh ./mvnw ...` como esta
documentado. No hace falta ejecutar `chmod +x` para esta prueba.

## Paso 6: Base de datos

La base definida para el nuevo sistema es:

```text
inventario_modular
```

Importante:

- No usar `inventario_prod`.
- No modificar tablas del inventario actual.
- No correr migraciones contra `10.15.0.62` sin autorizacion.
- No asumir que MySQL esta en `localhost`; para el trabajo la base esta en `10.15.0.62`.

### Paso 6.0: Confirmar conectividad hacia `10.15.0.62`

Desde el servidor Ubuntu de la aplicacion:

```bash
ping -c 4 10.15.0.62
```

Luego probar el puerto MySQL:

```bash
nc -vz 10.15.0.62 3306
```

Si `nc` no esta instalado, usar esta prueba alternativa:

```bash
timeout 5 bash -c '</dev/tcp/10.15.0.62/3306' && echo "MySQL alcanzable" || echo "No conecta"
```

Si no conecta, no seguir con la prueba de la app. Hay que confirmar con el administrador:

- Confirmacion de que `10.15.0.62` es la IP correcta del servidor MySQL.
- Puerto MySQL, normalmente `3306`.
- Firewall entre el servidor Ubuntu de la app y `10.15.0.62`.
- Usuario MySQL permitido desde la IP del servidor Ubuntu de la app.

### Paso 6.1: Crear la base en el servidor correcto

La base se crea en `10.15.0.62`, no necesariamente desde el Ubuntu de la aplicacion.

Si se esta conectado directamente al servidor de base `10.15.0.62` por consola autorizada:

```bash
sudo mysql
```

Si el administrador autoriza conectarse remotamente desde el servidor Ubuntu de la app:

```bash
mysql -h 10.15.0.62 -u root -p
```

Si el DBA/admin entrega otro usuario administrador, reemplazar `root` por ese usuario.

Crear solamente la base nueva:

```sql
CREATE DATABASE IF NOT EXISTS inventario_modular
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

Si se quiere verificar antes de crear:

```sql
SHOW DATABASES LIKE 'inventario_modular';
```

No usar:

```sql
DROP DATABASE inventario_prod;
DROP DATABASE inventario_modular;
```

Los comandos `DROP` no forman parte de la instalacion inicial.

## Paso 6.2: Crear usuario MySQL de la aplicacion

La aplicacion no debe conectarse como `root`.

Como la app corre en otro servidor, el usuario MySQL debe quedar autorizado desde el
servidor Ubuntu de la aplicacion, no desde `localhost`.

Primero identificar o pedir al administrador la IP/nombre del servidor Ubuntu donde correra
la app. En el ejemplo se usa el placeholder `IP_DEL_SERVIDOR_APP`.

Crear usuario propio:

```sql
CREATE USER IF NOT EXISTS 'inventario_modular_app'@'IP_DEL_SERVIDOR_APP'
  IDENTIFIED BY 'CAMBIAR_EN_EL_SERVIDOR';
```

Dar permisos solo sobre la base nueva:

```sql
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
  ON inventario_modular.* TO 'inventario_modular_app'@'IP_DEL_SERVIDOR_APP';
FLUSH PRIVILEGES;
```

Verificar permisos:

```sql
SHOW GRANTS FOR 'inventario_modular_app'@'IP_DEL_SERVIDOR_APP';
```

Salir:

```sql
EXIT;
```

> Nota: reemplazar `CAMBIAR_EN_EL_SERVIDOR` por una clave real solo en la terminal del
> servidor. No escribir esa clave en git, documentacion, chat ni capturas.

Bloque SQL completo para copiar si esta autorizado:

```sql
CREATE DATABASE IF NOT EXISTS inventario_modular
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'inventario_modular_app'@'IP_DEL_SERVIDOR_APP'
  IDENTIFIED BY 'CAMBIAR_EN_EL_SERVIDOR';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
  ON inventario_modular.* TO 'inventario_modular_app'@'IP_DEL_SERVIDOR_APP';
FLUSH PRIVILEGES;
```

No commitear esa clave. No pegarla en documentacion.

Evitar `'inventario_modular_app'@'%'` salvo que el DBA/admin lo decida explicitamente.
Es mas seguro autorizar solo la IP o nombre del servidor Ubuntu de la aplicacion.

## Paso 7: Configuracion local del servidor

La configuracion real debe quedar fuera de git.

Variables esperadas:

```bash
export INVENTARIO_DB_URL="jdbc:mysql://10.15.0.62:3306/inventario_modular"
export INVENTARIO_DB_USER="inventario_modular_app"
export INVENTARIO_DB_PASSWORD="CAMBIAR_EN_EL_SERVIDOR"
export INVENTARIO_LDAP_URL="ldap://SERVIDOR_AD:389"
export INVENTARIO_LDAP_DOMAIN="DOMINIO"
export INVENTARIO_LDAP_BASE_DN="DC=ejemplo,DC=local"
export INVENTARIO_LDAP_DISPLAY_NAME_ATTRIBUTE="displayName"
export INVENTARIO_LDAP_FUERO_ATTRIBUTE="department"
```

Todavia falta confirmar los datos reales de Active Directory y el atributo exacto donde
esta cargado el fuero. Se usa `department` como valor inicial porque es un atributo comun,
pero puede ser otro segun el esquema real del dominio.

Para una prueba temporal en la misma sesion PuTTY, las variables se pueden exportar a mano.
Para una configuracion persistente futura, conviene usar un archivo fuera del repositorio,
por ejemplo:

```text
/etc/inventario-modular/inventario-modular.env
```

No crear este archivo como paso obligatorio todavia si solo se esta haciendo laboratorio.

## Paso 8: Prueba manual sin servicio systemd

Solo para laboratorio, se puede probar el `.jar` sin instalar servicio:

```bash
java -jar target/inventario-modular-0.0.1-SNAPSHOT.jar
```

Si la app intenta conectar a MySQL y faltan variables, puede fallar. Eso es esperable hasta
crear la base en `10.15.0.62`, autorizar el usuario y configurar credenciales locales.

No crear servicio systemd todavia. No tocar nginx todavia.

Si se ejecuta con variables en la misma linea:

```bash
INVENTARIO_DB_URL="jdbc:mysql://10.15.0.62:3306/inventario_modular" \
INVENTARIO_DB_USER="inventario_modular_app" \
INVENTARIO_DB_PASSWORD="CAMBIAR_EN_EL_SERVIDOR" \
java -jar target/inventario-modular-0.0.1-SNAPSHOT.jar
```

Esto sigue siendo una prueba manual, no un despliegue productivo.

## Paso 9: Ver CI/CD en GitLab

Abrir GitLab:

```text
https://gitlab.com/gustavoeliasm/inventario-modular
```

Buscar:

```text
Build -> Pipelines
```

Verificar que el pipeline de la rama `primeros-pasos` tenga las etapas:

```text
validar
construir
```

La etapa `validar` debe correr tests. La etapa `construir` debe generar el artefacto
`.jar`.

## Paso 10: Sincronizar GitHub desde Windows

GitHub es copia de seguridad y practica de versionado. Desde Windows:

```powershell
cd "G:\unju2025\google gravity\inventario-modular"
git push github primeros-pasos
```

## Que queda para hacer despues

- Confirmar datos reales de Active Directory.
- Crear migraciones Flyway iniciales.
- Crear tablas de modulos, permisos, roles y usuarios internos.
- Implementar autenticacion AD.
- Implementar autorizacion local por modulos.
- Agregar tests de seguridad.
- Definir ambiente staging real.
- Recien despues evaluar systemd, nginx y despliegue productivo.

## Criterio de exito de manana

Se considera exitoso si:

- El repo se clona desde GitLab en una carpeta nueva.
- Java 21 queda disponible en Ubuntu.
- `sh ./mvnw --batch-mode test` termina con `BUILD SUCCESS`.
- `sh ./mvnw --batch-mode -DskipTests package` genera el `.jar`.
- El servidor Ubuntu alcanza `10.15.0.62:3306`, o queda registrado que falta habilitar red/firewall.
- Se puede ver el pipeline en GitLab.
- No se toca el inventario actual ni la base `inventario_prod`.

## Bitacora de instalacion en Ubuntu

### 2026-08-28 - Preparacion inicial por PuTTY

Sesion observada:

```text
usuario: administrador
host: serverinventario
carpeta inicial: /home/administrador
```

Verificaciones realizadas:

- `/opt/inventario` existe y pertenece al sistema actual. No se debe usar para esta prueba.
- `/opt/inventario-modular` no existia al iniciar.
- Se creo `/opt/inventario-modular` como carpeta separada para laboratorio:

```bash
sudo mkdir -p /opt/inventario-modular
sudo chown "$USER":"$USER" /opt/inventario-modular
```

Resultado:

```text
drwxr-xr-x 2 administrador administrador 4096 ago 28 08:13 /opt/inventario-modular
```

Intento de clone por HTTPS:

```bash
cd /opt/inventario-modular
git clone --branch primeros-pasos https://gitlab.com/gustavoeliasm/inventario-modular.git .
```

Resultado:

- GitLab pidio usuario y clave.
- La autenticacion fallo con `HTTP Basic: Access denied`.
- Se decidio mantener GitLab como origen obligatorio y configurar SSH en lugar de clonar
  desde GitHub.

Verificacion SSH:

```bash
ls -la ~/.ssh
ssh -T git@gitlab.com
```

Resultado:

- Existia `~/.ssh`, pero no habia clave privada autorizada para GitLab.
- Se acepto la huella ED25519 de `gitlab.com`.
- GitLab respondio `Permission denied (publickey)`.

Clave SSH generada para GitLab:

```bash
ssh-keygen -t ed25519 -C "serverinventario gitlab inventario-modular" -f ~/.ssh/id_ed25519_gitlab
```

Clave publica mostrada para cargar en GitLab:

```text
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKfSYO8vUF30k7YNuxFAcK1EMbHgMtnd/mhrWiWYO5Qz serverinventario gitlab inventario-modular
```

Pendiente inmediato:

1. Agregar la clave publica en GitLab, en **User Settings -> SSH Keys**.
2. Crear `~/.ssh/config` para usar `~/.ssh/id_ed25519_gitlab` con `gitlab.com`.
3. Probar `ssh -T git@gitlab.com`.
4. Si la prueba responde bienvenida de GitLab, clonar con:

```bash
cd /opt/inventario-modular
git clone --branch primeros-pasos git@gitlab.com:gustavoeliasm/inventario-modular.git .
```

Nota de seguridad: la clave privada `~/.ssh/id_ed25519_gitlab` no debe compartirse ni
guardarse en el repositorio.

### 2026-08-28 - Documentacion subida a GitLab y GitHub

Despues de documentar la preparacion Ubuntu por SSH, se reviso el cambio local antes de
subirlo:

```powershell
git status --short --branch
git diff --check
git diff -- docs\inventario-modular\runbook-manana-ubuntu-putty.md
```

Controles realizados:

- El cambio tocaba solamente este runbook.
- `git diff --check` no reporto errores de espacios.
- No se detectaron secretos reales en el diff. Solo habia menciones documentales a
  `secretos`, `token` y placeholders.

Se creo el commit:

```powershell
git add docs\inventario-modular\runbook-manana-ubuntu-putty.md
git commit -m "docs: documenta preparacion Ubuntu por SSH"
```

Commit generado:

```text
bf98ff9 docs: documenta preparacion Ubuntu por SSH
```

El commit se subio a los dos repositorios configurados:

```powershell
git push origin primeros-pasos
git push github primeros-pasos
```

Resultado:

```text
GitLab origin: 9f57390..bf98ff9 primeros-pasos -> primeros-pasos
GitHub github: 9f57390..bf98ff9 primeros-pasos -> primeros-pasos
```

Estado final verificado:

```text
bf98ff9 (HEAD -> primeros-pasos, origin/primeros-pasos, origin/HEAD, github/primeros-pasos)
```

Nota de identidad Git:

- Git aviso que uso automaticamente `Gustavo Murad <gmurad@podjudsp.local>` como autor
  del commit.
- No bloquea el trabajo, pero si se quiere otra identidad en futuros commits conviene
  configurar `user.name` y `user.email` antes de seguir documentando o implementando.

Punto CI/CD abierto:

- El push a GitLab deberia disparar el pipeline de la rama `primeros-pasos`.
- Revisar en GitLab: **Build -> Pipelines**.
- Confirmar que pasen las etapas `validar` y `construir`.
- Si el pipeline falla, registrar el error antes de continuar con la instalacion Ubuntu.

### 2026-08-28 - Practica guiada de push y verificacion CI/CD

Se practico el flujo de Git paso a paso desde PowerShell en Windows para subir una nueva
documentacion. Hubo una confusion inicial al intentar ejecutar un comando de Windows
dentro de PuTTY:

```bash
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
```

Resultado en Ubuntu:

```text
-bash: cd: C:\Users\gmurad\Documents\ChatGPT\inventario-modular: No such file or directory
```

Aprendizaje registrado:

- PowerShell usa rutas Windows como `C:\Users\...`.
- PuTTY/Ubuntu usa rutas Linux como `/opt/inventario-modular`.
- Los commits y pushes de la copia local deben hacerse desde PowerShell en:

```text
C:\Users\gmurad\Documents\ChatGPT\inventario-modular
```

Comandos de verificacion ejecutados en PowerShell:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
git status --short --branch
git diff --stat
git diff --check
git diff -- docs\inventario-modular\runbook-manana-ubuntu-putty.md
```

Resultado observado:

- Rama: `primeros-pasos`.
- Archivo modificado: `docs/inventario-modular/runbook-manana-ubuntu-putty.md`.
- Cambio: 65 lineas nuevas de documentacion.
- `git diff --check` no reporto errores.
- El visor de `git diff` mostro `(END)`; para salir del visor se debe presionar `q`.

Se preparo el archivo para commit:

```powershell
git add docs\inventario-modular\runbook-manana-ubuntu-putty.md
git status --short --branch
```

La salida paso de ` M` a `M ` para el archivo, indicando que quedo en staging.

Se creo el commit:

```powershell
git commit -m "docs: documenta subida a repositorios"
```

Commit generado:

```text
80ae39b docs: documenta subida a repositorios
```

Git volvio a avisar que uso automaticamente la identidad:

```text
Gustavo Murad <gmurad@podjudsp.local>
```

Esto no bloqueo el commit. Queda como mejora futura configurar explicitamente:

```powershell
git config --global user.name "Gustavo Murad"
git config --global user.email "CORREO_A_DEFINIR"
```

Se subio primero a GitLab:

```powershell
git push origin primeros-pasos
```

Resultado:

```text
bf98ff9..80ae39b  primeros-pasos -> primeros-pasos
```

Se subio despues a GitHub:

```powershell
git push github primeros-pasos
```

Resultado:

```text
bf98ff9..80ae39b  primeros-pasos -> primeros-pasos
```

Verificacion final local/remota:

```powershell
git status --short --branch
git log --oneline -4 --decorate
git ls-remote origin refs/heads/primeros-pasos
git ls-remote github refs/heads/primeros-pasos
```

Resultado confirmado:

```text
HEAD -> primeros-pasos
origin/primeros-pasos -> 80ae39b
github/primeros-pasos -> 80ae39b
```

Verificacion CI/CD en GitLab:

- Se reviso la pantalla **Build -> Pipelines** del proyecto `inventario-modular`.
- El pipeline del commit `80ae39b` aparecio en estado `Passed`.
- Mensaje del commit en GitLab: `docs: documenta subida a repositorios`.
- Rama: `primeros-pasos`.
- Duracion observada: `00:01:16`.
- Stages esperadas: `validar` y `construir`, ambas indicadas como correctas en la vista
  del pipeline.

Conclusion:

- La documentacion quedo subida a GitLab y GitHub.
- El pipeline de GitLab paso correctamente para el commit `80ae39b`.
- Se puede continuar con la instalacion Ubuntu por PuTTY desde el pendiente de SSH a GitLab.

### 2026-08-28 - Clone GitLab e instalacion de Java 21 en Ubuntu

Se configuro correctamente SSH en `serverinventario` para usar la clave local
`~/.ssh/id_ed25519_gitlab` contra GitLab:

```bash
cat > ~/.ssh/config <<'EOF'
Host gitlab.com
  HostName gitlab.com
  User git
  IdentityFile ~/.ssh/id_ed25519_gitlab
  IdentitiesOnly yes
EOF

chmod 600 ~/.ssh/config
ssh -T git@gitlab.com
```

Resultado:

```text
Welcome to GitLab, @gustavoeliasm!
```

Con GitLab SSH funcionando, se clono el repositorio desde GitLab en la carpeta separada de
laboratorio:

```bash
cd /opt/inventario-modular
git clone --branch primeros-pasos git@gitlab.com:gustavoeliasm/inventario-modular.git .
git status
git log --oneline -5
```

Resultado confirmado:

```text
On branch primeros-pasos
Your branch is up to date with 'origin/primeros-pasos'.
nothing to commit, working tree clean
80ae39b (HEAD -> primeros-pasos, origin/primeros-pasos, origin/HEAD) docs: documenta subida a repositorios
```

Se verifico que la carpeta contenia el proyecto esperado:

```bash
ls
```

Resultado:

```text
docs  mvnw  mvnw.cmd  pom.xml  README.md  src
```

Aviso CI/CD registrado:

- El servidor Ubuntu quedo apuntando al commit `80ae39b`.
- Ese commit ya tenia pipeline `Passed` en GitLab.
- Por lo tanto, la instalacion en Ubuntu partio desde el mismo commit validado por CI.

Luego se verifico Java en Ubuntu:

```bash
java -version
javac -version
```

Resultado inicial:

```text
Command 'java' not found
Command 'javac' not found
```

Se instalo JDK 21 headless con `apt`. Este paso instala paquetes del sistema, pero no toca
`/opt/inventario`, no toca MySQL y no reinicia el servicio del inventario actual:

```bash
sudo apt update
sudo apt install -y openjdk-21-jdk-headless
java -version
javac -version
```

Resultado confirmado:

```text
openjdk version "21.0.12" 2026-07-21
OpenJDK Runtime Environment (build 21.0.12+8-1-24.04-Ubuntu)
OpenJDK 64-Bit Server VM (build 21.0.12+8-1-24.04-Ubuntu, mixed mode, sharing)
javac 21.0.12
```

Durante la instalacion aparecio el aviso:

```text
Service restarts being deferred:
 systemctl restart systemd-logind.service
```

Decision tomada:

- No reiniciar servicios del servidor para esta prueba.
- Continuar con la compilacion del proyecto usando Maven Wrapper.

Siguiente paso previsto:

```bash
cd /opt/inventario-modular
sh ./mvnw --batch-mode test
```

Nota CI/CD:

- Este comando replica en el servidor Ubuntu la etapa `validar` del pipeline GitLab.
- Si termina con `BUILD SUCCESS`, queda confirmado que Ubuntu puede ejecutar la misma
  validacion basica que CI.

### 2026-08-28 - Verificacion de base MySQL por phpMyAdmin

Desde el servidor Ubuntu de la aplicacion se confirmo que el cliente MySQL esta instalado:

```bash
mysql --version
```

Resultado:

```text
mysql  Ver 8.0.46-0ubuntu0.24.04.3 for Linux on x86_64 ((Ubuntu))
```

Se intento conectar al servidor MySQL remoto `10.15.0.62` usando `root` desde el servidor
de aplicacion `10.15.2.251`:

```bash
mysql -h 10.15.0.62 -u root -p
```

Resultado:

```text
ERROR 1045 (28000): Access denied for user 'root'@'10.15.2.251' (using password: YES)
```

Interpretacion:

- El servidor MySQL responde por red.
- El usuario `root` no esta autorizado para entrar remotamente desde `10.15.2.251`.
- Este bloqueo es correcto desde seguridad; no seguir intentando con `root` remoto.

Luego se informo acceso por navegador a phpMyAdmin:

```text
http://10.15.0.62/phpmyadmin/db_structure.php?server=1&db=inventario_modular
```

Conclusion:

- La base `inventario_modular` existe o phpMyAdmin permite llegar a su vista.
- La creacion/verificacion del usuario de aplicacion debe hacerse desde phpMyAdmin o desde
  una consola autorizada del servidor MySQL.
- La aplicacion Java debe usar un usuario propio, por ejemplo
  `inventario_modular_app` autorizado desde `10.15.2.251`.
- No registrar contrasenas reales en Git, documentacion, chat ni capturas.

### 2026-08-28 - Usuario MySQL de aplicacion y error 1045

Desde phpMyAdmin se creo o verifico el usuario:

```text
'inventario_modular_app'@'10.15.2.251'
```

Tambien se asignaron permisos sobre la base nueva:

```text
inventario_modular.*
```

Permisos esperados:

```text
SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
```

Luego se probo desde el servidor Ubuntu de la aplicacion:

```bash
mysql -h 10.15.0.62 -u inventario_modular_app -p inventario_modular
```

Resultado:

```text
ERROR 1045 (28000): Access denied for user 'inventario_modular_app'@'10.15.2.251' (using password: YES)
```

Interpretacion:

- La red hacia MySQL funciona.
- MySQL identifica correctamente al cliente como `10.15.2.251`.
- El usuario/host existe o fue referenciado correctamente, pero la clave no coincide, el
  usuario fue creado con otra clave, o `CREATE USER IF NOT EXISTS` no actualizo la clave de
  un usuario que ya existia.

Accion recomendada en phpMyAdmin, sin registrar la clave real:

```sql
ALTER USER 'inventario_modular_app'@'10.15.2.251'
  IDENTIFIED BY 'NUEVA_CLAVE_REAL_SOLO_EN_PHPMYADMIN';

FLUSH PRIVILEGES;

SHOW GRANTS FOR 'inventario_modular_app'@'10.15.2.251';
```

Despues volver a probar desde PuTTY:

```bash
mysql -h 10.15.0.62 -u inventario_modular_app -p inventario_modular
```

Nota de seguridad:

- No usar el usuario personal de phpMyAdmin para la aplicacion.
- No guardar contrasenas reales en el repo, chat, capturas ni `.gitlab-ci.yml`.
- Si una contrasena real fue compartida por accidente, cambiarla antes de dejar el entorno
  como estable.

### 2026-08-28 - Clave MySQL de aplicacion actualizada

Desde phpMyAdmin se ejecuto correctamente:

```sql
ALTER USER 'inventario_modular_app'@'10.15.2.251'
  IDENTIFIED BY 'NUEVA_CLAVE_REAL_SOLO_EN_PHPMYADMIN';

FLUSH PRIVILEGES;

SHOW GRANTS FOR 'inventario_modular_app'@'10.15.2.251';
```

Resultado:

- phpMyAdmin informo que las consultas se ejecutaron con exito.
- `SHOW GRANTS` mostro permisos para `inventario_modular_app` desde `10.15.2.251`.
- La clave real no se registra en este documento.

Siguiente verificacion desde PuTTY:

```bash
mysql -h 10.15.0.62 -u inventario_modular_app -p inventario_modular
```

Si conecta, ejecutar:

```sql
SELECT DATABASE();
SHOW TABLES;
EXIT;
```

### 2026-08-28 - Conexion MySQL verificada desde Ubuntu

Desde PuTTY, en el servidor de aplicacion `serverinventario`, se probo la conexion a la
base nueva:

```bash
mysql -h 10.15.0.62 -u inventario_modular_app -p inventario_modular
```

Resultado:

```text
Welcome to the MySQL monitor.
Server version: 8.0.42-0ubuntu0.20.04.1 (Ubuntu)
```

Dentro de MySQL se verifico:

```sql
SELECT DATABASE();
SHOW TABLES;
EXIT;
```

Resultado:

```text
DATABASE() = inventario_modular
SHOW TABLES = Empty set
```

Interpretacion:

- El servidor Ubuntu de la aplicacion `10.15.2.251` puede conectarse al MySQL
  `10.15.0.62`.
- El usuario `inventario_modular_app` funciona desde `10.15.2.251`.
- La base `inventario_modular` esta creada.
- La base esta vacia, lo cual es esperable antes de crear migraciones Flyway.
- No se uso ni se modifico `inventario_prod`.

### 2026-08-28 - Tests Maven ejecutados en Ubuntu

Desde PuTTY se ejecuto:

```bash
cd /opt/inventario-modular
sh ./mvnw --batch-mode test
```

Resultado confirmado:

```text
Tests run: 4, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
Total time: 13.561 s
Finished at: 2026-08-28T11:55:34-03:00
```

Detalles relevantes:

- La prueba corrio con Java `21.0.12`.
- El perfil activo fue `test`.
- La base usada por tests fue H2 en memoria:

```text
jdbc:h2:mem:inventario_modular_test
```

- Este comando replica en Ubuntu la etapa CI/CD `validar` del pipeline GitLab.

Warnings observados y aceptados para esta etapa:

- Spring Security genero una clave de desarrollo temporal. Esto es normal hasta implementar
  la autenticacion real con Active Directory y usuarios locales.
- Mockito aviso sobre carga dinamica de agente en futuras versiones de JDK. No bloquea el
  build actual.

Siguiente paso recomendado en Ubuntu:

```bash
cd /opt/inventario-modular
sh ./mvnw --batch-mode -DskipTests package
ls -lh target/*.jar
```

Este paso replica la etapa CI/CD `construir` y confirma que el `.jar` tambien se genera en
Ubuntu.

### 2026-08-28 - Base lista para probar pagina de inicio

Despues de confirmar la conexion MySQL desde Ubuntu, se definio que ya se puede empezar a
probar la pagina inicial del nuevo sistema.

Estado confirmado:

- El servidor Ubuntu de aplicacion es `10.15.2.251`.
- El servidor MySQL es `10.15.0.62`.
- La base nueva es `inventario_modular`.
- El usuario de aplicacion es `inventario_modular_app`.
- La conexion desde Ubuntu hacia MySQL ya fue verificada.
- La base esta vacia, lo cual es esperable antes de crear migraciones Flyway.

Pagina inicial disponible en la primera base funcional:

```text
/
/admin
/api/v1/sistema/estado
```

Para laboratorio, la app Java debe correr en HTTP interno y puerto separado:

```text
http://10.15.2.251:8081/admin
http://10.15.2.251:8081/api/v1/sistema/estado
```

Recordatorio importante:

- El sistema viejo entraba por HTTPS.
- Inventario Modular todavia no debe tocar nginx, certificados ni systemd del sistema viejo.
- Primero se valida HTTP interno en `8081`.
- Despues se planifica HTTPS con nginx/reverse proxy en una etapa separada y revisada.

Comando de arranque manual previsto, sin registrar la clave real:

```bash
INVENTARIO_DB_URL="jdbc:mysql://10.15.0.62:3306/inventario_modular" \
INVENTARIO_DB_USER="inventario_modular_app" \
INVENTARIO_DB_PASSWORD="CLAVE_REAL_SOLO_EN_SERVIDOR" \
INVENTARIO_SERVER_PORT="8081" \
java -jar target/inventario-modular-0.0.1-SNAPSHOT.jar
```

Antes de ejecutar este arranque, debe generarse el `.jar` en Ubuntu:

```bash
cd /opt/inventario-modular
sh ./mvnw --batch-mode -DskipTests package
ls -lh target/*.jar
```

Nota CI/CD:

- El build local en Windows ya paso.
- El commit funcional `7e93058` ya fue subido a GitLab.
- El push a GitLab activo CI/CD; revisar en GitLab que el pipeline del commit `7e93058`
  quede `Passed` antes de considerar esta base como lista para actualizar Ubuntu.

### 2026-08-28 - Primera base funcional del nuevo sistema

Se empezo a construir Inventario Modular con una primera entrega pequena y verificable:

- Configuracion local de puerto `8081` mediante `INVENTARIO_SERVER_PORT`.
- Soporte para encabezados de proxy con `server.forward-headers-strategy=framework`.
- Endpoint publico versionado:

```text
GET /api/v1/sistema/estado
```

- Entrada web administrativa minima:

```text
GET /admin
```

- Redireccion de `/` hacia `/admin`.
- Configuracion inicial de seguridad: `/`, `/admin`, `/css/**` y
  `/api/v1/sistema/estado` quedan publicos por ahora; el resto requiere autenticacion.

Archivos principales agregados o modificados:

```text
src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/config/SecurityConfig.java
src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/web/AdminController.java
src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/web/SystemStatusController.java
src/main/resources/templates/admin/index.html
src/main/resources/static/css/admin.css
src/main/resources/application.properties
src/main/resources/application-local.properties
src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/SystemStatusControllerTests.java
```

Validacion local en Windows:

```powershell
$env:JAVA_HOME='C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot'
$env:Path="$env:JAVA_HOME\bin;$env:Path"
.\mvnw.cmd --batch-mode test
.\mvnw.cmd --batch-mode -DskipTests package
```

Resultado:

```text
Tests run: 4, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
target\inventario-modular-0.0.1-SNAPSHOT.jar
```

Nota sobre HTTPS:

- El inventario viejo entraba por HTTPS.
- En esta primera etapa Inventario Modular no instala nginx ni systemd.
- La app Java queda preparada para correr HTTP interno en laboratorio y recibir HTTPS mas
  adelante por nginx/reverse proxy.
- No reutilizar todavia el puerto ni la configuracion HTTPS del inventario viejo.

Comandos previstos para actualizar el servidor Ubuntu por PuTTY despues de subir el
commit a GitLab:

```bash
cd /opt/inventario-modular
git status
git pull origin primeros-pasos
git log --oneline -5
sh ./mvnw --batch-mode test
sh ./mvnw --batch-mode -DskipTests package
ls -lh target/*.jar
```

Explicacion:

- `git status` confirma que no haya cambios locales en el servidor.
- `git pull origin primeros-pasos` trae el commit validado desde GitLab.
- `git log --oneline -5` permite verificar que el commit esperado llego al servidor.
- `sh ./mvnw --batch-mode test` replica la etapa CI `validar`.
- `sh ./mvnw --batch-mode -DskipTests package` replica la etapa CI `construir`.
- `ls -lh target/*.jar` confirma que el artefacto `.jar` existe en Ubuntu.

No ejecutar todavia:

```bash
java -jar target/inventario-modular-0.0.1-SNAPSHOT.jar
```

Motivo: el perfil local intenta conectar a MySQL. Antes de arrancar la app en Ubuntu hay
que confirmar la base `inventario_modular`, usuario, permisos y variables `INVENTARIO_*`.

### 2026-08-28 - Login Active Directory solo lectura

Se agrego una primera integracion de autenticacion con Active Directory para Inventario
Modular.

Alcance de esta entrega:

- `/admin` deja de ser publico y requiere login.
- Spring Security mantiene `/`, `/css/**` y `/api/v1/sistema/estado` publicos.
- Si `INVENTARIO_LDAP_ENABLED=true`, la app usa Active Directory como proveedor de
  autenticacion.
- La app solo lee atributos del usuario autenticado; no escribe ni modifica Active
  Directory.
- El panel inicial muestra usuario/cuenta, nombre visible y fuero.
- El atributo de nombre visible es configurable con
  `INVENTARIO_LDAP_DISPLAY_NAME_ATTRIBUTE`.
- El atributo de fuero es configurable con `INVENTARIO_LDAP_FUERO_ATTRIBUTE`.
- Valor inicial sugerido para fuero: `department`, pendiente de confirmar contra el AD real.
- Se agrego un boton `Salir` para cerrar la sesion usando el logout de Spring Security.
- Se agrego una tabla de atributos no sensibles recibidos desde AD durante el login para
  poder inspeccionar que esta entregando realmente el dominio.

Archivos principales agregados o modificados:

```text
src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/InventarioModularApplication.java
src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/config/ActiveDirectoryProperties.java
src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/config/SecurityConfig.java
src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/security/ActiveDirectoryUserDetails.java
src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/security/ActiveDirectoryUserDetailsContextMapper.java
src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/web/AdminController.java
src/main/resources/application-local.properties
src/main/resources/templates/admin/index.html
src/main/resources/static/css/admin.css
src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/security/ActiveDirectoryUserDetailsContextMapperTests.java
src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/SystemStatusControllerTests.java
src/test/resources/application-test.properties
```

Validacion local en Windows:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
$env:JAVA_HOME='C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot'
$env:Path="$env:JAVA_HOME\bin;$env:Path"
.\mvnw.cmd --batch-mode test
.\mvnw.cmd --batch-mode -DskipTests package
```

Resultado:

```text
Tests run: 8, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
target\inventario-modular-0.0.1-SNAPSHOT.jar
```

Comandos para actualizar Ubuntu por PuTTY despues del push a GitLab:

```bash
cd /opt/inventario-modular
git status
git pull origin primeros-pasos
git log --oneline -5
sh ./mvnw --batch-mode test
sh ./mvnw --batch-mode -DskipTests package
ls -lh target/*.jar
```

Explicacion de los comandos:

- `cd /opt/inventario-modular` entra al nuevo proyecto, no al sistema viejo.
- `git status` confirma que el servidor no tenga cambios locales pendientes.
- `git pull origin primeros-pasos` trae desde GitLab el commit validado.
- `git log --oneline -5` permite comprobar que llego el commit esperado.
- `sh ./mvnw --batch-mode test` ejecuta las pruebas tambien en Ubuntu.
- `sh ./mvnw --batch-mode -DskipTests package` genera el `.jar`.
- `ls -lh target/*.jar` confirma que el artefacto existe.

Variables necesarias para una prueba manual con MySQL remoto y AD activo:

```bash
INVENTARIO_DB_URL="jdbc:mysql://10.15.0.62:3306/inventario_modular" \
INVENTARIO_DB_USER="inventario_modular_app" \
INVENTARIO_DB_PASSWORD="CLAVE_REAL_SOLO_EN_SERVIDOR" \
INVENTARIO_LDAP_ENABLED="true" \
INVENTARIO_LDAP_URL="ldap://SERVIDOR_AD:389" \
INVENTARIO_LDAP_DOMAIN="DOMINIO" \
INVENTARIO_LDAP_BASE_DN="DC=ejemplo,DC=local" \
INVENTARIO_LDAP_DISPLAY_NAME_ATTRIBUTE="displayName" \
INVENTARIO_LDAP_FUERO_ATTRIBUTE="department" \
INVENTARIO_SERVER_PORT="8081" \
java -jar target/inventario-modular-0.0.1-SNAPSHOT.jar
```

No escribir claves reales en git, README, capturas compartidas ni commits. Si alguna clave
quedo expuesta durante laboratorio, conviene rotarla antes de usar el sistema de forma
estable.

Nota HTTPS:

- El sistema viejo seguia entrando por HTTPS.
- Esta entrega no toca nginx, certificados ni systemd.
- Primero se valida login AD por HTTP interno en `8081`.
- Despues se planifica HTTPS con reverse proxy en una etapa separada.

Nota CI/CD:

- Al subir este commit a GitLab se activa el pipeline.
- Ese pipeline debe correr tests y construir el `.jar`.
- Todavia no despliega automaticamente en Ubuntu ni toca la base remota.

### 2026-08-28 - Boton salir y atributos visibles desde AD

Se amplio la pantalla `/admin` para que, despues del login Active Directory, permita ver
mas informacion de diagnostico del usuario autenticado.

Cambios:

- Boton `Salir` en el panel principal.
- Logout via `POST /logout`, gestionado por Spring Security.
- Tabla `Datos recibidos desde Active Directory`.
- La tabla muestra los atributos no vacios recibidos en el contexto LDAP.
- Se ocultan atributos de cuenta que no aportan a la pantalla y pueden ser sensibles, como
  datos de expiracion, bloqueo o ultimos inicios de sesion.

Validacion local:

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
$env:JAVA_HOME='C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot'
$env:Path="$env:JAVA_HOME\bin;$env:Path"
.\mvnw.cmd --batch-mode test
.\mvnw.cmd --batch-mode -DskipTests package
```

Resultado:

```text
Tests run: 8, Failures: 0, Errors: 0, Skipped: 0
BUILD SUCCESS
```

Cuando este commit llegue al servidor Ubuntu, los comandos de actualizacion siguen siendo:

```bash
cd /opt/inventario-modular
git status
git pull origin primeros-pasos
git log --oneline -5
sh ./mvnw --batch-mode test
sh ./mvnw --batch-mode -DskipTests package
ls -lh target/*.jar
```

### 2026-08-28 - Datos reales AD y diagnostico de puerto 8081

Se confirmo la configuracion real de Active Directory leyendo solo variables no secretas
del `.env` del sistema viejo.

Comando usado en PuTTY, dentro de `/opt/inventario`:

```bash
printf "\n[AD sin mostrar claves]\n"
grep -E '^(AUTH_MODE|AD_SERVER|AD_DOMAIN|AD_BASE_DN|AD_USE_SSL|AD_CONNECT_TIMEOUT|AD_SUPERUSERS)=' .env 2>/dev/null

printf "\n[AD usuarios de sincronizacion, clave ocultada]\n"
grep -E '^(AD_SYNC_USER)=' .env 2>/dev/null
grep -E '^(AD_SYNC_PASSWORD)=' .env 2>/dev/null | sed 's/=.*/=******** OCULTA ********/'
```

Resultado util:

```text
AD_SERVER=10.15.0.41
AD_DOMAIN=podjudsp.local
AD_BASE_DN=OU=USUARIOS,OU=PODJUDSP,DC=podjudsp,DC=local
AD_USE_SSL=false
AD_CONNECT_TIMEOUT=5
AD_SUPERUSERS=gmurad
```

Nota: en el `.env` viejo aparecian algunas variables AD repetidas. Para esta documentacion
se toma el ultimo valor efectivo observado para `AD_BASE_DN`.

Equivalencia para Inventario Modular:

```bash
INVENTARIO_LDAP_ENABLED="true"
INVENTARIO_LDAP_URL="ldap://10.15.0.41:389"
INVENTARIO_LDAP_DOMAIN="podjudsp.local"
INVENTARIO_LDAP_BASE_DN="OU=USUARIOS,OU=PODJUDSP,DC=podjudsp,DC=local"
INVENTARIO_LDAP_DISPLAY_NAME_ATTRIBUTE="displayName"
INVENTARIO_LDAP_FUERO_ATTRIBUTE="department"
```

Tambien se diagnostico por que no cargaba:

```text
http://10.15.2.251:8081/
```

El navegador mostro `ERR_CONNECTION_REFUSED`. Se verifico:

```bash
cd /opt/inventario-modular
ps -ef | grep '[j]ava'
ss -ltnp | grep ':8081' || echo "Nada escuchando en 8081"
```

Resultado:

```text
No habia procesos Java.
Nada escuchando en 8081.
```

Conclusion: el `.jar` existia, pero la app no estaba levantada. Para probar por navegador
primero hay que ejecutar manualmente:

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

La terminal queda ocupada mientras la app corre. Si vuelve al prompt, hay que leer el error
de consola antes de seguir.

Documentacion tecnica agregada:

```text
docs/inventario-modular/login-active-directory.md
docs/decisions/ADR-004-login-active-directory-solo-lectura.md
```

### 2026-08-28 - Servicio systemd para Inventario Modular

Se decidio que Inventario Modular debe levantar automaticamente en Ubuntu, igual que el
sistema viejo, pero como servicio separado.

Estado observado antes de crear el servicio:

```text
inventario.service       activo, sistema viejo GOLD, no tocar
inventario-next.service  activo, SvelteKit en puerto 5173
inventario-modular       no existia todavia
```

Puertos observados:

```text
80    activo
443   activo
8080  activo
5173  activo por inventario-next
8081  libre para inventario-modular
```

Archivo de entorno creado fuera de git:

```text
/etc/inventario-modular/inventario-modular.env
```

Variables reales configuradas sin documentar la clave:

```text
INVENTARIO_DB_URL=jdbc:mysql://10.15.0.62:3306/inventario_modular
INVENTARIO_DB_USER=inventario_modular_app
INVENTARIO_DB_PASSWORD=******** OCULTA ********
INVENTARIO_LDAP_ENABLED=true
INVENTARIO_LDAP_URL=ldap://10.15.0.41:389
INVENTARIO_LDAP_DOMAIN=podjudsp.local
INVENTARIO_LDAP_BASE_DN=OU=USUARIOS,OU=PODJUDSP,DC=podjudsp,DC=local
INVENTARIO_LDAP_DISPLAY_NAME_ATTRIBUTE=displayName
INVENTARIO_LDAP_FUERO_ATTRIBUTE=department
INVENTARIO_SERVER_PORT=8081
```

Permisos del archivo:

```bash
sudo chown root:root /etc/inventario-modular/inventario-modular.env
sudo chmod 600 /etc/inventario-modular/inventario-modular.env
```

Servicio creado:

```text
/etc/systemd/system/inventario-modular.service
```

Contenido usado:

```ini
[Unit]
Description=Inventario Modular Spring Boot
After=network.target

[Service]
Type=simple
User=administrador
Group=administrador
WorkingDirectory=/opt/inventario-modular
EnvironmentFile=/etc/inventario-modular/inventario-modular.env
ExecStart=/usr/bin/java -jar /opt/inventario-modular/target/inventario-modular-0.0.1-SNAPSHOT.jar
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Comandos ejecutados para activar el servicio:

```bash
sudo systemctl daemon-reload
sudo systemctl enable inventario-modular.service
sudo systemctl start inventario-modular.service
```

Primer problema encontrado:

```text
Access denied for user 'inventario_modular_app'@'10.15.2.251' (using password: NO)
```

Diagnostico:

```text
La aplicacion estaba leyendo usuario y URL, pero la variable INVENTARIO_DB_PASSWORD estaba
vacia. Por eso MySQL recibia conexion sin password.
```

Correccion aplicada:

- Se detuvo solo `inventario-modular.service`.
- Se actualizo `/etc/inventario-modular/inventario-modular.env`.
- Se verifico que `INVENTARIO_DB_PASSWORD` tuviera largo mayor que cero, sin mostrar la
  clave.
- Se inicio nuevamente `inventario-modular.service`.

Resultado final reportado:

```text
Funciono.
```

Conclusion:

- Inventario Modular ya puede quedar levantado automaticamente.
- El servidor viejo `inventario.service` sigue activo.
- `inventario-next.service` todavia no debe apagarse hasta confirmar que ya no se usa.
- HTTPS/nginx todavia no se toca.

Comandos de verificacion utiles:

```bash
systemctl status inventario-modular.service --no-pager -l
ss -ltnp | grep ':8081' || echo "Nada escuchando en 8081"
sudo journalctl -u inventario-modular.service -n 120 --no-pager
```

URL de laboratorio:

```text
http://10.15.2.251:8081/
```

### 2026-08-28 - Proximo paso despues del primer arranque

Con Inventario Modular ya levantando en Ubuntu, se propone el siguiente orden:

```text
Usuarios y permisos minimos
  -> Equipos/API de inventario
  -> Dashboard simple
  -> Tareas tecnicas
  -> Stock/componentes
  -> Actas/reportes
```

Razon:

- Active Directory ya autentica.
- Falta que Inventario Modular autorice localmente quien puede entrar y que puede ver.
- Luego conviene iniciar con Equipos porque es el nucleo del inventario viejo.

Documento de referencia:

```text
docs/inventario-modular/proximo-paso-funcional.md
```
