# Inventario Modular Java

## Dolor real

La migracion experimental a Inventario Next no resolvio el problema principal de
autenticacion con Active Directory y genero friccion operativa con administradores de base
de datos y servidores. El sistema original sigue funcionando para flujos importantes como
equipos, actas y OVMelos, pero arrastra deuda tecnica y no ofrece una base modular clara
para crecer hacia muebles, patrimonio, componentes, stock, usuarios y reportes.

## Reformulacion

No se busca solo cambiar de lenguaje. Se busca crear un sistema nuevo, limpio y modular en
Java, copiando la logica operativa validada del inventario original sin arrastrar codigo
heredado ni decisiones tecnicas que no funcionaron.

## Nombre

- Nombre de producto: Inventario Modular
- Carpeta sugerida: `inventario-modular`
- Base de datos local de desarrollo: `inventario_modular`

## Decision de stack

- Backend: Java 21 con Spring Boot
- Arquitectura: API-first para futura app movil
- Frontend inicial: panel administrativo minimo con Thymeleaf, HTML, CSS y JavaScript simple
- Base de datos: MySQL
- Seguridad: Spring Security
- Autenticacion empresarial: Active Directory via LDAP
- Autorizacion interna: roles, permisos y modulos guardados en MySQL

## Principio de seguridad

Active Directory autentica identidad: confirma que el usuario existe en el dominio y que
su clave es correcta. Inventario Modular autoriza acciones: decide que modulos ve el
usuario y que permisos tiene dentro de cada modulo.

El sistema no debe guardar claves del dominio en MySQL.

## Modulos iniciales

- EQUIPOS
- ACTAS
- MUEBLES
- PATRIMONIO
- STOCK
- COMPONENTES
- USUARIOS
- REPORTES
- TAREAS

`MUEBLES` queda como modulo propio porque representa gestion fisica y operativa de bienes
muebles. `PATRIMONIO` queda separado para control institucional, numeracion patrimonial,
auditoria y reportes administrativos.

## Modelo de permisos

Cada usuario validado por dominio puede tener roles y permisos locales. Los roles pueden
habilitar modulos completos, y los permisos definen acciones dentro del modulo.

Permisos base:

- VER
- CREAR
- EDITAR
- ELIMINAR
- EXPORTAR
- ADMINISTRAR

Ejemplos:

- ADMINISTRADOR: todos los modulos y permisos.
- TECNICO: equipos, actas, tareas, componentes y stock segun necesidad.
- PATRIMONIO: muebles, patrimonio, componentes y reportes.
- LECTOR: solo consulta.
- PERSONALIZADO: combinacion manual de modulos y permisos.

## Flujo de login

```text
Usuario ingresa usuario/clave
  -> Spring Security recibe el intento
  -> LDAP valida contra Active Directory
  -> si AD rechaza, no se consulta permisos locales
  -> si AD acepta, se busca el usuario en MySQL
  -> se cargan roles, permisos y modulos habilitados
  -> la API y el panel muestran solo los modulos autorizados
```

## Premisas aceptadas

1. La nueva app arranca en Java desde cero, en un directorio limpio.
2. Produccion queda totalmente fuera durante esta primera etapa.
3. Se crea una base local nueva llamada `inventario_modular`.
4. El primer nucleo a construir es usuarios, roles, permisos, modulos y login con Active
   Directory.
5. La base vieja se conserva como referencia y futura fuente de migracion, no como modelo
   estructural obligatorio.

## Primer alcance recomendado

Crear una aplicacion Spring Boot minima con:

- Login contra Active Directory.
- Tabla local de usuarios autorizados.
- Tablas de roles, permisos y modulos.
- API inicial que informa los modulos autorizados.
- Panel inicial que muestra un mosaico/menu solo con modulos permitidos.
- Un usuario administrador inicial definido por configuracion local o seed controlado.

Fuera de alcance inicial:

- Migrar equipos.
- Migrar actas.
- Migrar patrimonio.
- Conectar produccion.
- Escribir o modificar datos de la base remota.

## Casos borde a resolver en el diseno tecnico

- AD no disponible.
- Usuario valido en AD pero no dado de alta en Inventario Modular.
- Usuario desactivado localmente.
- Usuario sin modulos asignados.
- Rol modificado mientras el usuario tiene sesion abierta.
- Intento de acceder por URL directa a un modulo oculto.
- Error de conexion a MySQL local.

## Plan de tests pendiente

- Login exitoso con usuario de dominio y usuario local autorizado.
- Login rechazado por AD.
- Login rechazado porque el usuario no existe localmente.
- Usuario con un solo modulo ve solo ese modulo.
- Usuario sin permiso recibe 403 al entrar por URL directa.
- Administrador ve todos los modulos.
- No se persisten ni se loguean claves del dominio.

## Nota de entorno local

Al momento de esta decision, la maquina tenia Java 8 en PATH y no tenia `mvn` ni `mysql`
en PATH. Se instalo JDK 21 con `winget install EclipseAdoptium.Temurin.21.JDK`.
El paquete `Apache.Maven` no existe en el catalogo local de winget, por lo que Maven debe
instalarse con `choco install maven -y` o manualmente desde Apache Maven. MySQL local
responde en `127.0.0.1:3306`.

Ver tambien:

- `docs/inventario-modular/README.md`
- `docs/inventario-modular/instalacion-desde-cero.md`
- `docs/inventario-modular/requerimientos-sistema.md`
- `docs/inventario-modular/plan-de-trabajo.md`
- `docs/decisions/ADR-002-inventario-modular-api-first.md`
