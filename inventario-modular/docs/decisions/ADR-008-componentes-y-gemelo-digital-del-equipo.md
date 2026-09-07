# ADR-008: Componentes Y Gemelo Digital Del Equipo

## Estado

Aceptado

## Fecha

2026-08-31

## Contexto

La idea de "gemelo digital" en Inventario Modular no significa solo mostrar una ficha
bonita del equipo. La idea operativa viene del trabajo real con el inventario viejo:

```text
El script informa las caracteristicas de una PC
-> el sistema muestra ese estado en un dashboard o detalle
-> desde stock salen componentes para armar o mejorar un equipo
-> se arma una orden de armado
-> el sistema compara lo esperado contra lo que realmente llego o se detecto
```

El concepto era confuso porque mezcla varios mundos: inventario tecnico, stock,
componentes, armado de equipos, reportes automaticos y control posterior. Pero esa mezcla
representa una necesidad real: saber si el equipo fisico coincide con lo que se planifico,
se entrego y se instalo.

## Decision

Mantener el concepto de gemelo digital, pero implementarlo por etapas y con datos
estructurados.

Proceso confirmado:

```text
1. Completar COMPONENTES para que el script guarde piezas detectadas.
2. Agregar RELEVAMIENTO_INICIAL para maquinas viejas ya existentes.
3. Crear STOCK para cargar componentes sueltos nuevos.
4. Crear ORDENES_ARMADO para planificar maquinas nuevas o mejoras.
5. Crear pantalla de comparacion del gemelo digital.
```

Primera etapa:

- Crear el modulo `COMPONENTES`.
- Vincular componentes a un `EQUIPO`.
- Registrar tipo de componente: RAM, disco, motherboard, monitor, teclado, mouse,
  impresora, CPU, fuente, gabinete u otro.
- Registrar origen del dato:

```text
SCRIPT        -> componente detectado por inventario automatico.
RELEVAMIENTO_INICIAL -> componente detectado o cargado al empezar con una maquina vieja.
STOCK         -> componente que salio o saldra de stock.
ORDEN_ARMADO  -> componente esperado por una orden de armado.
MANUAL        -> componente cargado o corregido por un administrador/tecnico.
```

- Registrar estado de comparacion:

```text
DETECTADO -> aparecio en el reporte.
ESPERADO  -> deberia estar segun stock/orden.
COINCIDE  -> lo esperado coincide con lo detectado o cargado.
FALTA     -> estaba esperado pero no aparece.
SOBRA     -> aparece pero no estaba planificado.
REVISAR   -> necesita revision manual.
```

## Flujo objetivo

Camino 1, PC vieja que ya existe:

```text
Tecnico ejecuta script en la PC
-> Inventario Modular actualiza EQUIPO
-> Inventario Modular guarda componentes con origen SCRIPT
-> Tecnico revisa el detalle del equipo
-> Si corresponde, convierte o carga esos datos como RELEVAMIENTO_INICIAL
-> Ese relevamiento queda como base del gemelo digital de esa PC
```

Camino 2, PC nueva armada desde cero:

```text
Stock recibe componentes
-> Tecnico crea orden de armado para un equipo
-> Se asignan componentes esperados al equipo
-> El script reporta componentes detectados
-> Inventario Modular compara esperado vs detectado
-> El detalle del equipo muestra el gemelo digital
-> Auditoria registra cambios, diferencias y correcciones
```

## Consecuencias

- `EQUIPOS` deja de ser una fila plana y empieza a representar el estado tecnico del
  equipo real.
- `COMPONENTES` queda como puente natural hacia `STOCK`, `TAREAS`, `ACTAS` y `AUDITORIA`.
- No hace falta implementar todo stock para empezar a comparar componentes.
- El script puede seguir evolucionando para alimentar componentes automaticamente.
- La edicion manual sigue siendo necesaria para corregir datos reales que el script no
  pueda detectar.

## Alcance inicial

Implementado en esta etapa:

- Tabla `componentes`.
- Entidad, repositorio y servicio de componentes.
- API para listar componentes por equipo.
- API para crear componentes asociados a un equipo.
- API para actualizar componentes.
- Ingesta automatica de componentes detectados desde `POST /api/v1/equipos/inventario`.
- Ingesta automatica de componentes detectados desde el endpoint heredado
  `POST /submit_inventory`.
- Seccion visual de gemelo digital en `/admin/equipos/{id}`.
- Formulario para cargar componentes desde el detalle del equipo.

Pendiente:

- Pantalla para consolidar detectados de una maquina vieja como `RELEVAMIENTO_INICIAL`.
- Modulo `STOCK`.
- Ordenes de armado como entidad propia.
- Salida real de stock.
- Comparacion automatica entre orden, stock y reporte del script.
- Auditoria transversal de cambios.
- Dashboard visual de diferencias.
