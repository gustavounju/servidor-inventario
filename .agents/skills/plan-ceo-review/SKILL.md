---
name: plan-ceo-review
description: Usar después de office-hours, antes de implementar, para encontrar la versión más valiosa de una feature en lugar de la más literal. Cuatro modos: Expansión, Expansión Selectiva, Mantener Alcance, Reducción. Disparadores: "revisá el alcance de esto", "/plan-ceo-review", "¿hay una versión mejor de esto?".
---

# Plan CEO Review — Encontrar el producto de 10 puntos escondido en el pedido

Adaptación del "modo founder" de gstack para una herramienta interna, no para un startup.
Acá el "cliente" es el equipo de Informática del Centro Judicial: sistemas, técnicos,
operadores. El objetivo es el mismo: no implementar el ticket literal, sino preguntarse
"¿para qué es esto realmente, y cuál es la versión que de verdad mueve la aguja para
quien lo va a usar todos los días?"

## Ejemplo de cómo pensar esto en este proyecto

Pedido literal: "Que se pueda exportar el inventario a Excel."

Una respuesta floja agrega un botón y un `openpyxl.Workbook()`. Eso no es necesariamente
el producto real. Preguntas que vale la pena hacerse:

- ¿Para qué se exporta? ¿Para mandarlo a alguien fuera del sistema, para auditoría, para
  un informe periódico?
- Si es para un informe periódico, ¿no sería mejor que el sistema genere y mande ese
  informe solo (ya existe `services/reporting.py`, `bp_tasks.py`, e integración con
  WhatsApp vía Green-API — quizás la pieza que falta es automatizar el envío, no el
  export manual)?
- ¿El Excel manual es en realidad un parche porque el dashboard no muestra algo que
  debería mostrar de forma nativa?

El plan cambia completamente si la respuesta real es "automatizar un reporte recurrente"
en vez de "agregar un botón de exportar".

## Cuatro modos (preguntale a la persona cuál corresponde si no es obvio)

- **Expansión**: proponé la versión ambiciosa. Cada expansión se presenta como una
  decisión individual a aceptar o rechazar, con recomendación entusiasta de tu parte.
- **Expansión Selectiva**: el alcance actual queda como base, mostrás oportunidades
  adicionales una por una con recomendación neutral — la persona elige cuáles vale la
  pena.
- **Mantener Alcance**: máximo rigor sobre el plan ya definido, sin proponer expansiones.
  Usar cuando el tiempo es la limitación real (ej. hay que entregar antes de una fecha).
- **Reducción**: encontrar la versión mínima viable, cortando todo lo demás. Usar cuando
  el pedido ya es ambicioso y hay que aterrizarlo a algo entregable esta semana.

## Qué mirar específicamente en este proyecto

- ¿La feature pisa un módulo que ya existe y debería extenderse en vez de duplicarse?
  (revisar `blueprints/` antes de proponer un blueprint nuevo)
- ¿Hay una integración ya disponible que resuelve parte del problema sin código nuevo?
  (WhatsApp/Green-API, push notifications, el asistente de IA en
  `services/ai_assistant.py`, OCR de PDFs)
- ¿La feature afecta a los roles de usuario (Administrador, Sistemas, Técnico, Usuario)?
  Si sí, señalalo explícitamente — los cambios de permisos son decisiones de producto,
  no solo de código.

## Salida esperada

Una decisión de alcance clara (qué modo se usó y por qué), y la lista de "qué entra" vs
"qué queda explícitamente afuera por ahora". Esto alimenta directamente a
`/plan-eng-review`.
