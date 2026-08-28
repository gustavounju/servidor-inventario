# Instalacion Desde Cero

Guia para preparar una maquina Windows de desarrollo para Inventario Modular Java.

## Estado actual observado

En la maquina de desarrollo se detecto:

- Java actual en PATH: OpenJDK 8 de Red Hat.
- Maven no disponible en PATH.
- Cliente `mysql` no disponible en PATH.
- MySQL local escuchando en `127.0.0.1:3306`.
- `winget` disponible.
- Chocolatey disponible.

## Paso 1: Instalar JDK 21 LTS

Usar JDK 21 LTS, no JDK 22. Java 21 es moderno, estable y adecuado para Spring Boot en un
entorno institucional. Java 22 fue una version intermedia, no una base recomendable para
un sistema que se espera mantener durante anos.

Comando:

```powershell
winget install EclipseAdoptium.Temurin.21.JDK
```

Salida esperada aproximada:

```text
Encontrado Eclipse Temurin JDK with Hotspot 21
Descargando OpenJDK21U-jdk_x64_windows_hotspot...
El hash del instalador se verifico correctamente
Instalado correctamente
```

Despues de instalar, cerrar y abrir PowerShell.

Verificar:

```powershell
java -version
javac -version
```

Debe aparecer Java 21.

## Paso 2: Instalar Maven

El comando `winget install Apache.Maven` no funciono en esta maquina porque `winget` no
encontro un paquete coincidente. Como Chocolatey si esta instalado y el paquete `maven`
existe, el comando recomendado es:

```powershell
choco install maven -y
```

Despues de instalar, cerrar y abrir PowerShell.

Verificar:

```powershell
mvn -version
```

Debe aparecer Maven 3.9.x o superior.

## Alternativa si Chocolatey esta bloqueado

Si en una maquina del trabajo no se permite instalar Maven con Chocolatey:

1. Descargar Apache Maven desde el sitio oficial.
2. Descomprimirlo en una carpeta estable, por ejemplo:

```text
C:\tools\apache-maven
```

3. Crear o actualizar la variable de entorno `MAVEN_HOME`:

```text
C:\tools\apache-maven
```

4. Agregar al `Path`:

```text
C:\tools\apache-maven\bin
```

5. Cerrar y abrir PowerShell.
6. Verificar:

```powershell
mvn -version
```

## Paso 3: Verificar MySQL local

Comprobar que MySQL local responde:

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 3306
```

Debe indicar:

```text
TcpTestSucceeded : True
```

## Paso 4: Crear base local nueva

Produccion queda fuera. La primera base es local de desarrollo.

Nombre de base:

```text
inventario_modular
```

Cuando el cliente `mysql` este disponible:

```powershell
mysql -u root -p
```

Dentro de MySQL:

```sql
CREATE DATABASE inventario_modular
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

## Paso 5: Crear el proyecto Java

El proyecto debe crearse en un directorio limpio:

```text
inventario-modular/
```

Stack recomendado:

- Java 21 LTS
- Spring Boot
- Spring Web
- Spring Security
- Spring Data JPA
- Spring LDAP
- MySQL Driver
- Flyway para migraciones
- Validation
- Thymeleaf solo para panel administrativo minimo

## Paso 6: Variables locales

Crear configuracion local con placeholders. No commitear secretos.

Valores esperados:

```properties
spring.datasource.url=jdbc:mysql://127.0.0.1:3306/inventario_modular
spring.datasource.username=usuario_local
spring.datasource.password=CAMBIAR_EN_LOCAL

inventario.ldap.url=ldap://SERVIDOR_AD:389
inventario.ldap.domain=DOMINIO
inventario.ldap.base-dn=DC=ejemplo,DC=local
```

Las credenciales reales deben quedar fuera de git.

## Paso 7: Primer arranque esperado

Cuando el proyecto exista:

```powershell
mvn spring-boot:run
```

El sistema debe iniciar localmente sin conectarse a produccion.

## Pendiente antes de implementar

- Confirmar servidor, puerto y base DN reales de Active Directory.
- Confirmar si se usara LDAP simple, LDAPS o StartTLS.
- Definir usuario administrador inicial.
- Crear migraciones Flyway iniciales.
- Crear pruebas de login y autorizacion.
