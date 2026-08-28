# Requerimientos Del Sistema

## Vision

Inventario Modular debe ser el reemplazo moderno del inventario actual, construido desde
cero en Java, con arquitectura modular y preparado para una futura app movil real.

La prioridad no es tener una web responsive para tecnicos. La prioridad es que el backend
exponga una API estable para que una app movil futura pueda usar las mismas reglas de
negocio, seguridad y permisos.

## Usuarios principales

- Administrador del sistema.
- Tecnico de Informatica.
- Personal de patrimonio.
- Usuario lector o de consulta.
- Usuarios personalizados con permisos limitados.

## Modulos previstos

- EQUIPOS
- ACTAS
- MUEBLES
- PATRIMONIO
- STOCK
- COMPONENTES
- USUARIOS
- REPORTES
- TAREAS

## Gestion de usuarios

El sistema debe permitir:

- Vincular usuarios internos con usuarios de Active Directory.
- Validar usuario y clave contra Active Directory al iniciar sesion.
- Administrar roles locales.
- Administrar permisos locales.
- Administrar visibilidad de modulos.
- Desactivar usuarios sin borrar historial.
- Rechazar usuarios validos en AD que no esten autorizados localmente.

## Roles base

- ADMINISTRADOR: acceso total.
- TECNICO: acceso operativo a modulos tecnicos.
- PATRIMONIO: acceso a muebles, patrimonio, componentes y reportes.
- LECTOR: solo lectura.
- PERSONALIZADO: permisos definidos manualmente.

## Permisos base

- VER
- CREAR
- EDITAR
- ELIMINAR
- EXPORTAR
- ADMINISTRAR

## Regla de autenticacion y autorizacion

Active Directory autentica:

```text
El usuario existe y la clave es correcta.
```

Inventario Modular autoriza:

```text
El usuario puede entrar al sistema y usar estos modulos con estos permisos.
```

## Requerimientos para futura app movil

El backend debe:

- Exponer API REST versionada, por ejemplo `/api/v1`.
- No depender de sesiones HTML como unica forma de autenticacion.
- Poder emitir tokens o manejar sesiones compatibles con cliente movil.
- Centralizar permisos en servicios reutilizables.
- Responder 401 cuando no hay autenticacion.
- Responder 403 cuando el usuario esta autenticado pero no autorizado.
- Mantener contratos estables para modulos, usuarios y permisos.
- Evitar que la logica de negocio viva solo en templates HTML.

## Entregable inicial

Primer entregable esperado:

- Proyecto Java limpio.
- Base local `inventario_modular`.
- Migraciones iniciales.
- Login contra Active Directory.
- Registro local de usuarios autorizados.
- Roles, permisos y modulos.
- API para obtener modulos permitidos del usuario autenticado.
- Panel administrativo minimo para gestionar usuarios y permisos.

## Fuera de alcance inicial

- Migrar produccion.
- Escribir en base remota.
- Reemplazar todavia el inventario original.
- Implementar app movil nativa.
- Migrar actas, equipos, muebles, stock o patrimonio.

## Criterios de aceptacion iniciales

- Un usuario con clave incorrecta en AD no entra.
- Un usuario valido en AD pero no registrado en MySQL no entra.
- Un usuario desactivado localmente no entra.
- Un usuario sin permiso para un modulo no lo ve.
- Un usuario sin permiso para un modulo recibe 403 si intenta entrar por URL/API.
- Un administrador ve todos los modulos.
- No se guardan claves de dominio en MySQL.
- No se registran claves en logs.
