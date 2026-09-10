# Tareas LAN para Android

Aplicacion interna para Inventario Modular. Muestra `/movil/tareas` y recibe avisos del
mismo Spring Boot durante una jornada activada por el tecnico. No usa Firebase, FCM,
Google Play Services, analitica ni servidores de notificaciones externos.

## Probar el piloto

1. Conectar PC y celular al Wi-Fi/LAN con acceso al servidor.
2. Abrir `http://IP-DEL-SERVIDOR:8081/movil/tareas` en el navegador del celular.
3. Ingresar con una cuenta local o de dominio con permisos TAREAS/VER y TAREAS/EDITAR.
4. Descargar la APK desde el icono de celular. La descarga requiere autenticacion.
5. Instalarla mediante el mecanismo interno autorizado para los telefonos.
6. En la APK, configurar la direccion del servidor sin rutas. Ingresar con el usuario tecnico.
7. Activar **Avisos**, aceptar el permiso de notificaciones y configurar bateria sin
   restricciones. En algunos fabricantes tambien se necesita permitir inicio automatico.
8. Usar **Ajustes > Probar sonido** para comprobar el canal y el volumen.
9. Desde una PC con otra cuenta administradora, crear una tarea. El telefono debe mostrar
   un aviso sonoro y permitir abrir esa tarea al tocarlo.

La APK piloto acepta HTTP de la LAN para las pruebas locales. La variante release exige
HTTPS. No usar el piloto HTTP con credenciales de dominio reales en produccion.
Para produccion se necesita certificado del servidor emitido por la CA institucional,
CA instalada en los telefonos y una APK release firmada con clave institucional.
No se ignoran errores TLS ni se desactiva la verificacion del nombre del servidor.

## Funcionamiento y limites

- Android 8 o posterior, con Android System WebView actualizado (Chromium 103 o superior).
- El servicio consulta la intranet cada 10 segundos, con reintentos de hasta 60 segundos
  cuando se pierde la conexion. En esta version se usa consulta periodica HTTP, no WebSocket.
- Avisos al crear tareas desde PC, visor, API o movil. Los cambios de estado y comentarios
  se consultan en el modulo, pero no generan sonido en esta version.
- Los usuarios con TAREAS/VER pueden consultar los avisos de nuevas tareas, coherente con
  la visibilidad actual del modulo. El dispositivo no hace sonar las tareas creadas por su
  propio usuario. Probar siempre con administrador y tecnico distintos.
- El primer inicio toma el punto actual y no hace sonar el historial. Las desconexiones
  posteriores conservan el cursor por servidor y usuario para recuperar lo pendiente.
- Los avisos se guardan en la misma transaccion que la tarea. Un rollback no deja un aviso.
- No se guarda la clave en la APK. Se reutiliza la sesion del ingreso web; si vence, se
  revocan permisos o se cierra sesion, es necesario ingresar y activar avisos nuevamente.
- La notificacion permanente indica conexion y permite detener avisos. El servicio
  mantiene un bloqueo parcial de CPU durante la jornada; esto consume bateria. Al detener
  avisos se libera. No se inicia automaticamente al reiniciar el telefono o forzar el cierre.
- El permiso de bateria y las restricciones del fabricante afectan el funcionamiento en
  reposo. No se garantiza sonido si el usuario fuerza el cierre, apaga el Wi-Fi, silencia
  el canal o activa No molestar. La prueba con pantalla bloqueada debe hacerse en los
  modelos reales antes del despliegue.
- La web abierta puede emitir un sonido al activarlo con el boton de campana. El navegador
  puede suspenderla en segundo plano; ese sonido no reemplaza al servicio Android.
- No hay trabajo sin conexion: los formularios necesitan al servidor. El sistema conserva
  avisos pendientes, no una copia de las tareas para editar fuera de linea.
- La app limita sus peticiones al origen configurado y rechaza servidores con direcciones
  publicas. El aislamiento completo se aplica ademas en firewall, VLAN y Wi-Fi institucional.

## Compilar

Requisitos: JDK 17 o 21, SDK Android 35, Build Tools 35.0.0. Gradle Wrapper 8.11.1 y
Android Gradle Plugin 8.9.2 estan fijados en el proyecto. La preparacion del entorno
descarga herramientas de Google/Gradle; la APK en ejecucion no depende de esos servicios.

```powershell
$env:ANDROID_HOME = 'C:\ruta\al\android-sdk'
.\gradlew.bat assembleDebug lintDebug
```

En Linux: `./gradlew assembleDebug lintDebug`. Con dependencias previamente preparadas,
agregar `--offline`. La salida es `app/build/outputs/apk/debug/app-debug.apk`.

Para publicar el piloto local, copiarlo a
`output/android/inventario-tareas-lan-piloto.apk` en la raiz de Inventario Modular.
Esa carpeta no se incluye en Git. El servidor tambien admite configurar
`INVENTARIO_MOVIL_APK_PATH` con una ruta absoluta a la APK distribuida internamente.

La firma debug solo sirve para el piloto. Conservar fuera de Git la clave de firma
institucional y configurar firma de release antes de distribuir una version productiva.

## Validacion en telefonos

Registrar modelo, version de Android/WebView, cuenta, hora de creacion y hora de aviso.
Probar pantalla encendida, bloqueada 30 minutos, reposo Doze, perdida de Wi-Fi y
reconexion, servidor reiniciado, sesion cerrada, permisos revocados y dos tecnicos
intentando tomar la misma tarea. Tras reinstalar se pierde el cursor local.

Comandos opcionales para una prueba supervisada con ADB:

```sh
adb shell dumpsys deviceidle force-idle
adb shell dumpsys deviceidle unforce
adb shell dumpsys battery reset
```

Las restricciones de reposo y los servicios en primer plano estan documentados en
[Android Doze](https://developer.android.com/training/monitoring-device-state/doze-standby)
y [tipos de servicio](https://developer.android.com/develop/background-work/services/fgs/service-types).

## Validacion realizada en PC

Compilacion y lint de la APK, firma verificada con apksigner, pruebas Spring Boot de
ingreso/permisos/avisos/rollback/paginacion/toma simultanea, y comprobacion web adaptable.
No habia un dispositivo fisico conectado al desarrollar este piloto: el sonido y la
recepcion con pantalla bloqueada quedan pendientes de esa prueba de campo.

Ultima verificacion del 10/09/2026: assembleDebug y lintDebug completaron sin errores.
Lint reporto 9 advertencias: dos por commit sincrono de preferencias (se usa en el
worker para guardar el cursor antes de avanzar), JavaScript habilitado en WebView,
dos por aceptar CA del usuario, HTTP de debug, reglas de respaldo para versiones
anteriores a Android 12 y dos textos nativos sin recursos de traduccion. No equivalen
a una auditoria de seguridad aprobada; revisar antes de la distribucion general.

La guia de firma y despliegue offline esta en
[Instalacion de tareas LAN](../docs/inventario-modular/instalacion-tareas-lan-2026-09-10.md).
