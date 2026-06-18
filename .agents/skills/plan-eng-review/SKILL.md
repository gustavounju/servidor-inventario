---
name: plan-eng-review
description: Usar antes de implementar cualquier cosa no trivial, después de plan-ceo-review. Define arquitectura, flujo de datos, casos borde y plan de tests para Flask/MySQL. Fuerza diagramas para sacar a la luz supuestos ocultos. Disparadores: "armemos la arquitectura", "/plan-eng-review", "pensemos el diseño técnico".
---

# Plan Eng Review — De la idea aprobada al plan que se puede construir

Tu trabajo acá es ser el líder técnico de este proyecto Flask + MySQL + Blueprints. No es
momento de ideación de producto (eso ya pasó). Es momento de hacer las preguntas que, si
no se responden ahora, van a explotar en producción contra la base de datos remota del
Centro Judicial.

## Preguntas que SIEMPRE hay que responder en este stack

- **Blueprint**: ¿esto va en un blueprint existente (`bp_dashboard`, `bp_infrastructure`,
  `bp_stock`, `bp_tasks`, `bp_mobile`, `bp_vault`, `bp_users`, `bp_operadores`,
  `bp_tecnicos`, `bp_setup`, `bp_api`) o necesita uno nuevo? Si es nuevo, ¿se registra en
  `servidor.py` y respeta el sistema de roles de `utils/auth.py`?
- **Esquema**: ¿qué tablas o columnas nuevas hacen falta? ¿La migración va en
  `database/migrations.py` siguiendo el patrón existente, es reversible, y qué pasa con
  los datos ya existentes en producción al aplicarla?
- **Conexión a datos**: ¿las queries nuevas pasan por `database/db_core.py` con
  parámetros (placeholders `%s`), nunca con f-strings o `.format()` insertando datos de
  usuario directo en el SQL?
- **Síncrono vs background**: si la feature toca OCR (`services/pdf_ocr.py`,
  `pdf_ocr_queue.py`), notificaciones push, WhatsApp, o el asistente de IA, ¿qué corre
  síncrono en el request y qué debería ir a una cola/background? Estas integraciones
  externas pueden tardar o fallar — el request del usuario no debería quedar colgado
  esperándolas.
- **Modo de fallo**: si la base de datos remota (`10.15.0.62`) está lenta o caída, ¿la
  página rompe con un 500 feo o degrada con gracia? Si una integración externa
  (Green-API, Firebase, Gemini) falla, ¿el flujo principal del inventario sigue
  funcionando?
- **Trust boundary**: si la feature toca Vault o Auth, marcala explícitamente para pasar
  por `/cso` antes de mergear — no la apruebes acá sin esa pasada adicional.
- **Frontend**: como no hay framework JS, ¿el cambio en el template Jinja2 necesita JS
  vainilla nuevo en `static/js/`? ¿Reutiliza componentes ya existentes en
  `_shared_modals.html` o `_module_switcher.html`?

## Diagramas (no te los saltees)

Pedí o generá al menos uno de estos, según lo que aplique — esto fuerza a que los
supuestos ocultos salgan a la luz antes de escribir código:

- Diagrama de flujo de datos: request → blueprint → service → `db_core` → MySQL →
  template renderizado.
- Diagrama de secuencia si hay una integración externa en el medio (ej. subida de PDF →
  cola de OCR → resultado guardado → notificación push).
- Matriz de casos borde: por cada input nuevo, qué pasa si viene vacío, duplicado, con
  formato inválido, o si dos usuarios lo modifican a la vez (race condition en updates
  concurrentes a una misma fila — pasa seguido en sistemas de inventario con varios
  técnicos usando la app en simultáneo).

## Plan de tests

Como hoy el proyecto no tiene `pytest`, este es el momento de listar explícitamente qué
tests harían falta para esta feature en particular (no toda la suite, solo lo nuevo):
casos felices, casos de error esperado, y al menos un caso de concurrencia si la feature
toca una tabla compartida (stock, tareas, racks). Esta lista la recoge `/qa` y `/ship`
más adelante — no hace falta volver a escribirla.

## Salida esperada

Un plan técnico concreto: blueprint/archivo afectado, cambios de esquema, manejo de
fallos, y la lista de tests pendientes. Si encontraste algo que toca Vault/Auth,
decilo explícitamente como "requiere /cso antes de mergear".
