# Traspaso tecnico: tareas, visor y Android LAN

Entrega documental del 10 de septiembre de 2026. Proyecto Inventario Modular, Centro
Judicial San Pedro. Repositorio: https://gitlab.com/gustavoeliasm/inventario-modular
Rama: `primeros-pasos`. Base anterior a esta entrega: `f4d5960`.

Este documento y `instalacion-tareas-lan-2026-09-10.md` son las fuentes editables del
PDF `output/pdf/traspaso-tareas-lan.pdf`. El codigo del commit de entrega prevalece
sobre documentos historicos. El commit exacto queda en `VERSION.txt` del paquete
transportable; no se incluye en este PDF para evitar una referencia circular al commit.

## 1. Resumen y estado real

El administrador dispone de un visor independiente para PC/TV y de accesos desde el
Panel General. Los tecnicos disponen de una web movil y una APK Android piloto para
operar tareas y consultar avisos dentro de la LAN. El servidor de mensajes es el
mismo Spring Boot: no se agregaron Firebase, FCM, servicios Google, MQTT ni otro demonio Linux.

La web y las API estan implementadas y probadas localmente. La APK se compilo y se
verifico su firma debug. NO se probo un telefono fisico, Active Directory real ni
el MySQL del trabajo durante esta entrega. No se desplego en produccion.

La distribucion general de la APK queda condicionada a HTTPS institucional, firma
release, validacion de bateria/Doze y prueba de campo. El piloto no es una garantia
de recepcion permanente. La aplicacion no funciona para editar tareas sin conexion.

## 2. Requerimientos y decisiones

1. Ver tareas en una direccion independiente, sin menu general, para la sala de reuniones.
2. Crear tareas, ver comentarios, identificar solicitante y tecnico responsable.
3. Mostrar pendientes y actividad diaria, con busqueda y fichas compactas.
4. Permitir acceso local o de dominio desde celulares conectados por Wi-Fi institucional.
5. Avisar con sonido cuando otra persona crea una tarea, sin servidores externos.
6. Mantener autenticacion, permisos del modulo, auditoria y proteccion CSRF existentes.

Se conservaron los estados de base `PENDIENTE`, `EN_PROCESO`, `CERRADA` y `CANCELADA`.
Tomar una tarea asigna responsable y utiliza `EN_PROCESO`; la interfaz movil y la
etiqueta del visor presentan ambas situaciones abiertas como Pendiente. No se hizo
una migracion destructiva del enum. Consultar las inconsistencias pendientes en la seccion 7.

La web abierta usa sonido WebAudio activado por el usuario. No se eligio una PWA como
solucion de avisos en reposo: el navegador puede suspenderla. Android usa un servicio
visible durante una jornada activada por el tecnico, con consulta periodica al servidor.
Las restricciones de reposo siguen aplicando y requieren prueba por modelo de telefono.

## 3. Recorrido funcional

Visor: `/admin/tareas/visor`. Es una plantilla autonoma sin barra lateral ni cabecera
del inventario. Ofrece filtros, formularios y comentarios, conservando el origen del
formulario mediante `origen=visor`. Las fichas se compactaron para mostrar mas tareas.
El modo En vivo refresca el tablero y contadores cada 30 segundos. Si se escribe en
un formulario o este tiene el foco, se pausa para preservar el borrador. Guardar o
volver a abrir la pagina permite reanudar. No hay modo publico sin autenticacion.

Movil: `/movil/login` y `/movil/tareas`. El formulario envia a `/login` con
`destino=movil`, y vuelve al modulo movil. Un destino diferente no puede redirigir
a una web externa. La cuenta debe tener `TAREAS/VER`; las acciones requieren los
permisos y reglas de propiedad de la API existente.

El movil permite crear, tomar, editar, comentar, cerrar, cancelar, reabrir y eliminar
segun autorizacion. Un tecnico crea tareas a su nombre; el administrador puede dejarlas
sin tomar. Hay vistas Pendientes, Mis tareas, Finalizadas y Todas. La busqueda movil
incluye ID, titulo, descripcion, solicitante, fuero, responsable y equipo; no comentarios.
La busqueda del visor si incluye comentarios. La nueva tarea movil usa PC-GENERICA;
no hay selector de equipo en ese formulario. Al editar se conserva el equipo existente.

