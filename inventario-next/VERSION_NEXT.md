# Inventario Next - version de avance

## v0.1-preview

Esta version consolida el primer frente funcional de Inventario Next, en paralelo al Flask
estable.

- Lee la configuracion MySQL heredada del proyecto actual en modo lectura.
- Lista equipos reales y muestra detalle enriquecido desde `pcs` y `components`.
- Reconcilia monitores y discos para evitar duplicados y separar WMI concatenado.
- Expone gestion de usuarios en lectura, unificando `app_users` y `ad_users`.
- Expone tareas reales con solicitante enriquecido por fuero cuando existe match de dominio.
- Genera vista imprimible de actas de entrega desde el detalle reconciliado.
- Mantiene APIs JSON para equipos, usuarios, solicitantes, tareas y actas.

Pendiente para la siguiente version:

- Generacion PDF server-side.
- Autenticacion/autorizacion propia de Next.
- PWA movil para tecnicos con certificados.
- Escrituras controladas, luego de definir permisos y auditoria.
