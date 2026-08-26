# Handoff para Antigravity / Gemini - Inventario Next

## Resumen ejecutivo

Este repositorio contiene dos lineas de trabajo:

1. **ServidorInventario actual**: aplicacion Flask + MySQL + Jinja2 en produccion real.
2. **Inventario Next**: subproyecto nuevo en `inventario-next/`, creado para evolucionar
   el sistema en paralelo sin apagar ni romper Flask.

Inventario Next no reemplaza todavia al sistema actual. Es una aplicacion nueva dentro del
mismo repositorio para facilitar comparacion, versionado y convivencia. La regla inicial es
que Next debe comenzar en modo lectura sobre MySQL, sin escribir ni modificar datos de
produccion.

## Aclaracion importante: que comparte y que no comparte

### Comparte

- El mismo repositorio Git.
- La intencion de usar la misma base MySQL del sistema, cuando se configure `.env`.
- Los mismos requisitos operativos: Active Directory, certificados HTTPS, acceso movil de
  tecnicos, dashboard, visor, detalles de equipo, actas, resumenes PDF y efemerides.
- El contexto de negocio del Centro Judicial San Pedro.

### No comparte actualmente

- No importa codigo Python de Flask.
- No ejecuta blueprints Flask.
- No usa templates Jinja2.
- No consume datos reales si no se configura `.env`.
- No escribe en MySQL; por defecto `MYSQL_READ_ONLY=true`.
- No reemplaza rutas de produccion.

En otras palabras: esta dentro del mismo repo, pero es una aplicacion separada. La
convivencia es deliberada para poder comparar Next contra Flask antes de promover modulos.

## Rama y estado

Rama creada:

```sh
codex/inventario-next
```

Subproyecto creado:

```sh
inventario-next/
```

Documento de diseno inicial:

```sh
docs/designs/inventario-next.md
```

## Stack elegido

- SvelteKit 5 + TypeScript.
- Adapter Node para produccion detras de nginx/systemd.
- MySQL existente via `mysql2`.
- Drizzle ORM para queries tipadas.
- `ldapts` para Active Directory.
- Zod para validar configuracion/contratos.
- Vitest + Playwright + ESLint + Prettier desde el inicio.

Motivo: se eligio una opcion mas moderna y compacta que React/Django tradicional, pero sin
perder capacidad de correr en servidor propio del Poder Judicial.

## Comandos locales

Desde la raiz del repo:

```sh
cd inventario-next
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

URLs locales:

```text
http://127.0.0.1:5173/
http://127.0.0.1:5173/api/health
```

Verificaciones ya ejecutadas:

```sh
npm run format
npm run lint
npm run check
npm run build
```

Todas pasaron al momento del handoff.

## Configuracion

Existe:

```sh
inventario-next/.env.example
```

No commitear `.env` real. Las credenciales de MySQL, AD, TLS y certificados deben quedar
solo en `.env` local/servidor.

Default seguro:

```text
MYSQL_READ_ONLY=true
```

Si una tarea futura necesita escribir en MySQL, debe pasar por diseno tecnico y revision de
seguridad antes.

## Primer modulo recomendado

Construir primero:

```text
Detalle de equipo + previsualizacion de acta
```

Este modulo debe mostrar en una misma vista:

- datos crudos del script WMI;
- datos normalizados;
- componentes patrimoniales registrados;
- discrepancias;
- componentes finales que entran al acta;
- usuario/fuero;
- remitos y OC;
- salida PDF esperada.

La razon es que ahi se cruzan los problemas mas sensibles: monitores duplicados, monitores
pegados en una sola linea WMI, discos repetidos, discos pegados, seriales placeholder,
actas de entrega y resumenes PDF.

## Trabajo relacionado hecho antes del handoff

En Flask se corrigio:

- separacion de entradas WMI concatenadas por multiples `SN/SERIAL`;
- deduplicacion mas segura de discos/monitores;
- conservacion de equipos iguales cuando tienen seriales distintos;
- autocomplete de solicitantes con `Nombre (Fuero)`.

Tests focalizados que pasaron:

```sh
.\.venv\Scripts\python.exe -m pytest tests\test_pc_detail_components.py tests\test_ad_user_directory.py tests\test_asset_validation_lifecycle.py
```

Resultado: `30 passed`.

Suite Flask completa:

```sh
.\.venv\Scripts\python.exe -m pytest
```

Resultado observado antes del handoff: `147 passed`, `2 failed`.

Fallas no relacionadas con Inventario Next:

- `tests/test_build_orders_view_validation.py`: fake de test no contempla la consulta de
  usuarios AD.
- `tests/test_local_qr_endpoint.py`: `/qr-code` devuelve 500.

## Limpieza de codigo viejo

El modulo de mapa del Poder Judicial no debe migrarse a Inventario Next salvo que el usuario
lo pida explicitamente. No borrar todavia codigo Flask de produccion sin revisar uso real.

Estrategia:

1. Next nace sin mapas ni modulos no usados.
2. Flask conserva codigo viejo hasta confirmar que no se usa.
3. La limpieza del sistema actual debe ser tarea separada con review.

## Prompt para continuar en Antigravity / Gemini

Copiar y pegar este prompt en la otra IA:

```text
Estas trabajando en el repo G:\unju2025\google gravity\ServidorInventario.