Se muestran hasta 40 filas por tanda con Ver mas. Esto limita el renderizado, no el
volumen de la respuesta de la API: la paginacion real del servidor sigue pendiente.

## 4. Contratos y persistencia

Las nuevas rutas de solo lectura son:

- `GET /api/v1/movil/sesion`: usuario actual, `puedeEditar` y `administrador`.
- `GET /api/v1/movil/avisos`: cursor actual, sin historial, para iniciar seguimiento.
- `GET /api/v1/movil/avisos?despuesDe=N`: hasta 100 eventos posteriores, en orden.
- `GET /api/v1/movil/apk`: descarga autenticada de un archivo configurado en el servidor.

Las mutaciones reutilizan `/api/v1/tareas-tecnicas`, incluidos tomar, estado y comentarios.
No se creo una segunda logica de negocio para celulares. Las API sin sesion responden
401; sin permiso, 403; tomar una tarea finalizada o asignada a otro tecnico produce 409.
Un cursor negativo produce 400. La APK ausente produce 404. CSRF no se desactivo.

Ejemplo de respuesta de avisos (datos ficticios):

```json
{
  "siguiente": 42,
  "avisos": [{
    "id": 42,
    "tareaId": 18,
    "titulo": "Revisar impresora",
    "autor": "administrador.ejemplo",
    "creadoEn": "2026-09-10T09:00:00"
  }]
}
```

V15 crea `tareas_aviso_secuencia`, con una fila id=1 y ultimo_id, y `tareas_avisos`,
con id, tarea_id, titulo, autor y creado_en. Son tablas aditivas; no borran tareas.
La secuencia usa SELECT FOR UPDATE dentro de la misma transaccion que la creacion,
con propagacion MANDATORY. La tarea, auditoria y aviso confirman o revierten juntos.
No reemplazar la secuencia por un autoincremento sin analizar el orden de confirmacion:
un cursor podria adelantarse y omitir una transaccion que confirma mas tarde.

El cursor de respuesta avanza hasta el ultimo evento entregado, no hasta el ultimo
existente si quedan otras paginas. Ante una restauracion con cursor cliente mayor
al servidor, se vuelve al punto actual sin emitir historial. No se garantiza entrega
exactamente una vez: un cierre entre notificacion y persistencia puede repetir un aviso.

No existe FK de aviso a tarea: una eliminacion no borra el anuncio historico.
No hay purga, destinatarios por sede, acuses de lectura ni escalamiento. Los anuncios
son visibles para todas las cuentas con TAREAS/VER. Solo la creacion genera un aviso;
comentarios, toma y cierre no generan sonido en esta version.

Dos tomas simultaneas usan el bloqueo pesimista `buscarParaTomar` y verifican asignacion
y estado bajo ese bloqueo. Esto protege la toma; no constituye una auditoria completa
de todas las carreras posibles entre editar, cerrar, eliminar y reasignar.

## 5. Android y seguridad de red

Paquete release: `ar.gov.justiciajujuy.tareaslan`. Piloto: el mismo con sufijo `.piloto`.
Version 0.1.0; versionCode 1. Minimo Android 8 / API 26; compile y target SDK 35.
WebView requiere Chromium 103 o superior para las API JavaScript utilizadas.
Gradle 8.11.1, Android Gradle Plugin 8.9.2, Build Tools 35.0.0, Java 17 o 21.

`MainActivity` aloja el WebView con navegacion al mismo origen, sin puente JavaScript
nativo, sin acceso a archivos y sin cookies de terceros. La app usa recursos locales;
Safe Browsing esta desactivado para no realizar consultas externas desde ese mecanismo.
La sesion de Spring se comparte mediante CookieManager. No se persiste la clave en
codigo nativo; la cookie de sesion sigue siendo sensible y requiere custodia del celular.

`LanClient` admite un origen sin ruta ni credenciales. Release solo admite HTTPS;
debug tambien permite HTTP para laboratorio. Se verifican IP privadas/loopback,
origen y TLS. La CA institucional instalada puede ser usada por la APK; no se ignoran
errores de certificado ni de nombre. La validacion de IP no reemplaza un firewall
de salida ni constituye una defensa completa ante manipulacion de DNS.

