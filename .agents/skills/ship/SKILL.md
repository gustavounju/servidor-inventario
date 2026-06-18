---
name: ship
description: Usar cuando el branch está listo para integrarse. Sincroniza con main, corre o bootstrapea tests, audita cobertura del cambio, y prepara el Merge Request en GitLab. Disparadores: "preparalo para subir", "/ship", "subamos esto".
---

# Ship — La máquina de lanzamiento, no de brainstorming

Para este punto ya se decidió qué construir, se revisó la arquitectura, se implementó, se
pasó por `/review` y por `/qa`. Acá no se vuelve a discutir el alcance. Se ejecuta el
trabajo de release con disciplina.

## El repo es GitLab, no GitHub

El remoto de este proyecto es GitLab (`gitlab.com/.../servidorinventario`). Usá
terminología y flujo de Merge Request (MR), no Pull Request. Si la CLI `glab` está
disponible, usala para crear el MR; si no, dejá las instrucciones exactas (URL de
comparación, título, descripción) para que la persona lo cree manualmente desde la web.

## Pasos

1. **Sincronizar**: traer los últimos cambios de `main` (o la rama base que corresponda)
   y resolver conflictos si los hay, sin pisar trabajo ajeno.
2. **Bootstrap de tests si no existen todavía**: hoy `requirements.txt` no tiene
   `pytest`. Si esta es la primera vez que `/ship` corre en el proyecto, proponé:
   - agregar `pytest` (y `pytest-flask` si aplica) a `requirements.txt`
   - crear una carpeta `tests/` con al menos 3-5 tests reales contra el código actual
     (no tests de relleno) — por ejemplo, que la app arranca, que un blueprint clave
     responde 200 en su ruta principal con sesión autenticada, y un test del contrato de
     `services/dashboard_contract.py` ya que existe `test_dashboard_contracts.py` como
     punto de partida
   - documentar cómo correrlos en un `TESTING.md` corto
   No hace falta llegar a cobertura total en un solo `/ship` — pero cada `/ship` debería
   dejar la suite un poco más grande que antes, nunca igual.
3. **Correr los tests** que existan y bloquear el ship si fallan.
4. **Auditoría de cobertura del diff**: para los archivos tocados en este cambio
   puntual, ¿hay al menos un test que los ejercite? Si no, generalo ahora en vez de
   posponerlo.
5. **Chequeo de seguridad rápido antes de subir**: si el diff toca `bp_vault.py`,
   `utils/auth.py`, `database/db_core.py`, o cualquier archivo de `deployment/` —
   confirmá que ya pasó por `/cso`. Si no pasó, decilo y ofrecé correrlo antes de
   continuar.
6. **Push y MR**: subí la rama, abrí (o actualizá) el Merge Request con una descripción
   que incluya: qué cambia, por qué, cómo se probó (referenciá el reporte de `/qa` si
   existe), y el estado de tests (cuántos había antes, cuántos hay ahora).
7. **Actualizar `CONTEXT.md`** si el cambio afecta la estructura del proyecto, las
   variables de entorno, o los módulos disponibles — o delegá esto explícitamente a
   `/document-release` si el cambio es grande.

## Qué no hacer

No reabras la discusión de alcance acá (eso ya pasó en `/plan-ceo-review`). No saltees
el bootstrap de tests "para ir más rápido" — es exactamente el tipo de atajo que hace que
este proyecto siga sin red de seguridad.
