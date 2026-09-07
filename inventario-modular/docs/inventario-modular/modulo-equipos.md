# Modulo Equipos

## Objetivo

`EQUIPOS` es el primer modulo funcional de Inventario Modular. Representa el inventario
tecnico de PCs y dispositivos principales que luego alimentaran dashboard, tareas,
reportes, actas, stock asignado y mapas.

Esta primera version no intenta copiar todo el inventario viejo. Define una base limpia y
API-first para empezar a recibir y consultar equipos.

## Datos iniciales

La migracion Flyway esta en:

```text
src/main/resources/db/migration/V3__equipos_inicial.sql
```

Crea la tabla `equipos` con estos campos principales:

- `nombre`: identificador tecnico de la PC o equipo, unico y normalizado en mayusculas.
- `ultimo_usuario`: ultimo usuario informado por el inventario.
- `fuero`: area o fuero asociado.
- `ip`: direccion IPv4 o IPv6 informada.
- `sistema_operativo`: sistema reportado por la PC.
- `procesador`: procesador reportado.
- `ram_mb`: memoria RAM en megabytes.
- `impresora`: impresora asociada o detectada.
- `monitoreo`: estado inicial `SIN_REPORTE` o `REPORTADO`.
- `activo`: permite ocultar o desactivar equipos sin borrar historial.
- `ultimo_reporte_en`: fecha/hora del ultimo reporte recibido.

## API

Los endpoints quedan bajo `/api/v1/equipos`.

### Listar equipos

```http
GET /api/v1/equipos?q=mesa&page=0&pageSize=25
```

Requiere permiso:

```text
EQUIPOS:VER
```

La busqueda `q` filtra por nombre del equipo, ultimo usuario o fuero.

### Ver detalle

```http
GET /api/v1/equipos/{id}
```

Requiere permiso:

```text
EQUIPOS:VER
```

Devuelve los campos de listado mas `procesador`, `ramMb`, `impresora` y
`ultimoReporteEn`.

### Actualizar manualmente

```http
PUT /api/v1/equipos/{id}
```

Requiere permiso:

```text
EQUIPOS:EDITAR
```

Permite corregir o completar datos desde administracion sin depender de un nuevo reporte
del script. El nombre se normaliza a mayusculas y no puede repetirse con otro equipo.

Payload:

```json
{
  "nombre": "PC-INF-001",
  "ultimoUsuario": "gmurad",
  "fuero": "Dpto. Informatica San Pedro",
  "ip": "10.15.2.10",
  "sistemaOperativo": "Windows 11 Pro",
  "procesador": "Intel Core i5",
  "ramMb": 16384,
  "ramDetalles": "2x8GB DDR4",
  "ramSeriales": "RAMSN-001 | RAMSN-002",
  "discosModelos": "KINGSTON SA400",
  "discosSeriales": "DISK-001",
  "motherboardModelo": "Dell 0ABC",
  "motherboardSerial": "MB-001",
  "monitores": "Dell 22 SN MON-001",
  "teclado": "Logitech Keyboard",
  "mouse": "Logitech Mouse",
  "impresora": "HP LaserJet",
  "activo": true
}
```

### Recibir inventario

```http
POST /api/v1/equipos/inventario
```

Requiere permiso:

```text
EQUIPOS:EDITAR
```

Payload:

```json
{
  "nombre": "pc-nueva-003",
  "ultimoUsuario": "jlopez",
  "fuero": "Informatica",
  "ubicacion": "Oficina Informatica",
  "ip": "10.15.2.12",
  "sistemaOperativo": "Windows 11 Pro",
  "procesador": "AMD Ryzen 5",
  "ramMb": 16384,
  "ramDetalles": "2x8GB DDR4 3200MHz",
  "ramSeriales": "RAM-001 | RAM-002",
  "discosModelos": "WD Blue SSD",
  "discosSeriales": "DISK-001",
  "motherboardModelo": "ASUS PRIME",
  "motherboardSerial": "MB-123",
  "monitores": "Samsung 24 SN-456",
  "teclado": "Logitech K120",
  "mouse": "Logitech M90",
  "impresora": "Ricoh Mesa",
  "activo": true
}
```

Script Windows inicial servido por la app:

```text
src/main/resources/static/scripts/windows/inventario-modular.ps1
```

Desde `/login` se puede copiar un comando que toma automaticamente la IP y puerto del
servidor desde donde se abrio la pantalla.