`AvisosService` se activa con Avisos. Usa notificacion permanente, canal de tareas
con sonido/vibracion y consulta cada 10 segundos; sin red aplica espera hasta 60.
Cada ciclo verifica la identidad activa. Un lote lleno se continua al segundo siguiente.
El cursor se guarda por origen/usuario despues de notificar. No suenan eventos propios.
La primera activacion establece el punto actual, sin hacer sonar tareas anteriores.

Mantiene un bloqueo parcial de CPU mientras esta activo: consume bateria y no elimina
todas las restricciones de Doze. Al detenerlo libera el bloqueo. No arranca al reiniciar
el telefono ni tras forzar cierre; usa START_NOT_STICKY. Una sesion vencida o permiso
revocado obliga a ingresar y activar de nuevo. No molestar, volumen, canal silenciado,
restricciones del fabricante y perdida de Wi-Fi pueden impedir el aviso.

El permiso Android INTERNET tambien permite acceso LAN; no implica dependencia de
Internet. Para cumplir el aislamiento total, aplicar reglas institucionales en Wi-Fi,
VLAN y firewall. La descarga de dependencias se hace solo al preparar la compilacion,
no al ejecutar el JAR o la APK. No hay implementacion equivalente para iPhone.

## 6. Mapa del codigo y pruebas

Base Java: `src/main/java/ar/gov/justiciajujuy/sanpedro/inventario/`.

- `web/TareaTecnicaPageController.java`: visor, busquedas, metricas y retorno de formularios.
- `web/TareaMovilController.java`: pagina movil, sesion, avisos y APK protegida.
- `web/TareaTecnicaController.java`: API existente y reglas de autorizacion de operaciones.
- `tareas/TareaTecnicaService.java`: creacion transaccional, toma y resumen diario.
- `tareas/TareaAvisoService.java`: secuencia persistente, lotes y cursores.
- `tareas/TareaTecnicaRepository.java`: busqueda ampliada y bloqueo de toma.
- `config/SecurityConfig.java`: login y destinos fijos, seguridad de API y filtro LAN.
- `config/DataSourceConfig.java`: seleccion primaria/fallback del perfil local.

Recursos: `src/main/resources/`.

- `templates/admin/tareas-visor.html`, `static/css/admin.css`: visor compacto independiente.
- `templates/movil/`, `static/css/movil.css`, `static/js/movil-tareas.js`: interfaz movil.
- `static/js/visor-live.js`: refresco sin perder formularios.
- `static/js/lucide.min.js` y `lucide.LICENSE`: iconos locales, version 0.468.0.
- `db/migration/V15__avisos_tareas_lan.sql`: tablas de avisos.
- `application-{local,casa}.properties`: inicializacion SQL; Flyway sigue apagado.

Android: `android/app/src/main/java/ar/gov/justiciajujuy/tareaslan/` contiene
MainActivity, LanClient y AvisosService. Revisar tambien Manifest, reglas de respaldo
y configuraciones TLS main/debug. `android/README.md` contiene compilacion y prueba.

Pruebas: `src/test/java/.../web/TareaMovilControllerTests.java` tiene siete casos
que cubren login/destino seguro, permisos/CSRF, avisos, rollback, paginacion,
inicializacion idempotente, restauracion de cursor y toma concurrente/finalizada.
Los ocho casos de TareaTecnicaPageControllerTests cubren las paginas administrativas.

Evidencia local registrada en esta entrega:

- Suite Maven: 125 pruebas, cero fallos, errores y omitidas.
- APK debug: compilacion y lint correctos; firma verificada con apksigner.
- Lint Android: cero errores; advertencias pendientes documentadas en android/README.md.
- Navegador: recorrido crear, tomar, comentar y cerrar; escritorio y movil de 390 px sin desborde.
- Visor: refresco automatico observado, consola sin errores durante la prueba.
- Descarga autenticada de APK: HTTP 200, tipo correcto y hash igual al archivo.

