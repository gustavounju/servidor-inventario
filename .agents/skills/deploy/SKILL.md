---
name: deploy
description: Usar para llevar un cambio ya mergeado a producción real, vía la sesión PuTTY/SSH al servidor Ubuntu. Reemplaza al land-and-deploy de gstack (pensado para plataformas como Vercel/Fly.io) porque acá el deploy es manual. Disparadores: "vamos a producción", "/deploy", "esto hay que subirlo al servidor del trabajo".
---

# Deploy — De "mergeado" a "verificado en producción", a mano por PuTTY

Este sistema no tiene CI/CD. El deploy es un procedimiento manual que vos mismo ejecutás
en una sesión PuTTY/SSH contra el Ubuntu de producción. Este skill es la versión
disciplinada de eso: un runbook que se sigue siempre igual, no algo que se reinventa cada
vez ni se hace "de memoria". Reemplaza la información dispersa en
`CHECKLIST_PUTTY_MANANA.md`, `GUIA_UBUNTU_MANANA.md` y `DEPLOY_README.md` — si esos tres
archivos dicen cosas distintas entre sí (ej. la IP de la base de datos), este skill usa
los valores confirmados más abajo y señala la inconsistencia para que se corrija en los
tres documentos a la vez.

## Antes de tocar la sesión PuTTY

1. Confirmá que el cambio ya pasó por `/review`, `/qa`, y `/ship` (PR/MR mergeado a la
   rama que se deploya).
2. Confirmá si el cambio incluye una migración de esquema (`database/migrations.py`
   tocado, o un script de migración nuevo). Si sí, este deploy necesita un paso extra de
   backup de la base antes de aplicarla — no se salta nunca.
3. Activá `/guard` mentalmente para toda la sesión que sigue: cada comando que se vaya a
   pegar en la terminal PuTTY se explica antes de sugerirlo, y se espera confirmación.

## Datos de producción confirmados (verificar contra el `.env` real del servidor antes
de asumir que no cambiaron)

- Host de la app: `/opt/inventario/` en el Ubuntu de producción
- DB_HOST: `10.15.3.20` — **no** `10.15.0.62` (ese valor en `CONTEXT.md` está
  desactualizado; si vas a tocar `CONTEXT.md`, corregilo de paso)
- DB_NAME: `inventario_prod`
- URL pública HTTPS: `https://10.15.2.251:5000`
- URL pública HTTP (fallback / móviles): `http://10.15.2.251:8080`
- Servicio systemd: `inventario` (`deployment/inventario.service`)

## El runbook

1. **Backup antes que nada.** Si el deploy incluye una migración de esquema, correr
   (o recordarle a la persona correr) un backup de `inventario_prod` antes de seguir.
   Revisar si `backup_mysql.sh` ya cubre esto o si hace falta uno manual.
2. **Conectar por PuTTY/SSH** al Ubuntu de producción.
3. `cd /opt/inventario && git status` — confirmar que no hay cambios locales sin
   commitear en el servidor que se vayan a perder con el pull (si los hay, frenar y
   preguntar qué son antes de seguir).
4. `git pull` — confirmar que trajo exactamente el commit esperado (el que se mergeó
   en GitLab), no más ni menos.
5. Si el pull trajo cambios en `requirements.txt`, instalar dependencias nuevas antes
   de reiniciar el servicio.
6. Si el pull trajo cambios en `database/migrations.py` o templates, correr
   `bash deploy_ubuntu.sh` (que ya encapsula instalar dependencias, regenerar `.env` si
   hace falta, copiar configs de systemd/nginx, y reiniciar servicios) — en vez de hacer
   los pasos sueltos a mano, para no repetir lo que el script ya automatiza.
7. **Verificar el estado del servicio** después del restart (`systemctl status
   inventario`, revisar el log de arranque).
8. **Probar contra producción real**, no solo confiar en que el servicio está "active
   (running)": abrir `https://10.15.2.251:5000` (o el fallback HTTP si HTTPS falla) y
   confirmar que el login funciona y que la página principal carga sin error 500.
9. Si algo se rompió: el rollback es `git checkout <commit-anterior>` +
   `bash deploy_ubuntu.sh` de nuevo, o restaurar el backup de base si la migración fue
   el problema. Decidir y ejecutar el rollback con la misma pausa de confirmación que el
   resto de los comandos de esta lista — un rollback apurado puede romper algo distinto.

## Primer login después de un deploy desde cero

Si es una instalación nueva (no una actualización), el sistema crea un usuario
`administrador` inicial automáticamente si `app_users` está vacía. El primer paso
siempre es entrar con ese usuario, crear el superusuario real de la persona, cerrar
sesión, volver a entrar con el usuario propio, y **borrar el usuario `administrador`**
— no dejarlo activo con la contraseña default. Si esa contraseña default sigue
hardcodeada en algún `.md` del repo (ver hallazgo en `/cso`), tratá eso como pendiente
hasta que se resuelva.

## Después del deploy

Sugerí correr `/document-release` si el deploy cambió algo de la estructura, las
variables de entorno, o resolvió/agregó un ítem de "Problemas Conocidos" en
`CONTEXT.md` — para que el próximo deploy no dependa de memoria.
