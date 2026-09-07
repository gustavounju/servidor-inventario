# Base De Datos Local Windows

Guia para crear la base MySQL local de Inventario Modular en una maquina Windows de casa.

## Alcance

Estos pasos son solo para desarrollo local. No se conectan al servidor MySQL del trabajo
`10.15.0.62` y no tocan ninguna base de produccion.

## Datos locales

```text
Host: 127.0.0.1
Puerto: 3306
Base: inventario_modular
Usuario de aplicacion: inventario_local
```

## Paso 1: Verificar que MySQL responde

Desde PowerShell:

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 3306
```

La salida correcta debe incluir:

```text
TcpTestSucceeded : True
```

Si da `False`, MySQL no esta iniciado, no esta instalado o escucha en otro puerto.

## Paso 2: Verificar cliente mysql

```powershell
mysql --version
```

Si PowerShell responde que `mysql` no se reconoce, hay que usar la ruta completa del
cliente MySQL o agregar su carpeta `bin` al `Path`.

Rutas habituales:

```text
C:\Program Files\MySQL\MySQL Server 8.0\bin
C:\Program Files\MariaDB 11.4\bin
```

Ejemplo con ruta completa:

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
```

## Paso 3: Entrar como administrador MySQL local

```powershell
mysql -u root -p
```

MySQL pedira la clave del usuario `root` local. Esa clave no debe guardarse en git ni en
documentacion.

## Paso 4: Crear base y usuario local

Opcion recomendada: ejecutar el SQL documentado del proyecto desde MySQL.

```powershell
cd "G:\unju2025\google gravity\inventario-modular"
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p
```

MySQL pedira la clave local de `root`. Esa clave se escribe en la terminal de MySQL, no
en git ni en este documento.

Dentro de MySQL ejecutar:

```sql
SOURCE G:/unju2025/google gravity/inventario-modular/docs/inventario-modular/sql/crear-base-local-mysql.sql;
EXIT;
```

Alternativa grafica: abrir MySQL Workbench, conectarse como `root`, abrir el archivo
`docs/inventario-modular/sql/crear-base-local-mysql.sql` y ejecutarlo.

El archivo ejecutado contiene:

```sql
CREATE DATABASE IF NOT EXISTS inventario_modular
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'inventario_local'@'localhost'
  IDENTIFIED BY 'Cambiar_Clave_Local_123!';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
  ON inventario_modular.* TO 'inventario_local'@'localhost';

FLUSH PRIVILEGES;
```

Si el usuario ya existia y se quiere cambiar la clave local:

```sql
ALTER USER 'inventario_local'@'localhost'
  IDENTIFIED BY 'Cambiar_Clave_Local_123!';

FLUSH PRIVILEGES;
```

## Paso 5: Verificar permisos

```sql
SHOW DATABASES LIKE 'inventario_modular';
SHOW GRANTS FOR 'inventario_local'@'localhost';
```

Salir:

```sql
EXIT;
```

## Paso 6: Probar conexion con el usuario de la app

Desde PowerShell:

```powershell
mysql -u inventario_local -p -h 127.0.0.1 inventario_modular
```

Ingresar la clave local configurada. Si conecta, salir con:

```sql
EXIT;
```

## Paso 7: Variables para ejecutar Spring Boot

Antes de ejecutar Maven, si PowerShell muestra:

```text
mvn : El termino 'mvn' no se reconoce
```

cargar Java y Maven en esa terminal:

```powershell
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot"
$env:Path = "$env:JAVA_HOME\bin;$env:USERPROFILE\tools\apache-maven-3.9.16\bin;$env:Path"
```

Verificar:

```powershell
mvn -version
```

La configuracion `local` intenta primero la base modular remota del trabajo y luego cae a
MySQL local. Para casa, estos son los valores de fallback por defecto:

```properties
inventario.datasource.fallback.url=jdbc:mysql://127.0.0.1:3306/inventario_modular
inventario.datasource.fallback.username=inventario_local
inventario.datasource.fallback.password=Cambiar_Clave_Local_123!
```

Por eso, despues de crear la base y el usuario, alcanza con ejecutar:

```powershell
mvn spring-boot:run
```

Si se quiere usar otra clave local, en la misma PowerShell donde se va a iniciar la app:

```powershell
$env:INVENTARIO_DB_FALLBACK_URL = "jdbc:mysql://127.0.0.1:3306/inventario_modular"
$env:INVENTARIO_DB_FALLBACK_USER = "inventario_local"
$env:INVENTARIO_DB_FALLBACK_PASSWORD = "Cambiar_Clave_Local_123!"
```

Estas variables viven solo en esa terminal. No se commitean.

## Verificacion realizada en Windows

En la maquina local se confirmo:

```text
MySQL80: Running
Base: inventario_modular
Usuario de app: inventario_local@localhost
Tablas creadas por Flyway: version 3 - seguridad modular, credenciales locales y equipos
Usuarios iniciales: 1
Modulos iniciales: 9
Roles iniciales: 5
Login local: admin.local -> /admin
Modo mostrado por la app: LOCAL, MySQL local, usuarios locales
```

## Comandos prohibidos

No usar estos comandos durante la instalacion local normal:

```sql
DROP DATABASE inventario_modular;
DROP USER 'inventario_local'@'localhost';
```

Si alguna vez hiciera falta borrar una base, se decide aparte y con backup.
