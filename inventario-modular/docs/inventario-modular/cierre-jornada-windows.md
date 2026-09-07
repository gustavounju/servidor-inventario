# Cierre De Jornada Windows

Fecha: 2026-08-28

Este documento registra lo realizado desde Windows en casa, sin acceso al servidor Ubuntu
de produccion.

## Contexto

El trabajo se hizo en una maquina Windows local. No se accedio al servidor de produccion,
no se ejecuto PuTTY y no se modifico ninguna base de datos remota.

## Proyecto creado

Se creo un repositorio nuevo, separado del inventario viejo:

```text
G:\unju2025\google gravity\inventario-modular
```

Rama inicial:

```text
primeros-pasos
```

Repositorio principal GitLab:

```text
https://gitlab.com/gustavoeliasm/inventario-modular
```

Repositorio espejo GitHub:

```text
https://github.com/gustavounju/inventario-modular
```

## Stack inicial

- Java 21 LTS.
- Spring Boot.
- Maven.
- MySQL.
- Flyway.
- Spring Security.
- LDAP / Active Directory.
- Thymeleaf para panel administrativo minimo.

## Paquete Java

El paquete Java quedo alineado con el dominio institucional `justiciajujuy.gov.ar` y la
sede San Pedro:

```java
ar.gov.justiciajujuy.sanpedro.inventario
```

Carpeta:

```text
src/main/java/ar/gov/justiciajujuy/sanpedro/inventario
```

## Entorno local configurado

JDK 21 instalado:

```text
C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot
```

Maven instalado en el perfil del usuario:

```text
C:\Users\Gustavo\tools\apache-maven-3.9.16
```

Variables usadas en PowerShell:

```powershell
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot"
$env:Path = "$env:JAVA_HOME\bin;$env:USERPROFILE\tools\apache-maven-3.9.16\bin;$env:Path"
```

Verificacion:

```powershell
mvn -version
```

Resultado esperado:

```text
Apache Maven 3.9.16
Java version: 21.0.12.1
```

## Validaciones locales realizadas

Integracion continua local:

```powershell
mvn test
```

Resultado:

```text
Tests run: 1, Failures: 0, Errors: 0
BUILD SUCCESS
```

Construccion del artefacto:

```powershell
mvn -DskipTests package
```

Resultado:

```text
BUILD SUCCESS
```

Artefacto generado:

```text
target/inventario-modular-0.0.1-SNAPSHOT.jar
```

## CI/CD

Se agrego `.gitlab-ci.yml` con dos etapas:

```text
validar -> construir
```

La etapa `validar` ejecuta tests. La etapa `construir` genera el `.jar` como artefacto.

Todavia no hay despliegue automatico a produccion.

## Estado de base de datos

La base definida para desarrollo/laboratorio es:

```text
inventario_modular
```

En Windows se verifico que MySQL local escucha en:

```text
127.0.0.1:3306
```

Eso corresponde solo al entorno de casa/desarrollo. En el trabajo, la base MySQL esta en
otro servidor con IP `10.15.0.62`, por lo que el servidor Ubuntu de la aplicacion debe usar:

```text
jdbc:mysql://10.15.0.62:3306/inventario_modular
```

Pendiente:

- Crear la base local si todavia no existe.
- Crear la base en `10.15.0.62` solo si el DBA/admin lo autoriza.
- Definir usuario MySQL para la app, autorizado desde la IP/host del servidor Ubuntu.
- Crear migraciones Flyway iniciales.

## Regla de remotos

- GitLab es el remoto principal de trabajo.
- GitHub es copia/espejo para practica de versionado.
- El asistente puede subir a GitLab.
- Gustavo sincroniza GitHub manualmente con:

```powershell
cd "G:\unju2025\google gravity\inventario-modular"
git push github primeros-pasos
```

## Punto de detencion

Se detiene el trabajo antes de acceder al servidor Ubuntu. Lo siguiente debe hacerse en el
trabajo, conectado por PuTTY/SSH y con cuidado de no afectar el inventario actual.