Uso manual local:

```powershell
$u='http://192.168.1.8:8081'; $p="$env:TEMP\inventario-modular.ps1"; $h=(iwr "$u/scripts/windows/inventario-modular.ps1.sha256" -UseBasicParsing).Content.Trim(); iwr "$u/scripts/windows/inventario-modular.ps1" -UseBasicParsing -OutFile $p; $sha=[System.Security.Cryptography.SHA256]::Create(); $fs=[System.IO.File]::OpenRead($p); try{$a=([BitConverter]::ToString($sha.ComputeHash($fs))).Replace('-','').ToLowerInvariant()}finally{$fs.Close()}; if($a -ne $h){throw "SHA-256 invalido. Script descargado no coincide con el publicado por el servidor."}; powershell -ExecutionPolicy Bypass -NoProfile -File $p -ServerUrl "$u/api/v1/equipos/inventario"
```

Guia operativa:

- [Script de inventario Windows](script-inventario-windows.md)
- [Actualizacion de produccion](actualizacion-produccion-inventario-modular.md)

Comportamiento:

- si `nombre` no existe, crea el equipo;
- si `nombre` ya existe, actualiza los datos reportados;
- normaliza `nombre` a mayusculas;
- marca `monitoreo` como `REPORTADO`;
- registra `ultimo_reporte_en`.

### Importar inventario viejo

```http
POST /api/v1/equipos/importar-viejo
Content-Type: text/csv
```

Requiere `EQUIPOS:EDITAR`. Acepta CSV con coma o punto y coma. Encabezados admitidos:
`nombre` o `PC_Nombre`, `ultimoUsuario` o `Usuario_Actual`, `fuero`, `ubicacion`,
`ip` o `IPAddress`, `sistemaOperativo` u `OsName`, `procesador`, `ramMb`, `RAM (GB)`,
`RAM_Detalles`, `RAM_Serials`, `Disk_Models`, `Disk_Serials`, `Motherboard_Model`,
`Motherboard_SN`, `Monitors`, `Keyboard_Model`, `Mouse_Model` y `Printer_Model`.

Ejemplo:

```csv
PC_Nombre;Usuario_Actual;fuero;ubicacion;IPAddress;OsName;Procesador;RAM (GB)
pc-vieja-010;mrojas;Informatica;Oficina Informatica;10.15.2.40;Windows 7 Pro;Intel Core i3;4
```

## Pantalla

La pantalla inicial esta en:

```text
/admin/equipos
```

Se muestra desde `/admin` solo cuando el usuario tiene permiso `EQUIPOS:VER`.

Incluye buscador por PC, usuario o fuero, importacion CSV del inventario viejo, listado
tabular, estado de monitoreo y datos basicos: equipo, ultimo usuario, fuero, IP y sistema
operativo.

El detalle visual esta en:

```text
/admin/equipos/{id}
```

Muestra identidad del equipo, fuero, ultimo usuario, IP, sistema operativo, procesador,
RAM, discos, motherboard, monitores, teclado, mouse, impresora y fecha del ultimo reporte.
Si el usuario tiene `EQUIPOS:EDITAR`, tambien muestra el formulario de edicion manual
controlada para completar datos o activar/desactivar el equipo.

## Seguridad

La autorizacion se resuelve con `AuthorizationService`:

- `GET /api/v1/equipos`: `EQUIPOS:VER`;
- `GET /api/v1/equipos/{id}`: `EQUIPOS:VER`;
- `PUT /api/v1/equipos/{id}`: `EQUIPOS:EDITAR`;
- `POST /api/v1/equipos/inventario`: `EQUIPOS:EDITAR`;
- `POST /api/v1/equipos/importar-viejo`: `EQUIPOS:EDITAR`;
- `/admin/equipos`: `EQUIPOS:VER`.
- `/admin/equipos/{id}`: `EQUIPOS:VER` para detalle y `EQUIPOS:EDITAR` para guardar.

Un usuario autenticado pero sin permisos recibe `403 Forbidden`.

## Pruebas

Tests relacionados:

```text
src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/EquipoControllerTests.java
src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/EquipoPageControllerTests.java
src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/AdminControllerTests.java
```

Comando:

```powershell
mvn "-Dtest=EquipoControllerTests,EquipoPageControllerTests,AdminControllerTests" test
```

## Pendiente

- Incorporar relacion futura con stock, componentes, ubicaciones y actas.
