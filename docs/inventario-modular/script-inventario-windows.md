# Script de inventario Windows

## Objetivo

El script Windows captura datos basicos de una PC y los envia al endpoint API-first de
Inventario Modular:

```text
POST /api/v1/equipos/inventario
```

Es la primera version modular del flujo que antes resolvia `inventario.ps1` en el sistema
viejo. No reemplaza todavia toda la profundidad del script heredado: deja funcionando el
camino minimo confiable para cargar equipos reales y despues sumar componentes con mas
detalle.

## Archivo servido por la app

```text
src/main/resources/static/scripts/windows/inventario-modular.ps1
```

Cuando la app esta levantada, el script se puede descargar desde el mismo servidor:

```text
http://IP_DEL_SERVIDOR:8081/scripts/windows/inventario-modular.ps1
```

La app tambien publica el hash SHA-256 del script:

```text
http://IP_DEL_SERVIDOR:8081/scripts/windows/inventario-modular.ps1.sha256
```

## Datos capturados

- nombre de PC;
- ultimo usuario local logueado;
- fuero opcional por parametro o variable de entorno;
- primera IPv4 util;
- sistema operativo;
- procesador;
- RAM total en MB;
- detalle y seriales de RAM;
- modelos y seriales de discos;
- modelo y serial de motherboard;
- monitores detectados;
- teclado y mouse;
- impresora predeterminada o primera impresora fisica detectada;
- estado activo.

No captura salud SMART en esta etapa.

## Copiar desde el login

La pantalla `/login` muestra un comando listo para copiar. Ese comando usa
`window.location.origin`, por eso toma automaticamente la IP y puerto desde donde se abrio
el login.

Antes de ejecutar, el comando:

1. descarga el hash SHA-256 publicado por el servidor;
2. descarga el script;
3. calcula el SHA-256 local del archivo descargado;
4. compara ambos valores;
5. ejecuta el script solo si coinciden.

Ejemplo: si se abre el login en:

```text
http://192.168.1.8:8081/login
```

el comando copiado descarga el script desde:

```text
http://192.168.1.8:8081/scripts/windows/inventario-modular.ps1
```

y envia el reporte a:

```text
http://192.168.1.8:8081/api/v1/equipos/inventario
```

## Uso local

Con la app levantada en la misma maquina:

```powershell
$u='http://localhost:8081'; $p="$env:TEMP\inventario-modular.ps1"; $wc=New-Object Net.WebClient; $h=$wc.DownloadString("$u/scripts/windows/inventario-modular.ps1.sha256").Trim(); $wc.DownloadFile("$u/scripts/windows/inventario-modular.ps1",$p); $sha=[System.Security.Cryptography.SHA256]::Create(); $fs=[System.IO.File]::OpenRead($p); try{$a=([BitConverter]::ToString($sha.ComputeHash($fs))).Replace('-','').ToLowerInvariant()}finally{$fs.Close()}; if($a -ne $h){throw "SHA-256 invalido. Script descargado no coincide con el publicado por el servidor."}; powershell -ExecutionPolicy Bypass -NoProfile -File $p -ServerUrl "$u/api/v1/equipos/inventario"
```

Para apuntar a la IP LAN de la maquina de Gustavo:

```powershell
$u='http://192.168.1.8:8081'; $p="$env:TEMP\inventario-modular.ps1"; $wc=New-Object Net.WebClient; $h=$wc.DownloadString("$u/scripts/windows/inventario-modular.ps1.sha256").Trim(); $wc.DownloadFile("$u/scripts/windows/inventario-modular.ps1",$p); $sha=[System.Security.Cryptography.SHA256]::Create(); $fs=[System.IO.File]::OpenRead($p); try{$a=([BitConverter]::ToString($sha.ComputeHash($fs))).Replace('-','').ToLowerInvariant()}finally{$fs.Close()}; if($a -ne $h){throw "SHA-256 invalido. Script descargado no coincide con el publicado por el servidor."}; powershell -ExecutionPolicy Bypass -NoProfile -File $p -ServerUrl "$u/api/v1/equipos/inventario"
```

Para probar sin enviar:

