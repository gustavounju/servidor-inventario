# Actualizacion de produccion - Inventario Modular

## Alcance

Estos comandos actualizan solamente el servidor nuevo de Inventario Modular en:

```text
/opt/inventario-modular
```

No tocan el inventario viejo ni el servicio `inventario.service`.

## Antes de empezar

Confirmar por PuTTY/SSH que se esta en el servidor Ubuntu correcto y que el servicio existe:

```bash
hostname
pwd
systemctl status inventario-modular.service --no-pager -l
```

Confirmar que el repositorio apunta a GitLab:

```bash
cd /opt/inventario-modular
git remote -v
git branch --show-current
git status --short
```

Si `git status --short` muestra cambios locales no esperados, detenerse y revisarlos antes
de actualizar.

## Variables de entorno

La configuracion real debe estar fuera de git:

```text
/etc/inventario-modular/inventario-modular.env
```

Revisar sin imprimir secretos completos:

```bash
sudo grep -E '^(SPRING_PROFILES_ACTIVE|INVENTARIO_SERVER_PORT|INVENTARIO_DB_PRIMARY_URL|INVENTARIO_DB_URL|INVENTARIO_DB_PRIMARY_USER|INVENTARIO_DB_USER|INVENTARIO_LDAP_ENABLED|INVENTARIO_LDAP_URL|INVENTARIO_LDAP_DOMAIN|INVENTARIO_LDAP_BASE_DN|INVENTARIO_LDAP_READ_ONLY_USER_DN)=' /etc/inventario-modular/inventario-modular.env
sudo grep -E '^(INVENTARIO_DB_PRIMARY_PASSWORD|INVENTARIO_DB_PASSWORD|INVENTARIO_LDAP_READ_ONLY_PASSWORD|INVENTARIO_REPORT_TOKEN)=' /etc/inventario-modular/inventario-modular.env | sed 's/=.*/=********/'
```

Valores esperados para trabajo, ajustando usuario/clave reales:

```bash
sudo nano /etc/inventario-modular/inventario-modular.env
```

