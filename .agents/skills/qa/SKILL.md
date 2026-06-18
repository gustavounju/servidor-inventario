---
name: qa
description: Usar después de review, antes de ship. Levanta la app Flask localmente (o apunta a staging), navega las páginas afectadas usando el navegador/preview de Antigravity, y reporta bugs reales con evidencia. Disparadores: "probá la app", "/qa", "fijate si esto funciona de verdad".
---

# QA — Probar la app de verdad, no asumir que funciona

No te quedes en "el código compila" o "no tiró excepción en el log". Esto es una app web
con UI real (Jinja2 + JS vanilla) — la única forma de saber si funciona es navegarla.

## Antes de arrancar

1. Confirmá que el servidor de desarrollo está corriendo. Si no, levantalo:
   `python servidor.py` (necesita `.env` con `FLASK_SECRET_KEY` y credenciales de MySQL
   dev configuradas — sin esto el servidor no arranca, es una validación intencional del
   propio `servidor.py`).
2. Si hay un diff de git disponible, identificá qué rutas/templates tocó el cambio
   (ej. un cambio en `bp_stock.py` + `templates/stock.html` → probar `/stock/`). Si no
   hay diff claro, pedile a la persona la URL o la página a probar.
3. Si la página requiere login, usá el usuario de prueba/dev (nunca credenciales de
   producción real) y verificá con qué rol corresponde probar (Administrador, Sistemas,
   Técnico, Usuario) según qué controla el cambio.

## Qué probar en cada pasada

- **Camino feliz**: la acción principal de la página funciona de punta a punta (crear,
  editar, listar, exportar, lo que corresponda).
- **Formularios**: enviar con campos vacíos, con datos duplicados, con texto donde se
  espera número — ¿el error se muestra de forma clara o la página rompe?
- **Roles**: si el cambio afecta permisos, probá con al menos dos roles distintos para
  confirmar que el control de acceso es real y no solo visual.
- **Estados vacíos y de carga**: si la sección puede no tener datos todavía (inventario
  recién creado, sin tareas asignadas), ¿se ve un estado vacío razonable o se rompe?
- **Mobile**: si el cambio toca `bp_mobile.py` o `templates/mobile*.html`, probalo
  también en el viewport mobile — este sistema lo usan técnicos desde el celular en
  campo, con conectividad mala. Verificá qué pasa si una request tarda o falla.
- **Consola del navegador**: revisá errores de JS en consola, no solo el resultado
  visual.

## Reporte

Para cada hallazgo: severidad, página/ruta, qué se esperaba vs qué pasó, y screenshot si
es posible. No reportes "funciona" sin haber probado al menos el camino feliz y un caso
de error real.

## Si encontrás un bug y lo arreglás

Hacé el fix con un commit chico y enfocado, volvé a probar la misma página para
confirmar, y si tiene sentido agregá un test de regresión (aunque sea simple) en vez de
dejar la corrección sin cobertura — recordá que el proyecto hoy no tiene suite de tests,
así que cada fix verificado es una oportunidad de empezar a construirla.
