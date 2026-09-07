# Modulo Patrimonio

## Alcance

El modulo `PATRIMONIO` registra bienes institucionales con numero patrimonial y custodio.
Puede vincular un bien a un equipo de `EQUIPOS`, pero la relacion es opcional para cubrir
bienes no informaticos o bienes pendientes de asociacion.

Primera version implementada:

- Tabla `bienes_patrimoniales` mediante Flyway `V9__muebles_patrimonio_reportes.sql`.
- API `GET /api/v1/patrimonio/bienes` con filtros por texto y estado.
- API `POST /api/v1/patrimonio/bienes`.
- API `PUT /api/v1/patrimonio/bienes/{id}`.
- Pantalla `/admin/patrimonio`.
- Alta y edicion desde la pantalla.
- Vinculacion opcional con equipo.
- Auditoria al crear y actualizar.
- Permisos `PATRIMONIO:VER` y `PATRIMONIO:EDITAR`.

## Datos principales

- Numero patrimonial unico.
- Categoria.
- Descripcion.
- Ubicacion.
- Fuero.
- Custodio.
- Estado: `EN_USO`, `EN_DEPOSITO`, `EN_REPARACION`, `BAJA`.
- Equipo vinculado opcional.
- Observaciones.
- Activo/inactivo.

## Verificacion local

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
.\mvnw.cmd --batch-mode "-Dtest=PatrimonioControllerTests,PatrimonioPageControllerTests" test
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
```

Como `V9` crea tablas nuevas, hacer backup de MySQL antes del `git pull`/reinicio.
