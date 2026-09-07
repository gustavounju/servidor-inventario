# Modulo Componentes Y Gemelo Digital

## Objetivo

El modulo `COMPONENTES` representa las partes internas y externas vinculadas a un equipo.
Es la primera base concreta del gemelo digital de Inventario Modular.

La idea operativa es:

```text
script de inventario
-> componentes detectados
stock
-> componentes entregados o disponibles
orden de armado
-> componentes esperados
gemelo digital
-> comparacion entre esperado, entregado y detectado
```

## Modelo inicial

La migracion Flyway esta en:

```text
src/main/resources/db/migration/V5__componentes_gemelo_digital.sql
```

Crea la tabla `componentes` con:

- `equipo_id`: equipo al que pertenece el componente.
- `tipo`: RAM, DISCO, MOTHERBOARD, MONITOR, TECLADO, MOUSE, IMPRESORA, CPU, FUENTE,
  GABINETE u OTRO.
- `origen`: SCRIPT, RELEVAMIENTO_INICIAL, STOCK, ORDEN_ARMADO o MANUAL.
- `estado_comparacion`: DETECTADO, ESPERADO, COINCIDE, FALTA, SOBRA o REVISAR.
- `descripcion`: texto principal del componente.
- `marca`, `modelo`, `serial`, `capacidad`, `ubicacion` y `observaciones`.
- `activo`: permite ocultar o desactivar sin borrar historial.

## Proceso confirmado

El flujo acordado para construir el gemelo digital queda asi:

```text
1. Completar COMPONENTES para que el script pueda guardar piezas detectadas.
2. Agregar RELEVAMIENTO_INICIAL como origen de componentes detectados en maquinas viejas.
3. Crear STOCK para cargar componentes sueltos nuevos.
4. Crear ORDENES_ARMADO.
5. Crear pantalla de comparacion del gemelo digital.
```

## Ingesta desde el script

Cuando el script reporta un equipo por:

```http
POST /api/v1/equipos/inventario
```

o por el endpoint compatible con el inventario viejo:

```http
POST /submit_inventory
```

Inventario Modular actualiza la ficha del equipo y tambien registra componentes
detectados con:

```text
origen = SCRIPT
estado_comparacion = DETECTADO
```

Cada nuevo reporte del script reemplaza los componentes anteriores de origen `SCRIPT`
para ese equipo. No borra componentes cargados como `RELEVAMIENTO_INICIAL`, `STOCK`,
`ORDEN_ARMADO` o `MANUAL`.

Componentes detectados en esta etapa:

- CPU.
- RAM.
- Discos.
- Motherboard.
- Monitores.
- Teclado.
- Mouse.
- Impresora.

Para una maquina vieja, esos datos sirven como punto de partida. Luego se podran
consolidar como `RELEVAMIENTO_INICIAL`, dejando una foto base del equipo al comienzo del
inventario.

## Consolidacion de relevamiento inicial

Desde el detalle del equipo se puede consolidar la ultima lectura del script como
`RELEVAMIENTO_INICIAL`.

La accion copia los componentes activos de origen `SCRIPT`, reemplaza el relevamiento
inicial anterior de ese equipo y deja la nueva foto base con:

```text
origen = RELEVAMIENTO_INICIAL
estado_comparacion = DETECTADO
```

No modifica componentes de `STOCK`, `ORDEN_ARMADO` o `MANUAL`.

## API

Listar componentes de un equipo:

```http
GET /api/v1/equipos/{equipoId}/componentes
```

Requiere:

```text
COMPONENTES:VER
```

Crear componente:

```http
POST /api/v1/equipos/{equipoId}/componentes
```

Requiere:

```text
COMPONENTES:EDITAR
```

Actualizar componente:

```http
PUT /api/v1/componentes/{id}
```

Requiere:

```text
COMPONENTES:EDITAR
```

Consolidar lectura de script como relevamiento inicial:

```http
POST /api/v1/equipos/{equipoId}/componentes/consolidar-relevamiento-inicial
```

Requiere:

```text
COMPONENTES:EDITAR
```

Payload:

```json
{
  "tipo": "RAM",
  "origen": "RELEVAMIENTO_INICIAL",
  "estadoComparacion": "DETECTADO",
  "descripcion": "Modulo RAM detectado al iniciar inventario",
  "marca": "Kingston",
  "modelo": "DDR4 2666",
  "serial": "RAMSN-001",
  "capacidad": "8GB",
  "ubicacion": "Slot 1",
  "observaciones": "Base inicial de una maquina vieja",
  "activo": true
}
```

## Pantalla

La primera pantalla esta integrada en:

```text
/admin/equipos/{id}
```

La seccion `Gemelo digital / Componentes` muestra los componentes detectados, esperados o
cargados manualmente. Desde ahi se puede cargar un componente si el usuario tiene
`COMPONENTES:EDITAR`.

La misma seccion incluye la accion `Consolidar lectura como relevamiento inicial`, pensada
para tomar una PC vieja ya reportada por script y dejar su base inicial estable.

## Como se relaciona con Stock

La primera salida real desde stock ya queda conectada con ordenes de armado:

```text
Componente en STOCK
-> se asigna a una orden de armado
-> queda RESERVADO
-> se confirma salida real
-> queda ASIGNADO y como componente ESPERADO de origen STOCK
-> el script o tecnico confirma si COINCIDE, REVISAR, FALTA o SOBRA
```

Esto permite avanzar con el gemelo digital sin esperar a que todo el modulo Stock este
terminado.

## Comparacion automatica

La comparacion trabaja con componentes activos y cruza esperado contra detectado de forma
uno-a-uno. Un detectado no puede cerrar dos esperados.

Estados principales:

- `COINCIDE`: mismo tipo y serial normalizado; o, sin seriales en ambos lados, datos
  fuertes de modelo, descripcion o capacidad compatible.
- `REVISAR`: mismo tipo con datos parecidos, pero falta confirmar serial, modelo o
  capacidad.
- `FALTA`: estaba esperado y no aparece detectado.
- `SOBRA`: aparece detectado y no estaba esperado.

## Pruebas

Tests relacionados:

```text
src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/ComponenteControllerTests.java
src/test/java/ar/gov/justiciajujuy/sanpedro/inventario/web/EquipoPageControllerTests.java
```

Comando:

```powershell
.\mvnw.cmd "-Dtest=ComponenteControllerTests,EquipoPageControllerTests,EquipoControllerTests" test
```

## Pendiente

- Exportar diferencias del dashboard.
