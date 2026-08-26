# Inventario Next - Diseño Inicial

## Dolor Real

El sistema actual ya cubre operaciones criticas: visor, dashboard, detalles de equipo,
actas de entrega, resumenes PDF, efemerides, tareas, stock, Active Directory, acceso movil
de tecnicos y certificados HTTPS. El problema no es solamente estetico ni de velocidad: el
riesgo principal es que distintas pantallas o documentos interpreten el inventario de forma
distinta.

Inventario Next debe nacer para reducir esa diferencia entre "lo que trajo el script",
"lo que esta registrado en patrimonio", "lo que ve el tecnico" y "lo que sale impreso en
el acta".

## Decision de Alcance

Modo: Expansion Selectiva.

Se conserva Flask como produccion estable y se construye Inventario Next en paralelo, oculto
o restringido a Sistemas. Al comienzo debe trabajar en modo lectura o con escritura muy
controlada, usando la misma base MySQL para no duplicar verdad operativa.

## Stack Propuesto

- Runtime: Bun para desarrollo local y tooling rapido.
- Aplicacion: SvelteKit, por ser mas compacto que React para UI interna y permitir server
  routes, SSR y service workers.
- Lenguaje: TypeScript estricto.
- Base de datos: MySQL existente.
- ORM/query layer: Drizzle ORM con mysql2, cuidando que al inicio no reemplace migraciones
  criticas del sistema actual.
- Autenticacion interna: integracion con Active Directory desde backend, respetando servidor,
  dominio, TLS y credenciales existentes.
- Certificados: TLS terminado por nginx en produccion; en local se documenta el uso de
  certificados de desarrollo para telefonos de tecnicos.
- PWA movil: service worker, manifest y cache controlado para acceso rapido desde celulares,
  sin asumir offline completo en la primera fase.
- PDFs/actas: HTML imprimible + generacion por navegador headless cuando convenga; el origen
  siempre debe ser un resumen patrimonial reconciliado.

## Que Entra

- Nueva carpeta o subproyecto `inventario-next/`.
- Lectura de MySQL existente sin tocar el esquema al principio.
- Vista nueva de detalle de equipo como primer modulo.
- Motor compartido de reconciliacion: script WMI normalizado, patrimonio registrado,
  discrepancias y componentes que entran al acta.
- Acta de entrega nueva basada en datos reconciliados.
- Dashboard nuevo solo cuando la fuente de datos ya este clara.
- Eliminacion conceptual de modulos que no se usan en Next, por ejemplo el mapa del Poder
  Judicial, sin borrar todavia codigo de produccion Flask.

## Que Queda Afuera Por Ahora

- Reescritura completa del sistema actual.
- Cambios destructivos en MySQL.
- Reemplazar login/autenticacion de produccion sin pruebas.
- Apagar Flask.
- Migrar todo el stock, tareas y reportes en el primer paso.

## Plan de Convivencia

1. Flask queda en produccion como sistema principal.
2. Inventario Next corre en otro puerto o path interno, por ejemplo `/next` o
   `inventario-next`.
3. Nginx puede publicar Next solo para IPs internas o usuarios administradores.
4. Next empieza leyendo las mismas tablas de MySQL.
5. Cada pantalla nueva se compara contra Flask antes de habilitarla al equipo.
6. Cuando una pantalla de Next supere a la actual en confiabilidad, se la promueve.

## Primer Modulo Recomendado

Detalle de equipo + previsualizacion de acta.

Motivo: es donde se juntan los problemas mas sensibles: monitores duplicados, discos
pegados, componentes oficiales, WMI, usuario, fuero, remitos, OC y salida PDF. Si esta
pantalla queda bien, el resto del sistema tiene una base mas confiable.

## Riesgos

- Compartir MySQL entre dos aplicaciones puede generar inconsistencias si Next empieza a
  escribir demasiado pronto.
- Active Directory y certificados deben probarse en red real del trabajo, no solo en local.
- Una tecnologia moderna no arregla por si sola datos mal normalizados.
- Los PDFs deben probarse visualmente, porque un test unitario no alcanza para actas.

## Referencias Tecnicas

- SvelteKit adapter-node: https://svelte.dev/docs/kit/adapter-node
- SvelteKit service workers: https://svelte.dev/docs/kit/service-workers
- Bun: https://bun.com/
- Drizzle MySQL: https://orm.drizzle.team/docs/mysql/get-started-mysql
- FastAPI detras de proxy, si se decide mantener un backend Python separado:
  https://fastapi.tiangolo.com/advanced/behind-a-proxy/
