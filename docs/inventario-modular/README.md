# Inventario Modular

Documentacion inicial del nuevo sistema de inventario en Java para el Departamento de
Informatica del Centro Judicial San Pedro.

## Objetivo

Crear un sistema nuevo, limpio y modular en Java, sin arrastrar codigo heredado del
inventario original ni de experimentos frontend descartados. El sistema debe conservar la
logica operativa que si funciona hoy, pero con una arquitectura preparada para crecer por
modulos y para exponer una futura app movil sin rehacer el backend.

## Decision principal

Inventario Modular se disena como una aplicacion **API-first**:

- Backend Java con Spring Boot.
- Base de datos MySQL local nueva en desarrollo: `inventario_modular`.
- Autenticacion contra Active Directory.
- Autorizacion propia en MySQL mediante usuarios, roles, permisos y modulos.
- Cliente web administrativo solo cuando sea necesario.
- Futura app movil consumiendo la misma API.

## Estado actual

El proyecto base ya existe en `inventario-modular/` y usa Java 21 con Maven Wrapper
(`mvnw.cmd`), por lo que no depende de tener `mvn` instalado globalmente.

Primer arranque local:

```powershell
cd inventario-modular
.\mvnw.cmd spring-boot:run
```

Servidor local:

```text
http://192.168.1.8:8081/
http://192.168.1.8:8081/api/v1/health
```

El endpoint inicial responde:

```json
{"status":"ok","service":"inventario-modular"}
```

Por ahora el arranque local excluye temporalmente DataSource, JPA y Flyway hasta configurar
la base `inventario_modular` y las migraciones iniciales. No se conecta a produccion.

## Documentos

- [Instalacion desde cero](./instalacion-desde-cero.md)
- [Requerimientos del sistema](./requerimientos-sistema.md)
- [Plan de trabajo](./plan-de-trabajo.md)
- [Decision tecnica API-first y app movil](../decisions/ADR-002-inventario-modular-api-first.md)

## Alcance inicial

El primer entregable no es actas, muebles ni stock. El primer entregable es el nucleo de
seguridad y modularidad:

1. Login validado contra Active Directory.
2. Usuarios internos vinculados a usuarios de dominio.
3. Roles y permisos administrables.
4. Modulos activables por usuario/rol.
5. API protegida que rechaza accesos sin permiso.
6. Panel minimo para administrar usuarios, roles, permisos y modulos.

## Principio rector

Active Directory confirma identidad. Inventario Modular decide autorizacion.

El sistema no guarda claves del dominio.
