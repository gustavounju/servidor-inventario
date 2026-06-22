# AGENTS.md — ServidorInventario (Centro Judicial San Pedro, Jujuy)

Este archivo es la constitución del proyecto para cualquier agente (Antigravity, Gemini CLI, etc.)
que trabaje en este repo. Léelo antes de tocar código. Es la adaptación de la metodología
**gstack** (originalmente para Claude Code) al ecosistema Antigravity/Gemini.

## Qué es este proyecto

Sistema de inventario interno para el Departamento de Informática del Centro Judicial
(San Pedro, Jujuy). No es un SaaS ni un producto con usuarios externos: lo usa un equipo
chico de sistemas/técnicos para llevar el inventario de PCs, racks, switches, impresoras,
stock y tareas. Corre en producción real, en infraestructura del Poder Judicial.

- **Backend**: Python 3.13, Flask (arquitectura por Blueprints en `blueprints/`)
- **Base de datos**: MySQL (local en dev, remoto en prod — `10.15.0.62`)
- **Frontend**: Jinja2 + HTML/CSS/JS vanilla (sin framework, sin bundler)
- **Servicios**: OCR de PDFs (pytesseract/pdf2image), asistente IA (google-genai / Gemini,
  ya integrado en `services/ai_assistant.py`), notificaciones push (firebase-admin,
  pywebpush), WhatsApp vía Green-API, futura integración con Active Directory (ldap3)
- **Deploy**: Windows en desarrollo, Ubuntu + systemd + nginx + gunicorn en producción
- **Contexto vivo del proyecto**: `CONTEXT.md` es la fuente de verdad real, no el `README.md`
  (que todavía tiene el boilerplate default de GitLab). Cualquier skill que actualice
  documentación debe mantener `CONTEXT.md` al día, no solo el README.

## Reglas que SIEMPRE aplican (no negociables)

1. **Nunca generes ni commitees secretos reales.** `.env.example` debe quedar siempre con
   placeholders. Si encontrás una credencial real (API key, password, token) en cualquier
   archivo que no sea `.env` o `.gitignore`'d, tratalo como un hallazgo crítico de seguridad,
   no como un detalle de estilo.
2. **Esto es producción judicial real, no un proyecto de juguete.** Cualquier comando que
   pueda afectar la base de datos remota (host real confirmado: `10.15.3.20`, base
   `inventario_prod` — el valor `10.15.0.62` que figura en `CONTEXT.md` está
   desactualizado, corregirlo cuando se edite ese archivo), borrar backups, tocar
   `deployment/`, `nginx_inventario.conf`, `inventario.service`, o los scripts de deploy
   (`deploy_ubuntu.sh`, `update_server.sh/.bat`) requiere confirmación explícita antes de
   ejecutarse. Ver los skills `/guard` y `/deploy`.
3. **Toda query SQL nueva debe ser parametrizada.** Nunca interpolar datos de usuario
   directamente en un string SQL (ni con f-strings, ni con `.format()`, ni con `%`).
4. **El directorio raíz tiene mucha deuda técnica heredada** (`scratch_*.py`, `fix*.py`,
   `tmp_*.py`, `debug_*.py`, archivos `.bak`, `snapshot.backup`, logs sueltos). No asumas
   que un archivo en la raíz es parte del flujo principal de la app — el flujo principal
   entra por `servidor.py` y los `blueprints/`. Si vas a limpiar esto, hacelo en un paso
   explícito y revisado (`/review` o `/ship` lo señalan), nunca de forma incidental dentro
   de otra tarea.
5. **No hay suite de tests todavía** (no hay `pytest` en `requirements.txt`, solo
   `test_dashboard_contracts.py` suelto). Cualquier skill que toque release o calidad debe
   tratar esto como gap conocido, no como sorpresa, y ofrecer bootstrapear tests reales
   en lugar de saltarse el paso.
6. **Datos sensibles**: el módulo Vault (`blueprints/bp_vault.py`, `templates/vault.html`)
   y la autenticación (`utils/auth.py`, roles, futura AD) son las superficies de más alto
   riesgo del sistema. Cualquier cambio ahí pasa primero por `/cso` antes de mergear.
7. **El repo remoto es GitLab** (no GitHub) — los flujos de PR en los skills usan
   terminología de Merge Request (MR) y, si está disponible, la CLI `glab` en vez de `gh`.

## El flujo de sprint (orden recomendado)

```
office-hours → plan-ceo-review → plan-eng-review → (implementar) → review → qa → ship → deploy → document-release
```

No todas las tareas necesitan el flujo completo. Una corrección de un bug chico puede ir
directo a `/review` → `/qa` → `/ship`. Una feature nueva o un cambio de alcance grande
debería pasar por `/office-hours` primero.

## Skills disponibles

| Comando / disparador en lenguaje natural | Cuándo usarlo |
|---|---|
| "pensemos esto antes de codear", `/office-hours` | Al arrancar una idea nueva o un pedido ambiguo. Reformula el pedido, cuestiona supuestos, propone alternativas. |
| "revisá el alcance de esto", `/plan-ceo-review` | Después de office-hours. Busca la versión más valiosa de la feature para el equipo de sistemas/técnicos real. |
| "armemos la arquitectura", `/plan-eng-review` | Antes de implementar algo no trivial. Fuerza diagramas, casos borde, plan de test. |
| "revisá el código", `/review` | Después de implementar, antes de probar. Busca bugs que pasan smoke test pero rompen en producción. |
| "probá la app", `/qa` | Después de `/review`. Recorre la app real (local o staging) y reporta bugs. |
| "preparalo para subir", `/ship` | Cuando el branch está listo. Sincroniza, corre tests, abre el Merge Request. |
| "vamos a producción", `/deploy` | Después de mergear el MR. Lleva el cambio al Ubuntu de producción vía PuTTY/SSH, paso a paso, con confirmación en cada comando. |
| "auditoría de seguridad", `/cso` | Antes de tocar Vault, Auth, o antes de cualquier release grande. OWASP + revisión de secretos. |
| "tené cuidado", `/guard` | Al trabajar cerca de producción, deploy, o la base remota. Pide confirmación antes de comandos destructivos. |
| "actualizá la documentación", `/document-release` | Después de `/ship`. Mantiene `CONTEXT.md` y el README al día con lo que cambió. |
| "mejorá el diseño de esta pantalla", `frontend-design` | Al crear o rediseñar una pantalla/template. Skill original de Anthropic (sin adaptar), pensado para identidad visual distintiva — usar con criterio en un panel interno, no todo aplica igual que en un producto de marca. |

## Notas de portabilidad

Esta carpeta usa el formato de Skills de Antigravity (`SKILL.md` con frontmatter YAML +
instrucciones en Markdown), guardado en `.agents/skills/` a nivel de proyecto. Si en algún
momento se vuelve a usar Claude Code, esta misma carpeta de skills es compatible casi sin
cambios (es el mismo formato que usa gstack, del que está adaptada esta metodología).
