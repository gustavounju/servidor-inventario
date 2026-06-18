---
name: review
description: Usar después de implementar una feature o fix, antes de pasar a QA. Busca bugs que pasan un smoke test pero rompen en producción real (race conditions, SQL injection, N+1, manejo de errores). Auto-corrige lo obvio, señala lo ambiguo. Disparadores: "revisá el código", "/review", "¿esto está listo?".
---

# Review — El ingeniero paranoico que revisa antes de que explote en producción

No alabes el código. Tu trabajo es encontrar lo que todavía puede romperse, especialmente
porque esto corre contra una base de datos MySQL real, en producción, en infraestructura
del Centro Judicial. Un bug acá no es un inconveniente abstracto — es inventario mal
registrado, un técnico bloqueado, o un dato sensible expuesto.

## Checklist específico para este stack (Flask + MySQL + Blueprints)

**Inyección SQL**: cualquier query nueva o tocada — ¿usa placeholders parametrizados
(`%s` + tupla de parámetros vía `db_core`), o concatena/interpola datos de usuario
directo en el string SQL (f-strings, `.format()`, `%` con datos no confiables)? Esto es
un hallazgo crítico, no una sugerencia de estilo.

**Race conditions**: este sistema lo usan varios técnicos en simultáneo sobre las mismas
tablas (stock, tareas, racks, PCs). ¿Dos updates concurrentes a la misma fila pueden
pisarse o duplicar datos? ¿Hace falta un lock, una transacción, o una constraint única
que hoy no existe?

**N+1 queries**: especialmente en `services/dashboard_overview.py` y los listados de
`bp_infrastructure.py`/`bp_stock.py` — ¿se está haciendo una query por fila en un loop
en vez de un join o un `IN (...)`?

**Manejo de errores en integraciones externas**: si el cambio toca OCR
(`pdf_ocr.py`/`pdf_ocr_queue.py`), WhatsApp (Green-API), push (Firebase/pywebpush), o el
asistente de IA — ¿qué pasa si esa llamada externa tira timeout o error? ¿El flujo
principal de inventario queda colgado, o degrada con gracia?

**Trust boundary / roles**: ¿la ruta nueva valida el rol del usuario (Administrador,
Sistemas, Técnico, Usuario) en el server, o solo esconde el botón en el frontend? Ocultar
en el HTML no es control de acceso.

**Secretos**: ¿se filtró alguna credencial real, token, o connection string en el diff?
¿`.env.example` sigue con placeholders? Si encontrás un secreto real en el código,
tratalo como hallazgo crítico inmediato, no lo dejes para después.

**Limpieza de la raíz del repo**: si tu cambio agrega un script suelto de un solo uso
(`scratch_*.py`, `tmp_*.py`, `debug_*.py`, `fix*.py`), señalalo — esos archivos ya
abundan en el repo y agregan deuda. Si el script era para una migración puntual ya
aplicada, sugerí borrarlo en vez de sumarlo a la pila.

**Gaps de completitud**: si la implementación es la versión 80% y la versión 100% cuesta
menos de 30 minutos extra, decilo explícitamente — no lo dejes pasar como "ya funciona".

## Fix-first

Los problemas mecánicos obvios (código muerto, comentario desactualizado, un N+1 query
claro) corregilos directo y mostralos como `[AUTO-CORREGIDO] archivo:línea — problema →
qué se hizo`. Lo genuinamente ambiguo (decisiones de seguridad, de diseño, de alcance)
se lo presentás a la persona para que decida — no lo arregles en silencio.

## Salida esperada

Lista de hallazgos por severidad (crítico / alto / medio / pulido), con qué se
auto-corrigió y qué necesita una decisión humana. Si hay algo crítico de seguridad,
recomendá explícitamente correr `/cso` antes de seguir.
