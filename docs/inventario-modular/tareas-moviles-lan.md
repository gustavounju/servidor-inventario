# Modulo movil y avisos internos

Primera version: 10 de septiembre de 2026.

## Accesos

- Modulo independiente: `/movil/tareas`.
- Ingreso local/Active Directory: `/movil/login`.
- Descarga autenticada de Android: `/api/v1/movil/apk`, disponible cuando existe el archivo configurado.
- En el Panel General hay un acceso **Tareas en el celular** junto al visor.

El visor de administracion actualiza fichas y contadores cada 30 segundos con **En vivo**.
Conserva los filtros de la direccion abierta y pausa la actualizacion al editar un
formulario, para no perder lo escrito. Guardar o volver a abrir el visor reanuda el seguimiento.

El movil usa las operaciones y autorizaciones existentes de `/api/v1/tareas-tecnicas`.
Permite crear, buscar por tarea/usuario/equipo, tomar, editar, comentar, finalizar,
cancelar y eliminar segun los permisos existentes. Las tareas creadas por un tecnico
quedan a su cargo; un administrador puede dejarlas libres para que alguien las tome.
El estado visible de una tarea abierta es Pendiente, aunque internamente se conserva
EN_PROCESO para las tareas tomadas. Finalizadas y canceladas se distinguen.

## Servidor Linux

Se utiliza el mismo proceso Spring Boot y la misma base MySQL. No se necesita otro
servidor de mensajes. Los nuevos endpoints respetan la autenticacion, los permisos
TAREAS/VER y el filtro LAN existente. Los cambios de tareas conservan proteccion CSRF.

La migracion `V15__avisos_tareas_lan.sql` agrega `tareas_avisos` y una secuencia bloqueada
durante el guardado. Esa secuencia evita que dos transacciones concurrentes produzcan
avisos confirmados fuera del orden del cursor. No hay FK desde el aviso a la tarea:
el historial puede sobrevivir a una eliminacion, que el cliente presenta como tarea
ya no disponible. Los avisos no tienen purga automatica en esta version.

Los perfiles `casa` y `local` ejecutan este SQL idempotente al arrancar, ya que actualmente
tienen Flyway desactivado. Para otro perfil, ejecutar V15 mediante el mecanismo de
migracion de ese entorno antes de habilitar esta version. No se modificaron datos del
servidor del trabajo durante el desarrollo local.

Ejemplo de variable en la unidad systemd existente, usando la ruta real del archivo:

```ini
Environment="INVENTARIO_MOVIL_APK_PATH=/opt/inventario-modular/distribucion/tareas-lan.apk"
```

El usuario del servicio debe poder leer la APK. No es necesario incluirla dentro del JAR.
Usar HTTPS con un nombre DNS interno y certificado de la CA institucional para el
despliegue de produccion. Android admite la CA institucional instalada en el almacen
de certificados del dispositivo. La red debe permitir el trafico entre clientes Wi-Fi
y servidor; el aislamiento entre clientes del punto de acceso puede impedirlo.

## API de avisos

`GET /api/v1/movil/sesion` devuelve usuario actual y permisos de operacion.

`GET /api/v1/movil/avisos` inicia el seguimiento en el ultimo cursor, sin historial.

`GET /api/v1/movil/avisos?despuesDe=123` devuelve hasta 100 avisos posteriores y
`siguiente`. El cliente guarda el cursor luego de procesar el lote. La consulta puede
repetirse tras una desconexion; el servidor no elimina avisos al consultarlos.

Los avisos son anuncios de creacion para usuarios habilitados en TAREAS. No hay aun
seleccion de destinatarios por sede ni confirmacion de lectura por tecnico. Las
operaciones posteriores de la tarea se siguen consultando por la API existente.

## Instalacion Android y prueba de campo

Ver [guia de la APK](../../android/README.md). La web funciona en el navegador;
los avisos de fondo requieren activar el servicio Android y configurar el telefono.
No se validaron dispositivos fisicos, iOS ni entrega durante Doze en esta PC.

Pruebas automatizadas del servidor:

```powershell
.\mvnw.cmd '-Dtest=TareaMovilControllerTests,TareaTecnicaControllerTests,TareaTecnicaPageControllerTests,LocalAuthenticationConfigTests' test
```

La prueba movil incluye ingreso local y destino seguro, permisos, CSRF, persistencia
de avisos, inicializacion idempotente, rollback, paginacion y toma concurrente. Active
Directory se reutiliza sin cambios, pero su conexion real debe probarse en el trabajo.