La tarea local #35 fue una prueba del circuito y quedo cerrada. La base H2 de casa y
sus credenciales no se distribuyen. Los reportes Maven se generan en target/surefire-reports;
el kit incluye un resumen de resultados y hashes. La CI de GitLab ejecuta Maven y
publica JAR por siete dias; no compila Android ni genera este PDF. Un push exitoso
no demuestra que el runner haya ejecutado o aprobado la pipeline.

## 7. Pendientes y riesgos conocidos

Prioridad antes de anunciar produccion movil:

1. Firmar release con clave institucional custodiada fuera del repositorio, habilitar
   HTTPS confiable y probar en telefonos reales. El kit trae solo APK piloto debug.
2. Ensayar V15 y arranque con una copia MySQL del trabajo. Las pruebas actuales usan H2.
3. Verificar AD real, roles locales, Wi-Fi, DNS, certificado, perdida de red y reposo.
4. Resolver semantica de metricas del visor: realizadasHoy usa cerradoEn e incluye
   canceladas; Between incluye el limite de medianoche del dia siguiente. Usar estado
   CERRADA e intervalo semiabierto, con pruebas de cancelacion y cambio de dia.
5. Unificar filtros: el contador Pendientes suma PENDIENTE y EN_PROCESO, pero el filtro
   PENDIENTE selecciona solo ese enum. Los selectores aun muestran EN_PROCESO. El movil
   ya agrupa ambos. Algunos botones Tomar administrativos pueden aparecer en tareas
   finalizadas sin responsable; el backend ahora rechaza esa accion con 409.

Prioridad posterior:

- Agregar paginacion real, medir volumen de comentarios y carga LDAP: el refresco del
  visor solicita la pagina completa y puede recalcular datos del dominio cada 30 segundos.
- Acordar retencion de avisos sin destruir cursores activos; no hay limpieza automatica.
- Evaluar acuses por dispositivo y alcance por sede si se requiere trazabilidad de entrega.
- Revisar bateria y permisos por fabricante, pruebas instrumentadas y distribucion interna.
- Probar conflictos entre cierre/edicion/toma; el test actual cubre dos tomas simultaneas.
- Unificar migraciones antes de activar Flyway: el historial contiene versiones V6 duplicadas.
- Revisar fallback MySQL y confianza de cabeceras proxy. LAN-only no es aislamiento completo.

No resolver estos puntos borrando estados, desactivando CSRF/TLS o agregando push externo.

## 8. Continuar con otra IA

Entregar este PDF, ambas fuentes Markdown y el repositorio o bundle de la entrega.
No entregar archivos de entorno, claves de firma, cookies, respaldos de base ni credenciales
de dominio. Graphify contiene un grafo local anterior al modulo movil: sirve como mapa
historico, pero no como fuente completa de esta version; esta ignorado por Git.

Prompt sugerido:

```text
Continua Inventario Modular, rama primeros-pasos.
Lee docs/inventario-modular/traspaso-tareas-lan-2026-09-10.md
y docs/inventario-modular/instalacion-tareas-lan-2026-09-10.md.
Verifica git status y el commit del paquete antes de editar.
No reviertas cambios ajenos ni uses servicios externos en ejecucion.
El servidor es Java 21 / Spring Boot 4.0.1 / MySQL.
La APK Android es piloto: no afirmar que funciona en reposo sin medirlo.
Prioriza la lista de pendientes y conserva permisos, CSRF y TLS.
No modificar el servicio legado inventario.service.
Actualiza pruebas, documentacion y bitacora con cada cambio.
```

## 9. Referencias

Fuentes primarias consultadas para firma y restricciones Android el 10/09/2026:

- Firma y compilacion por consola: https://developer.android.com/build/building-cmdline
- Verificacion de APK: https://developer.android.com/tools/apksigner
- Reposo y excepciones: https://developer.android.com/training/monitoring-device-state/doze-standby
- Servicios en primer plano: https://developer.android.com/develop/background-work/services/fgs/service-types

Fuentes locales complementarias: `android/README.md`, `tareas-moviles-lan.md`,
`actualizacion-produccion-inventario-modular.md`, `usuarios-locales-y-active-directory.md`
y `bitacora-del-proyecto.md`. Los documentos historicos contienen decisiones superadas:
para esta entrega, seguir el runbook fechado y verificar siempre la unidad real.
