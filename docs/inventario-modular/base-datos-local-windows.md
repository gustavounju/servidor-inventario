# Base De Datos Local Windows

Guia para preparar Inventario Modular en una PC Windows usando MySQL local.
Este flujo aplica para trabajo local en el edificio y evita usar H2 como base de prueba
principal.

## Alcance

Estos pasos usan solo `127.0.0.1:3306`. No se conectan al servidor MySQL de produccion
`10.15.0.62` y no modifican datos reales.

Produccion sigue usando MySQL remoto mediante variables del servicio Ubuntu. Local sigue
usando MySQL local por defecto.

## Datos locales

```text
Host: 127.0.0.1
Puerto: 3306
Base: inventario_modular
Usuario de aplicacion: inventario_local
```

## Paso 1: Verificar MySQL local

Desde PowerShell:

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 3306
```

La salida correcta debe incluir:

```text
TcpTestSucceeded : True
```

En esta PC se detecto el servicio `MySQL84` en estado `Running` y el cliente:

```text
C:\Program Files\MySQL\MySQL Server 8.4\bin\mysql.exe
```

## Paso 2: Crear o reparar la base local

Ejecutar el script del repo:

```powershell
.\scripts\setup-local-mysql.ps1
```

El script pide la clave de `root` de MySQL local en la consola. No escribir claves en
documentos, commits ni chat.

El script crea o actualiza:

```text
Base: inventario_modular
Usuario: inventario_local
```

Si aparece:

```text
Access denied for user 'inventario_local'@'localhost'
```

significa que MySQL local responde, pero el usuario `inventario_local` no existe, no tiene
permisos sobre `inventario_modular` o la clave ingresada no coincide. Ejecutar
`setup-local-mysql.ps1` corrige ese estado.

## Paso 3: Arrancar local con MySQL y Active Directory

Con la base local preparada:

```powershell
.\scripts\start-local-ad.ps1
```

El script pide:

```text
Usuario MySQL LOCAL [inventario_local]
Clave MySQL LOCAL
Usuario lector AD
Clave AD
```

Formatos aceptados para AD:

```text
PODJUDSP\usuario
usuario@podjudsp.local
```

Al iniciar, imprime:

```text
http://localhost:8081
http://IP-DE-LA-PC:8081/movil/login
```

La segunda URL es la que debe probarse desde el celular.

## Configuracion aplicada

El perfil `local` usa MySQL local por defecto:

```properties
inventario.datasource.primary.url=jdbc:mysql://127.0.0.1:3306/inventario_modular
inventario.datasource.primary.username=inventario_local
```

Para produccion, la unidad systemd o el archivo de entorno del servidor debe definir:

```text
SPRING_PROFILES_ACTIVE=local
INVENTARIO_DB_PRIMARY_URL=jdbc:mysql://10.15.0.62:3306/inventario_modular
INVENTARIO_DB_PRIMARY_USER=inventario_modular_app
INVENTARIO_DB_PRIMARY_PASSWORD=...
```

Esa clave vive solo en `/etc/inventario-modular/inventario-modular.env` del servidor
Ubuntu y no se versiona.

## Modo H2

El perfil `casa` con H2 queda solo como laboratorio aislado cuando no hay MySQL. No debe
usarse para validar el flujo de trabajo ni para pruebas con celulares en el edificio.

## Comandos prohibidos en el flujo normal

No usar estos comandos durante la instalacion local normal:

```sql
DROP DATABASE inventario_modular;
DROP USER 'inventario_local'@'localhost';
```

Si alguna vez hiciera falta borrar una base, se decide aparte y con backup.