Contenido guia, sin copiar claves reales al repositorio:

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
INVENTARIO_LDAP_URL=ldap://SERVIDOR_AD:389
INVENTARIO_LDAP_DOMAIN=podjudsp.local
INVENTARIO_LDAP_BASE_DN=OU=USUARIOS,OU=PODJUDSP,DC=podjudsp,DC=local
INVENTARIO_LDAP_READ_ONLY_USER_DN=CN=lector-inventario,OU=Servicios,DC=podjudsp,DC=local
INVENTARIO_LDAP_READ_ONLY_PASSWORD=CAMBIAR_EN_SERVIDOR
```

El perfil `local` acepta tambien los aliases historicos `INVENTARIO_DB_URL`,
`INVENTARIO_DB_USER` e `INVENTARIO_DB_PASSWORD`, porque esos nombres ya fueron usados en
el servidor. Las claves reales nunca se escriben en git.

Proteger el archivo:

```bash
sudo chown root:root /etc/inventario-modular/inventario-modular.env
sudo chmod 600 /etc/inventario-modular/inventario-modular.env
```

## Actualizar codigo desde GitLab

```bash
cd /opt/inventario-modular
git fetch origin
git checkout primeros-pasos
git pull --ff-only origin primeros-pasos
```

## Validar y construir

```bash
cd /opt/inventario-modular
sh ./mvnw --batch-mode test
sh ./mvnw --batch-mode -DskipTests package
```

La salida esperada de tests debe terminar en `BUILD SUCCESS`.

## Reiniciar solo Inventario Modular

```bash
sudo systemctl restart inventario-modular.service
systemctl status inventario-modular.service --no-pager -l
sudo journalctl -u inventario-modular.service -n 120 --no-pager
```

## Verificaciones HTTP

Desde el servidor Ubuntu:

```bash
curl -s http://127.0.0.1:8081/api/v1/sistema/estado
curl -s 'http://127.0.0.1:8081/api/v1/usuarios/dominio?q=gmurad'
curl -s http://127.0.0.1:8081/scripts/windows/inventario-modular.ps1.sha256
curl -I http://127.0.0.1:8081/scripts/windows/inventario-modular.ps1
```

El endpoint `/api/v1/usuarios/dominio` exige usuario autenticado con permiso de administrar
usuarios, por lo que la verificacion con `curl` directo puede redirigir al login o devolver
HTML si no hay sesion. La prueba funcional principal es entrar con `admin.local`, abrir
`/admin/usuarios`, buscar un usuario AD por usuario/nombre/apellido y autorizarlo con el
rol correspondiente.

## Incidente resuelto: busqueda de usuarios AD

Fecha de validacion: 31 de agosto de 2026.

Sintoma observado:

```text
/admin/usuarios -> Usuarios de dominio -> No disponible
No se pudo consultar Active Directory.
```

Causa:

```text
INVENTARIO_LDAP_ENABLED=true estaba configurado, pero faltaba la cuenta lectora LDAP.
Spring informaba: Property 'userDn' not set - anonymous context will be used for read-only operations.
Active Directory rechazaba la consulta anonima.
```

Correccion aplicada:

```text
1. Se configuro una cuenta lectora LDAP en /etc/inventario-modular/inventario-modular.env.
2. Se actualizo la app para buscar usuarios AD bajo demanda, no al abrir la pantalla.
3. Se movio la seccion Usuarios de dominio arriba, en una fila/tabla ordenada de resultados.
```

Variables criticas, sin documentar valores secretos:

```bash
INVENTARIO_LDAP_READ_ONLY_USER_DN=CUENTA_LECTORA_LDAP
INVENTARIO_LDAP_READ_ONLY_PASSWORD=CLAVE_REAL_SOLO_EN_SERVIDOR
```

Resultado confirmado:

```text
La busqueda ya toma usuarios de Active Directory desde la pantalla de administracion.
Desde cada resultado se puede seleccionar el usuario, asignarle rol y guardarlo como
usuario autorizado en MySQL.
```

Desde una PC de la red, abrir:

```text
http://IP_DEL_SERVIDOR:8081/login
```

La pantalla de login debe mostrar el boton `Copiar comando`.

## Comando manual con verificacion SHA-256

El login arma automaticamente este tipo de comando, usando la IP desde donde se abrio:

```powershell
$u='http://IP_DEL_SERVIDOR:8081'; $p="$env:TEMP\inventario-modular.ps1"; $h=(iwr "$u/scripts/windows/inventario-modular.ps1.sha256" -UseBasicParsing).Content.Trim(); iwr "$u/scripts/windows/inventario-modular.ps1" -UseBasicParsing -OutFile $p; $sha=[System.Security.Cryptography.SHA256]::Create(); $fs=[System.IO.File]::OpenRead($p); try{$a=([BitConverter]::ToString($sha.ComputeHash($fs))).Replace('-','').ToLowerInvariant()}finally{$fs.Close()}; if($a -ne $h){throw "SHA-256 invalido. Script descargado no coincide con el publicado por el servidor."}; powershell -ExecutionPolicy Bypass -NoProfile -File $p -ServerUrl "$u/api/v1/equipos/inventario"
```

Si en produccion se configura `INVENTARIO_REPORT_TOKEN` real en el servidor, el equipo que
ejecuta el script tambien debe recibir ese token. No publicarlo en el login ni en archivos
versionados. Para una prueba controlada:

```powershell
$env:INVENTARIO_REPORT_TOKEN = "TOKEN_REAL_DE_REPORTE"
$u='http://IP_DEL_SERVIDOR:8081'; $p="$env:TEMP\inventario-modular.ps1"; $h=(iwr "$u/scripts/windows/inventario-modular.ps1.sha256" -UseBasicParsing).Content.Trim(); iwr "$u/scripts/windows/inventario-modular.ps1" -UseBasicParsing -OutFile $p; $sha=[System.Security.Cryptography.SHA256]::Create(); $fs=[System.IO.File]::OpenRead($p); try{$a=([BitConverter]::ToString($sha.ComputeHash($fs))).Replace('-','').ToLowerInvariant()}finally{$fs.Close()}; if($a -ne $h){throw "SHA-256 invalido. Script descargado no coincide con el publicado por el servidor."}; powershell -ExecutionPolicy Bypass -NoProfile -File $p -ServerUrl "$u/api/v1/equipos/inventario"
```

## Politica de ejecucion de PowerShell

Algunos equipos bloquean `.ps1` por politica local y muestran:

```text
No se puede cargar el archivo ... porque la ejecucion de scripts esta deshabilitada en este sistema.
```

Por eso el comando copiado desde el login usa `-ExecutionPolicy Bypass` solo en ese proceso
de PowerShell, despues de validar el SHA-256 del script descargado:

```powershell
powershell -ExecutionPolicy Bypass -NoProfile -File $p -ServerUrl "$u/api/v1/equipos/inventario"
```

No cambia la politica permanente de Windows y no reemplaza la verificacion del hash.

## Rollback basico

Volver al commit anterior conocido y reconstruir:

```bash
cd /opt/inventario-modular
git log --oneline -5
git checkout COMMIT_ANTERIOR
sh ./mvnw --batch-mode -DskipTests package
sudo systemctl restart inventario-modular.service
```

No ejecutar rollback contra base de datos sin revisar las migraciones aplicadas por Flyway.
