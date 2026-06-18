---
name: document-release
description: Usar después de ship, o cuando la documentación del proyecto quedó desactualizada respecto al código real. Mantiene CONTEXT.md (la fuente de verdad real del proyecto) y el README sincronizados con lo que efectivamente cambió. Disparadores: "actualizá la documentación", "/document-release", "el contexto está desactualizado".
---

# Document Release — Mantener CONTEXT.md como la verdad, no como un recuerdo viejo

En este proyecto, `CONTEXT.md` es el documento que de verdad se usa (el `README.md`
todavía tiene el boilerplate default de GitLab y no se actualiza). Tu trabajo es que
`CONTEXT.md` siga siendo confiable después de cada cambio relevante — si alguien lo lee
para entender el sistema, no debería encontrar información vieja o contradictoria con el
código actual.

## Qué revisar después de un cambio

- **Stack técnico**: ¿se agregó una dependencia nueva a `requirements.txt`
  (notificaciones, IA, OCR, lo que sea)? Reflejalo en la sección de Stack Técnico.
- **Estructura del proyecto**: ¿se agregó un blueprint, un servicio, o una carpeta
  nueva? Actualizá el árbol de estructura.
- **Roles y permisos**: ¿cambió qué puede hacer cada rol (Administrador, Sistemas,
  Técnico, Usuario)? Actualizá la sección de roles.
- **Módulos disponibles**: ¿se agregó o cambió una ruta principal? Actualizá la tabla de
  módulos con su URL.
- **Variables de entorno**: ¿el cambio requiere una variable nueva en `.env`? Agregala
  (con placeholder, nunca el valor real) tanto en `CONTEXT.md` como en `.env.example`.
- **Problemas conocidos**: si el cambio resolvió algo de la lista de "Problemas
  Conocidos", sacalo de ahí. Si introdujo una limitación nueva conocida, agregala.
- **Próximas mejoras**: si el cambio implementó algo de esa lista, movelo de "próximas
  mejoras" a completado (o simplemente quitalo de la lista).
- **Fecha y versión**: actualizá "Última actualización" y, si corresponde, la versión en
  `utils/constants.py` (`APP_VERSION`).

## Sobre el README.md

El README actual es el template default de GitLab sin contenido real del proyecto. Si
tenés ocasión (no hace falta forzarlo en cada `/document-release` chico), proponé
reemplazarlo por una versión real basada en `CONTEXT.md`: qué es el sistema, cómo se
instala/corre en desarrollo, y un link o resumen de la estructura — pensado para que
alguien nuevo en el equipo de Informática lo pueda leer y entender el sistema en cinco
minutos, sin tener que abrir `CONTEXT.md` entero.

## Qué NO hacer

No inventes información que no esté confirmada por el código o por lo que la persona te
dijo explícitamente en la sesión. Si no estás seguro de un dato (por ejemplo, una IP de
producción o una credencial), dejalo como estaba o marcalo como "a confirmar" en vez de
adivinar.
