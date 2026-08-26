# Inventario Next

Proyecto paralelo para evolucionar el sistema de inventario sin interrumpir Flask.

## Stack

- SvelteKit 5 + TypeScript
- Adapter Node para correr detras de nginx/systemd
- MySQL existente via `mysql2` y Drizzle ORM
- Active Directory via `ldapts`
- Vitest, Playwright, ESLint y Prettier desde el inicio

## Arranque local

```sh
npm install
npm run dev
```

Por defecto el servidor local queda en `http://localhost:5173`.

## Variables

Copiar `.env.example` a `.env` y completar valores locales. No commitear secretos reales.

La bandera `MYSQL_READ_ONLY=true` es obligatoria en las primeras fases: Inventario Next
debe comenzar leyendo datos, no modificando la base de produccion.

## Primer objetivo

Construir el detalle de equipo nuevo y la previsualizacion de acta desde una estructura
reconciliada:

1. datos crudos del script WMI;
2. componentes patrimoniales registrados;
3. discrepancias;
4. componentes finales que entran al acta.

Los modulos heredados que no se usan, como mapas, quedan fuera de Next.
