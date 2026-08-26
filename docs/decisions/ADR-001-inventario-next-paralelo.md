# ADR-001: Inventario Next como aplicacion paralela

## Estado

Aceptado

## Contexto

ServidorInventario es una aplicacion Flask en produccion real para el Departamento de
Informatica del Centro Judicial San Pedro. El sistema actual ya cubre stock, tareas,
dashboard, visor, efemerides, detalles de equipo, actas de entrega, resumenes PDF,
integracion con Active Directory, certificados HTTPS y uso movil por tecnicos.

El sistema crecio mucho y contiene codigo heredado o modulos que ya no se usan. Aun asi,
reemplazarlo de golpe seria riesgoso porque la operacion diaria depende de que los datos,
actas y PDFs sigan funcionando.

## Decision

Crear Inventario Next como una aplicacion nueva y paralela en `inventario-next/`, dentro del
mismo repositorio pero separada tecnicamente de Flask.

Inventario Next debe:

- correr en otro puerto/path;
- iniciar en modo lectura contra MySQL;
- respetar Active Directory, TLS/certificados y acceso movil;
- no importar codigo Python ni templates Jinja;
- no migrar modulos sin uso, como mapas, salvo decision explicita;
- construir primero detalle de equipo + previsualizacion de acta.

## Alternativas consideradas

### Reescritura completa inmediata

Ventaja: arquitectura limpia desde el inicio.

Desventaja: alto riesgo operativo, doble mantenimiento grande y posibilidad de romper
actas/PDFs/datos criticos.

Rechazada por riesgo.

### Modernizar Flask en el mismo codigo

Ventaja: menor cambio de infraestructura.

Desventaja: mantiene mezcla entre UI, SQL, normalizacion, actas y servicios heredados.

Rechazada como estrategia principal, aunque se seguiran haciendo fixes puntuales en Flask.

### Aplicacion paralela en el mismo repositorio

Ventaja: permite convivir, comparar salidas contra Flask y promover modulos de a poco.

Desventaja: requiere disciplina para no escribir en MySQL demasiado pronto.

Aceptada.

## Consecuencias

- El repo tendra dos aplicaciones durante una etapa de transicion.
- Flask sigue siendo produccion estable.
- Inventario Next puede innovar sin comprometer la operacion diaria.
- Las reglas de seguridad sobre secretos, DB remota, certificados y deploy siguen vigentes.
- La primera medida de seguridad tecnica es `MYSQL_READ_ONLY=true` por defecto.
