# Seguridad LAN, Stock y Discrepancias - 2026-09-08

Este documento registra la entrega de endurecimiento y ajustes operativos realizados sobre
Inventario Modular para uso en red institucional.

## Seguridad de red y credenciales

- El sistema queda preparado para operar en modo LAN-only mediante
  `inventario.security.network.lan-only`.
- Los accesos HTTP entrantes se filtran para aceptar solo loopback y rangos privados de
  red local cuando el modo LAN-only esta activo.
- Los tokens de reporte y claves locales ya no tienen valores por defecto seguros de
  copiar: deben configurarse con variables de entorno en el servidor.
- La autenticacion local solo se habilita si existe usuario y password explicitos.
- La comparacion del bearer token de reporte se realiza en tiempo constante para reducir
  filtraciones por timing.

## Discrepancias de gemelo digital

En la ficha del equipo, la tabla superior de discrepancias muestra los casos `FALTA`,
`SOBRA` o `REVISAR`. Para resolver rapidamente los faltantes:

- Las filas `FALTA` de la tabla de discrepancias quedan resaltadas.
- Las tablas inferiores de componentes resaltan solo los componentes concretos que
  originan una discrepancia `FALTA`.
- La senal visual inferior agrega un punto pulsante y el texto `Resolver` al lado de las
  acciones de taller.

La regla importante es que no se marca todo componente `ESPERADO`; solo se marca el
componente que coincide con una discrepancia `FALTA` real de la comparacion viva.

## Stock y vinculacion

La pantalla `/admin/stock` ahora muestra la columna `Vinculado a`:

- Si el stock esta `ASIGNADO` y existe un componente activo con el mismo tipo y serial, se
  muestra el equipo y el ultimo usuario registrado en esa PC.
- Si el usuario tiene permiso para ver equipos, el nombre del equipo enlaza a su ficha.
- Si un stock `ASIGNADO` con serial ya no tiene componente activo asociado, se libera
  automaticamente a `DISPONIBLE` al listar stock y se registra auditoria
  `LIBERAR_HUERFANO`.

Al desvincular un componente desde la ficha del equipo, el sistema tambien busca un item de
stock activo con el mismo serial y estado `ASIGNADO`; si lo encuentra, lo devuelve a
`DISPONIBLE`.

## Verificaciones realizadas

Pruebas focales ejecutadas:

```powershell
.\mvnw "-Dtest=LanOnlyAccessFilterTests,SystemStatusControllerTests,EquipoControllerTests,LocalAuthenticationConfigTests" test
.\mvnw "-Dtest=EquipoPageControllerTests#muestraDetalleDeHardwareExtendido" test
.\mvnw "-Dtest=EquipoPageControllerTests#retiraComponenteHaciaStockYRegeneraItemEnStock" test
```

Validaciones manuales en MySQL local:

- `/admin/equipos` respondio correctamente.
- `/admin/stock` respondio correctamente.
- `/admin/equipos/15` mostro dos componentes inferiores a resolver para dos
  discrepancias faltantes reales.
- En stock, una pieza asignada mostro equipo y usuario asociado.

Suite completa:

- `.\mvnw test` compilo y ejecuto 140 pruebas.
- Resultado actual: 14 fallas por tests heredados que esperan rutas ya removidas o
  renombradas, principalmente `ordenes-armado`, patrimonio y reportes antiguos.
- Las pruebas focales de seguridad, detalle de equipo y retiro a stock quedaron en verde.

## Nota operativa

Si una pieza figura `ASIGNADO` pero no muestra equipo ni usuario, revisar que tenga numero
de serie y que exista un componente activo en una ficha de equipo con el mismo serial y
tipo. Si tiene serial y no existe vinculo activo, el listado de stock la libera
automaticamente.
