# Auditoria Transversal

## Objetivo

El modulo `AUDITORIA` guarda eventos relevantes de los flujos que ya modifican datos
operativos del inventario.

La primera version se enfoca en:

```text
COMPONENTES
STOCK
ORDENES_ARMADO
```

Esto permite reconstruir quien hizo un alta, una correccion, una reserva, una salida real
desde stock o una consolidacion del gemelo digital.

## Migracion

La migracion Flyway esta en:

```text
src/main/resources/db/migration/V7__auditoria_transversal.sql
```

Crea:

- Modulo `AUDITORIA`.
- Permisos iniciales para el rol `ADMINISTRADOR`.
- Tabla `auditoria_eventos`.

Campos principales:

- `usuario`: usuario autenticado o `SISTEMA` cuando no hay contexto de seguridad.
- `modulo`: modulo donde ocurrio el cambio.
- `accion`: accion registrada.
- `entidad_tipo`: tipo de entidad afectada.
- `entidad_id`: identificador de la entidad afectada.
- `detalle`: resumen breve del cambio.
- `creado_en`: fecha y hora del evento.

## Eventos registrados

Componentes:

- `CREAR`
- `ACTUALIZAR`
- `CONSOLIDAR_RELEVAMIENTO_INICIAL`
- `REGISTRAR_SCRIPT`

Stock:

- `CREAR`
- `ACTUALIZAR`
- `RESERVAR`
- `ASIGNAR`

Ordenes de armado:

- `CREAR`
- `ACTUALIZAR`
- `AGREGAR_COMPONENTE`
- `CONFIRMAR_SALIDA_STOCK`

## Pantalla

La consulta visual esta disponible en:

```text
/admin/auditoria
```

Muestra los eventos recientes con fecha, usuario, modulo, accion, entidad y detalle.

## API

Listar eventos recientes:

```http
GET /api/v1/auditoria/eventos
```

Requiere:

```text
AUDITORIA:VER
```

La respuesta devuelve los ultimos eventos ordenados del mas reciente al mas antiguo.

## Pendiente

- Agregar filtros por fecha, modulo, usuario y entidad.
- Exportar eventos.
- Registrar cambios de usuarios, roles, claves locales y autorizaciones AD.
