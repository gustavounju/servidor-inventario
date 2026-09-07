# Modulo Actas

`ACTAS` registra constancias administrativas asociadas al inventario: entregas,
recepciones, devoluciones, traslados, bajas u otras actuaciones internas.

## Alcance implementado

- Migracion Flyway `V10__actas_ubicaciones.sql`.
- Tabla `actas` con numero unico, tipo, equipo opcional, fecha, destinatario,
  responsables, detalle, estado y observaciones.
- API protegida por permisos:

```text
GET  /api/v1/actas
GET  /api/v1/actas/proximo-numero
GET  /api/v1/actas/{id}/pdf
POST /api/v1/actas
PUT  /api/v1/actas/{id}
```

- Pantalla administrativa:

```text
/admin/actas
```

- Filtros por texto, tipo y estado.
- Alta y edicion desde pantalla si el usuario tiene `ACTAS:EDITAR`.
- Numeracion automatica por anio con formato `ACT-AAAA-0001` cuando se crea un acta sin
  numero manual.
- Sugerencia de proximo numero en pantalla y API.
- Asociacion opcional a un equipo existente.
- Auditoria al crear y actualizar.
- PDF/impresion formal de cada acta desde la pantalla y la API.
- CSV desde Reportes:

```text
GET /api/v1/reportes/actas.csv
```

## Estados

```text
BORRADOR
EMITIDA
ANULADA
```

## Tipos

```text
ENTREGA
RECEPCION
DEVOLUCION
TRASLADO
BAJA
OTRA
```

## Pendientes

- Evaluar numeracion por dependencia si el circuito administrativo lo requiere.
- Adjuntos y firmas.
- Vincular actas con bienes patrimoniales y componentes, no solo con equipos.
