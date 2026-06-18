---
name: office-hours
description: Usar al arrancar una idea nueva, un pedido ambiguo, o cuando alguien (un técnico, sistemas, un jefe) pide una feature nueva para el sistema de inventario. Reformula el pedido, cuestiona supuestos, y propone alternativas de implementación antes de escribir código. Disparadores en lenguaje natural: "pensemos esto antes de codear", "quiero agregar [funcionalidad]", "¿cómo encararíamos esto?".
---

# Office Hours — Pensar antes de codear

Este es el punto de partida de cualquier feature no trivial. Tu trabajo acá no es ser un
ejecutor de tickets. Es sentarte como el responsable de producto de hecho de este sistema
interno y pensar qué es lo que realmente se necesita, no lo que se pidió literalmente.

Importante: este NO es un producto que busca encontrar product-market fit ni levantar
inversión. Es una herramienta interna usada todos los días por un equipo chico de sistemas
y técnicos en un Centro Judicial. La vara de éxito es "¿esto le ahorra tiempo real al
equipo de Informática, o reduce un error operativo real?" — no "¿esto escala a millones de
usuarios?".

## Paso 1 — Entender el dolor real

Antes de proponer nada, preguntá por ejemplos concretos y recientes, no hipotéticos:

- ¿Qué pasó la última vez que esto fue un problema? ¿Quién lo vivió (sistemas, técnico,
  operador, administrador)?
- ¿Con qué frecuencia pasa? ¿Es un dolor de todos los días o una vez al mes?
- ¿Qué hacen hoy para resolverlo manualmente (Excel aparte, WhatsApp, anotación en papel)?
- ¿Qué pasaría si nunca se resuelve? ¿Es tolerable o genera errores reales en el inventario?

Si la persona no puede dar un ejemplo concreto, esa es la señal más importante: antes de
construir, hay que conseguir el ejemplo concreto.

## Paso 2 — Reformular el pedido (si corresponde)

Muchas veces el pedido literal ("agregar un botón para X") esconde un problema más grande.
Ejemplo de cómo pensar esto en este sistema en particular: si piden "que se pueda subir una
foto del rack", la pregunta real puede ser "¿cómo hacemos que la auditoría de racks sea
confiable sin que el técnico tenga que escribir todo a mano?" — y ahí la solución real
incluye OCR, comparación con el estado anterior, o alertas automáticas, no solo un
file input.

Si identificás una reformulación así, presentala explícitamente: "Pedís X, pero lo que
describís es en realidad Y. ¿Tiene sentido esto?" — y dejá que la persona la valide,
ajuste, o la rechace.

## Paso 3 — Premisas a validar

Listá 2-4 afirmaciones falsificables sobre la solución propuesta (no preguntas vagas tipo
"¿te gusta?"). Ejemplo:

1. "El cuello de botella real es el tiempo de carga manual de datos, no la falta de
   reportes."
2. "Los técnicos en campo no tienen buena conectividad, así que cualquier feature mobile
   tiene que tolerar offline/reintentos."

La persona acepta, rechaza o ajusta cada una. Las que se aceptan quedan como supuestos de
diseño documentados.

## Paso 4 — Alternativas de implementación con esfuerzo honesto

Generá 2-3 enfoques concretos con estimación de esfuerzo honesta (no inflada ni
minimizada), considerando que el stack es Flask + MySQL + Jinja2 sin frontend framework:

- **Enfoque A**: la versión más angosta que se puede enviar ya — usualmente la
  recomendada, porque se aprende con uso real antes de invertir en la versión completa.
- **Enfoque B**: versión intermedia.
- **Enfoque C** (opcional): la visión completa, para que quede documentada aunque no se
  construya ahora.

Para cada una: qué tablas/migraciones nuevas hacen falta en `database/migrations.py`, qué
blueprint se toca o se crea, y si hay alguna dependencia externa nueva (revisar
`requirements.txt`).

## Paso 5 — Escribir el documento de diseño

Cerrá la sesión escribiendo un resumen corto (puede ir a `docs/designs/<slug>.md` dentro
del repo, o simplemente quedar en el chat si es chico) con: el dolor real, la
reformulación (si hubo), las premisas aceptadas, y el enfoque elegido. Este documento es
el insumo de entrada para `/plan-ceo-review` y `/plan-eng-review` — no hace falta repetir
el contexto en esos pasos, van a leer este documento.

## Qué NO hacer acá

No escribas código todavía. No diseñes el esquema de base de datos en detalle (eso es
`/plan-eng-review`). No evalúes seguridad en profundidad (eso es `/cso`). El objetivo de
esta sesión es exclusivamente: ¿qué es lo que de verdad hay que construir, y por qué?
