---
name: guard
description: Activar al trabajar cerca de producción, del deploy, o de la base de datos remota del Centro Judicial. Pide confirmación explícita antes de ejecutar comandos destructivos o irreversibles, y puede restringir los cambios a una sola carpeta mientras se depura algo puntual. Disparadores: "tené cuidado", "/guard", "estamos en producción", "ojo con esto".
---

# Guard — Frenar antes de romper algo real

Antigravity no tiene (a la fecha de este documento) hooks nativos de pre-ejecución como
los de Claude Code, así que esta protección depende de que el propio agente se autoimponga
la pausa. Tratá esta lista como una regla de comportamiento obligatoria mientras este
skill está activo, no como una sugerencia.

## El acceso a producción es manual por PuTTY/SSH, no un pipeline automático

No hay CI/CD. El flujo real es: desarrollás en Windows con MySQL local
(`127.0.0.1` / `inventario_dev`), subís a GitLab, y en el trabajo entrás por PuTTY/SSH al
servidor Ubuntu (`/opt/inventario/`) para correr `git pull` y `bash deploy_ubuntu.sh` a
mano. Esto significa que cualquier comando "de producción" lo vas a estar tipeando vos
mismo en una sesión de terminal remota, en caliente, sin red de seguridad de un pipeline
que valide antes. Por eso este skill importa más en este proyecto que en uno con deploy
automatizado: la única protección real es la pausa antes de ejecutar.

## Comandos que SIEMPRE requieren confirmación explícita antes de ejecutarse

- Cualquier cosa que toque la base de datos de **producción** — host `10.15.3.20`,
  base `inventario_prod` (no `10.15.0.62`, que es el valor desactualizado que figura en
  `CONTEXT.md` — confirmar el host real contra `GUIA_UBUNTU_MANANA.md`/`.env` del
  servidor antes de asumir nada). No confundir con la de desarrollo
  (`127.0.0.1` / `inventario_dev`). Si no estás seguro contra qué host vas a correr
  algo, preguntá antes de ejecutar.
- Cualquier comando dentro de una sesión PuTTY/SSH activa contra el Ubuntu de
  producción — tratá toda esa sesión como zona de máximo cuidado, no solo los comandos
  obviamente destructivos. Antes de sugerir un comando para pegar en esa terminal,
  explicá qué hace y esperá confirmación.
- `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`, o cualquier `DELETE`/`UPDATE` sin `WHERE`
  (o con un `WHERE` que podría matchear más filas de las esperadas).
- Cualquier ejecución de `database/migrations.py` contra producción, o cualquier script
  de migración suelto (`tmp_migrate_racks.py`, `migrate_ups.py`, `run_migrations.py`)
  si el target no es explícitamente el entorno de desarrollo.
- Borrar o sobrescribir backups: `backup.sh`, `backup_mysql.sh`,
  `inventario_snapshot.backup`, `snapshot.backup`, `inventario.db.bak`.
- Tocar archivos de deploy/infraestructura: `deployment/nginx_inventario.conf`,
  `deployment/inventario.service` (o el `inventario.service` de la raíz),
  `deploy_ubuntu.sh`, `update_server.sh`, `update_server.bat`,
  `deployment/inventario_gpo.ps1`.
- `git push --force`, `git reset --hard`, o reescribir historia en una rama que no es
  exclusivamente tuya.
- Reiniciar o detener el servicio en producción (cualquier comando tipo
  `systemctl restart/stop inventario`, o equivalente).
- Cualquier comando que borre recursivamente una carpeta (`rm -rf`, o el equivalente en
  PowerShell) fuera de carpetas de build conocidas (`__pycache__`, `node_modules` si
  llegara a existir, carpetas de caché).
- Validate all tool parameters against an allowlist before execution. Reject dangerous parameter values (e.g. shell=True, --force, -rf /) and use safe defaults.

## Cómo pedir confirmación

Antes de ejecutar algo de la lista anterior, explicá en una línea qué va a hacer el
comando, contra qué entorno corre, y qué pasa si sale mal (¿es reversible? ¿hay backup
reciente?). Esperá una confirmación explícita ("sí", "dale", "confirmado") antes de
seguir — no asumas que "puede que esté bien" es luz verde.

## Restricción de carpeta (modo freeze)

Si estás debuggeando algo puntual y la persona pide explícitamente acotar el alcance
("solo tocá `blueprints/bp_stock.py`", "no toques nada fuera de `services/`"), respetá
ese límite estrictamente durante el resto de la sesión: no edites archivos fuera de esa
carpeta aunque encuentres algo que "de paso" convendría arreglar ahí. Señalalo para una
sesión aparte en cambio.

## Esto es prevención de accidentes, no control de acceso

Este skill no sustituye permisos reales a nivel de sistema operativo o base de datos. Es
una capa de criterio para que el agente (y la persona) no ejecuten algo irreversible por
apuro. La persona siempre puede confirmar y avanzar — la idea es que lo haga
conscientemente, no por default.
