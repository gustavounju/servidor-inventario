# ADR-003: Usar El Inventario Viejo Como Referencia Funcional

## Status

Aceptada

## Fecha

2026-08-28

## Contexto

El inventario viejo sigue siendo util para el trabajo diario. Tiene flujos importantes que
funcionan, como equipos, actas, OVMelos, patrimonio, stock y reportes. Tambien refleja
decisiones operativas reales del Centro Judicial San Pedro que no deben perderse durante
la migracion.

Al mismo tiempo, el sistema viejo no debe convertirse en la base tecnica del nuevo
Inventario Modular. El objetivo del nuevo proyecto es empezar limpio en Java, con
Spring Boot, arquitectura modular, Active Directory, permisos internos, API REST y una
base preparada para una futura app movil.

## Decision

Usar el inventario viejo como **referencia funcional**, no como base tecnica.

Esto significa:

- Se estudian sus pantallas, tablas, reportes y flujos reales.
- Se documentan las reglas de negocio que estan probadas por el uso diario.
- Se conserva la logica operativa que funciona.
- Se reimplementa cada modulo desde cero en Java.
- No se copian archivos, estructura interna ni codigo heredado al nuevo proyecto.

## Alternativas Consideradas

### Copiar el sistema viejo y traducirlo a Java

Ventaja: podria parecer mas rapido al inicio.

Desventaja: arrastraria deuda tecnica, decisiones viejas y acoplamientos que justamente
se quieren superar.

Resultado: descartado.

### Rehacer todo sin mirar el inventario viejo

Ventaja: maxima limpieza tecnica.

Desventaja: riesgo alto de perder reglas reales de trabajo, reportes necesarios y detalles
operativos que solo existen porque el sistema viejo se usa todos los dias.

Resultado: descartado.

### Migrar por modulos usando el viejo como guia

Ventaja: conserva conocimiento operativo y permite redisenar bien la arquitectura.

Desventaja: requiere estudiar cada modulo antes de implementarlo.

Resultado: aceptado.

## Consecuencias

- El sistema viejo debe seguir funcionando mientras el nuevo madura.
- Cada modulo nuevo debe empezar con relevamiento funcional.
- La documentacion debe explicar que regla del sistema viejo se conserva y como se
  implementa en Java.
- Las migraciones de datos se planificaran despues de entender el modulo, no antes.
- El nuevo Inventario Modular evita copiar deuda tecnica heredada.

## Regla Practica

```text
El inventario viejo responde que debe hacer el sistema.
Inventario Modular Java decide como implementarlo bien desde cero.
```
