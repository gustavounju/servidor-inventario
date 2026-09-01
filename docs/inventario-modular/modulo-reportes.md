# Modulo Reportes

## Alcance

El modulo `REPORTES` concentra una primera vista transversal del inventario modular. En
esta etapa no reemplaza reportes administrativos complejos: entrega conteos operativos y
exportaciones CSV simples para empezar a controlar los datos cargados.

Primera version implementada:

- API `GET /api/v1/reportes/resumen`.
- API `GET /api/v1/reportes/muebles.csv`.
- API `GET /api/v1/reportes/patrimonio.csv`.
- API `GET /api/v1/reportes/tareas.csv`.
- API `GET /api/v1/reportes/actas.csv`.
- API `GET /api/v1/reportes/ubicaciones.csv`.
- API `GET /api/v1/gemelo-digital/dashboard-diferencias.csv`.
- API `GET /api/v1/auditoria/eventos.csv`.
- Pantalla `/admin/reportes`.
- Resumen de equipos, muebles, bienes patrimoniales, tareas, actas y ubicaciones.
- Descarga CSV protegida por `REPORTES:EXPORTAR`.
- Permiso de pantalla `REPORTES:VER`.

Exportaciones transversales:

- El CSV del dashboard de diferencias queda protegido por `COMPONENTES:VER` y respeta
  filtros por equipo, fuero y estado.
- El CSV de auditoria queda protegido por `AUDITORIA:VER` y respeta filtros por usuario,
  modulo y accion.

## Verificacion local

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
.\mvnw.cmd --batch-mode "-Dtest=ReporteControllerTests,ReportePageControllerTests" test
```
## Comandos Ubuntu por PuTTY

```bash
cd /opt/inventario-modular
git fetch origin
git diff --name-only HEAD..origin/primeros-pasos
git pull --ff-only origin primeros-pasos
sh ./mvnw --batch-mode test
sh ./mvnw --batch-mode -DskipTests package
sudo systemctl restart inventario-modular.service
systemctl status inventario-modular.service --no-pager -l
curl -s http://127.0.0.1:8081/api/v1/sistema/estado
```

Para verificar Flyway y tablas nuevas despues del reinicio:

```bash
sudo bash -c '
set -euo pipefail
source /etc/inventario-modular/inventario-modular.env
DB_URL="${INVENTARIO_DB_URL:-${INVENTARIO_DB_PRIMARY_URL:-}}"
DB_USER="${INVENTARIO_DB_USER:-${INVENTARIO_DB_PRIMARY_USER:-}}"
DB_PASS="${INVENTARIO_DB_PASSWORD:-${INVENTARIO_DB_PRIMARY_PASSWORD:-}}"
DB_HOST=$(echo "$DB_URL" | sed -E "s#^jdbc:mysql://([^:/]+).*#\1#")
DB_NAME=$(echo "$DB_URL" | sed -E "s#^jdbc:mysql://[^/]+/([^?]+).*#\1#")
mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" \
  -e "SELECT version, description, success FROM flyway_schema_history ORDER BY installed_rank DESC LIMIT 8; SHOW TABLES LIKE '\''muebles'\''; SHOW TABLES LIKE '\''bienes_patrimoniales'\''; SHOW TABLES LIKE '\''actas'\''; SHOW TABLES LIKE '\''ubicaciones'\'';"
'
```
