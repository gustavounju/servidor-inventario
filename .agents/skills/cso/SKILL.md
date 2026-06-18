---
name: cso
description: Auditoría de seguridad estilo OWASP Top 10, obligatoria antes de mergear cambios en Vault, Auth, o base de datos, y recomendada antes de cualquier release grande. Busca inyección SQL, secretos filtrados, control de acceso roto, y configuración insegura. Disparadores: "auditoría de seguridad", "/cso", "¿esto es seguro?".
---

# CSO — Chief Security Officer para un sistema de un organismo judicial

Este sistema corre en infraestructura del Poder Judicial y maneja inventario de equipos,
roles de usuario, y un módulo Vault de credenciales/secretos. Tratá cada hallazgo con la
seriedad que corresponde a eso, no como un linter genérico.

## Áreas de revisión, en orden de prioridad para este proyecto

**1. Inyección SQL.** Recorré todo cursor.execute / conn.execute en los archivos
tocados (o, en una auditoría completa, en `blueprints/`, `services/`, `database/`).
Cualquier interpolación de datos de usuario en el string de la query (f-string,
`.format()`, concatenación, `%` fuera de los placeholders del driver) es CRÍTICO.
Verificá también los casos donde se construye una lista de placeholders dinámicamente
(`IN (%s, %s, ...)`) — confirmá que los valores en sí siguen yendo como parámetros y
nunca como texto directo en el SQL.

**2. Vault y secretos** (`blueprints/bp_vault.py`, `templates/vault.html`). Confirmá:
- los datos sensibles se cifran en reposo usando la librería `cryptography` ya presente
  en `requirements.txt` (no se guardan en texto plano)
- la clave de cifrado del Vault no está hardcodeada en el código ni en un archivo
  versionado — debe venir de variable de entorno
- el acceso al Vault respeta el sistema de roles (¿cualquier usuario autenticado puede
  ver secretos, o solo Administrador/Sistemas?)

**3. Autenticación y roles** (`utils/auth.py`). Confirmá:
- las contraseñas se hashean (no se comparan en texto plano)
- el control de acceso por rol se valida en el servidor (cada ruta de cada blueprint),
  no solo ocultando elementos en el HTML/JS
- las cookies de sesión tienen `Secure`, `HttpOnly`, y `SameSite` configurados de forma
  razonable para el entorno de producción
- `FLASK_SECRET_KEY` sigue viniendo obligatoriamente de entorno (ya hay una validación
  en `servidor.py` que lo exige — no debilitarla nunca con un valor default)

**4. Secretos filtrados en el repo.** Buscá credenciales reales, API keys (Gemini,
Green-API, Firebase), connection strings, o tokens en cualquier archivo que no sea
`.env` (que ya está gitignoreado). Prestá atención especial a los scripts sueltos de la
raíz (`scratch_*.py`, `tmp_*.py`, `debug_*.py`, archivos `.bak`, `.backup`) — son los
candidatos más probables a tener una credencial pegada a mano durante una sesión de
debugging y olvidada ahí.

Hallazgo conocido a resolver: `CHECKLIST_PUTTY_MANANA.md` y `GUIA_UBUNTU_MANANA.md`
tienen la contraseña real del usuario `administrador` inicial escrita en texto plano.
Mientras no se rote esa contraseña y se reemplace por un placeholder en ambos archivos
(igual que ya hace `CONTEXT.md` con `[OCULTA]`), tratá esto como un hallazgo Crítico
abierto en cualquier auditoría que corras, no lo vuelvas a "descubrir" cada vez — y no
lo cierres hasta confirmar que efectivamente se rotó.

**5. Configuración de producción.** Confirmá que `debug=False` en los `app.run()` que
efectivamente corren en producción (servidor.py ya lo hace en la mayoría de los casos
— revalidá si cambió). Revisá `deployment/nginx_inventario.conf` por headers de
seguridad básicos faltantes (`X-Frame-Options`, etc.) si el cambio toca esa zona.

**6. Integraciones externas.** El asistente de IA (`services/ai_assistant.py`) recibe
datos del sistema y los manda a una API externa (Gemini) — confirmá que no se le está
pasando información sensible del Vault o credenciales sin necesidad. Lo mismo para
WhatsApp (Green-API): confirmá qué datos del inventario se mandan por ese canal y si
corresponde.

**7. Subida de archivos** (`uploads/`, OCR de PDFs, fotos de racks). Confirmá que se
valida el tipo de archivo real (no solo la extensión) y que no se puede usar para subir
algo ejecutable o sobrescribir un path arbitrario en el servidor.

## Formato del hallazgo

Para cada finding: severidad (Crítico / Alto / Medio / Bajo), archivo:línea, evidencia
concreta (qué hace el código hoy), y la corrección recomendada. No reportes "buenas
prácticas generales" sin un hallazgo concreto en este código — esto es una auditoría de
este sistema, no una charla genérica de seguridad.

## Si encontrás algo Crítico

Decilo primero, claro, y recomendá no mergear/deployar hasta resolverlo — incluso si
implica frenar un `/ship` que ya estaba en curso.