Lee primero AGENTS.md y CONTEXT.md. Este sistema es produccion real del Departamento de
Informatica del Centro Judicial San Pedro, Jujuy. Usa Flask + MySQL en produccion, con
Active Directory, certificados HTTPS para acceso movil de tecnicos, generacion de actas,
PDFs, dashboard, visor, efemerides, stock, tareas y detalles de equipo.

Contexto reciente:
- Se creo la rama codex/inventario-next.
- Se creo un subproyecto nuevo en inventario-next/.
- Inventario Next es una aplicacion separada, no una extension directa de Flask.
- Esta en el mismo repo para versionado y convivencia, pero no importa codigo Python ni
  templates Jinja.
- Debe iniciar en modo lectura contra MySQL. No escribir en produccion.
- Por defecto MYSQL_READ_ONLY=true.
- No commitear .env, certificados privados, claves, tokens ni credenciales reales.

Stack actual de Inventario Next:
- SvelteKit 5 + TypeScript.
- Adapter Node para nginx/systemd.
- mysql2 + Drizzle ORM.
- ldapts para Active Directory.
- zod para validar config/contratos.
- Vitest, Playwright, ESLint y Prettier.

Documentos importantes:
- docs/designs/inventario-next.md
- docs/ANTIGRAVITY_HANDOFF_INVENTARIO_NEXT.md
- inventario-next/README.md

Objetivo propuesto:
Construir primero el modulo "Detalle de equipo + previsualizacion de acta" en Inventario
Next. Debe comparar:
1. datos crudos del script WMI;
2. datos normalizados;
3. componentes patrimoniales en MySQL;
4. discrepancias;
5. componentes finales que salen en acta/PDF.

Tener especial cuidado con:
- monitores que WMI trae pegados en una sola linea;
- discos que WMI trae pegados o repetidos;
- seriales placeholder como SerialNumber, N/A o Sin S/N;
- dos monitores/discos iguales pero con seriales distintos;
- usuario/fuero de Active Directory;
- certificados para web app movil;
- mantener Flask como produccion estable mientras Next se prueba aparte.

Comandos de Inventario Next:
cd inventario-next
npm install
npm run dev -- --host 127.0.0.1 --port 5173
npm run lint
npm run check
npm run build

Antes de tocar base remota, deploy, certificados o datos de produccion, pedir confirmacion
explicita. Si se sube a GitLab, tambien subir a GitHub segun AGENTS.md.

Primera tarea sugerida:
Crear en Inventario Next una ruta /equipos/[pcName] que lea datos de MySQL en modo lectura
y muestre una vista de detalle patrimonial reconciliado. Antes de escribir codigo, definir
tipos/contratos y tests para el parser/reconciliador.
```
