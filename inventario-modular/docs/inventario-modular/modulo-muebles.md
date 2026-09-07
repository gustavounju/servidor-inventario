# Modulo Muebles

## Alcance

El modulo `MUEBLES` registra mobiliario fisico del Centro Judicial: escritorios, sillas,
mesas, racks u otros bienes de oficina que conviene ubicar y reasignar sin mezclar con
componentes tecnicos.

Primera version implementada:

- Tabla `muebles` mediante Flyway `V9__muebles_patrimonio_reportes.sql`.
- API `GET /api/v1/muebles` con filtros por texto y estado.
- API `POST /api/v1/muebles`.
- API `PUT /api/v1/muebles/{id}`.
- Pantalla `/admin/muebles`.
- Alta y edicion desde la pantalla.
- Auditoria al crear y actualizar.
- Permisos `MUEBLES:VER` y `MUEBLES:EDITAR`.

## Datos principales

- Codigo unico.
- Tipo.
- Descripcion.
- Ubicacion.
- Fuero.
- Responsable.
- Estado: `ACTIVO`, `EN_REPARACION`, `BAJA`.
- Observaciones.
- Activo/inactivo.

## Verificacion local

```powershell
cd "C:\Users\gmurad\Documents\ChatGPT\inventario-modular"
.\mvnw.cmd --batch-mode "-Dtest=MuebleControllerTests,MueblePageControllerTests" test
```

## Comandos Ubuntu por PuTTY

Luego de mergear el cambio a `primeros-pasos`, actualizar el servidor modular desde
`/opt/inventario-modular`, no desde `/opt/inventario`.

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
