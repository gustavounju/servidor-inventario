# Modulo Ubicaciones

`UBICACIONES` registra oficinas, depositos, salas y racks donde se encuentran equipos,
muebles, patrimonio o stock. Es la base para ordenar fisicamente el inventario y para
futuros mapas internos.

## Alcance implementado

- Migracion Flyway `V10__actas_ubicaciones.sql`.
- Tabla `ubicaciones` con codigo unico, nombre, tipo, fuero, responsable, edificio,
  piso, estado y observaciones.
- API protegida por permisos:

```text
GET  /api/v1/ubicaciones
POST /api/v1/ubicaciones
PUT  /api/v1/ubicaciones/{id}
```

- Pantalla administrativa:

```text
/admin/ubicaciones
```

- Filtros por texto, tipo y estado.
- Alta y edicion desde pantalla si el usuario tiene `UBICACIONES:EDITAR`.
- Selectores de ubicacion en equipos, componentes, muebles, patrimonio y stock.
- Auditoria al crear y actualizar.
- CSV desde Reportes:

```text
GET /api/v1/reportes/ubicaciones.csv
```

## Estados

```text
ACTIVA
INACTIVA
```

## Tipos

```text
OFICINA
DEPOSITO
SALA
RACK
OTRA
```

## Pendientes

- Definir jerarquia edificio/piso/oficina si el mapa interno crece.
- Agregar conteos por ubicacion.
- Exportar mapa operativo por fuero o dependencia.