```powershell
powershell -ExecutionPolicy Bypass -File "$env:TEMP\inventario-modular.ps1" -DryRun
```

## Token

El endpoint acepta autenticacion de maquina por bearer token. En desarrollo local existe
un token de laboratorio, pero en trabajo debe definirse fuera de git:

```powershell
$env:INVENTARIO_REPORT_TOKEN = "TOKEN_REAL_DE_REPORTE"
```

La app debe arrancar con el mismo valor:

```powershell
$env:INVENTARIO_REPORT_TOKEN = "TOKEN_REAL_DE_REPORTE"
.\mvnw.cmd spring-boot:run -Dspring-boot.run.profiles=local
```

En Ubuntu/systemd se debe cargar en el `EnvironmentFile` del servicio, no en el repositorio.

No publicar el token real dentro del HTML del login. Si se configura un token real en el
servidor, pasarlo al equipo inventariado por una via administrada, por ejemplo:

```powershell
$env:INVENTARIO_REPORT_TOKEN = "TOKEN_REAL_DE_REPORTE"
```

Luego ejecutar el comando copiado desde el login.

## Fuero

Si no se informa fuero, el backend intenta detectarlo por prefijo del nombre de PC y, si el
equipo ya existia, conserva el fuero anterior.

Para mandarlo explicitamente:

```powershell
powershell -ExecutionPolicy Bypass -NoProfile -File "$env:TEMP\inventario-modular.ps1" `
  -Fuero "Dpto. Informatica San Pedro"
```

O por variable de entorno:

```powershell
$env:INVENTARIO_FUERO = "Dpto. Informatica San Pedro"
powershell -ExecutionPolicy Bypass -NoProfile -File "$env:TEMP\inventario-modular.ps1"
```

## Seguridad operativa

- El script no abre puertos.
- El script no instala servicios.
- El script no queda corriendo en segundo plano.
- El script no modifica configuracion del equipo.
- El script lee inventario por CIM/WMI y envia un POST al servidor.
- El uso normal usa `ExecutionPolicy Bypass` solo para el proceso actual de PowerShell,
  despues de validar el SHA-256 publicado por el servidor. No modifica la politica
  permanente de Windows.
- El comando de descarga usa `System.Net.WebClient` para evitar depender de
  `Invoke-WebRequest`, que no esta disponible en PowerShell 2.0 de Windows 7.

## Firewall, antivirus y Windows 7

El script debe ejecutarse de forma visible y administrada, no ocultarse del firewall ni del
antivirus. La forma correcta de evitar bloqueos falsos es:

- publicar el servidor en una IP/puerto permitidos por la red;
- preferir HTTP/HTTPS saliente hacia el servidor, sin abrir puertos en las PCs;
- crear una regla administrada de salida hacia `IP_DEL_SERVIDOR:8081` o mover el servicio a
  80/443 detras de un reverse proxy;
- usar token real de reporte fuera de git;
- validar siempre el SHA-256 del script descargado;
- firmar el script con certificado interno si se va a desplegar masivamente;
- registrar en documentacion interna que el script usa WMI/CIM y envia un POST de inventario.

Compatibilidad esperada:

- Windows 10/11: compatible con PowerShell moderno.
- Windows 7 con PowerShell 2.0: compatible en modo basico por WMI y `WebClient`; algunas
  lecturas de hardware pueden venir incompletas segun permisos, drivers o version de WMI.
- Windows 7 con PowerShell 3.0 o superior: mejor compatibilidad para CIM, aunque el script
  conserva fallback WMI.

## Respaldo local, no reenvio automatico

Si el servidor no responde, el script guarda el JSON en:

```text
C:\ProgramData\InventarioModular
```

Ese archivo permite reenviar o analizar el reporte cuando vuelva la conectividad.

El "reenvio automatico" seria un paso posterior: el script podria revisar esa carpeta al
arrancar y mandar al servidor los reportes que quedaron pendientes. Todavia no se implementa
para mantener este primer flujo simple y visible.

## Pendiente

- definir cola de reenvio automatico de reportes pendientes;
- rotar el token de laboratorio antes de usarlo fuera de casa;
- separar permisos de maquina por sede o segmento de red si se instala masivamente.
