# Instalacion en el trabajo sin Internet

Runbook de la entrega del 10/09/2026. Orientado a actualizar el servidor Linux existente,
no a instalar todo el sistema desde cero. Ejecutar en ventana de mantenimiento con
respaldo y autorizacion institucional. No se ejecutaron estos pasos contra produccion.

## 1. Que llevar y que se puede habilitar

Llevar `output/entrega-lan.zip`, generado por `scripts/preparar-entrega-lan.ps1`.
Contiene JAR compilado, APK piloto, PDF, fuentes Markdown, V15 de referencia, bundle
Git, VERSION.txt, resumen de pruebas y SHA256SUMS. No lleva base de datos, secretos,
JDK, MySQL, Nginx, SDK Android ni caches de compilacion. El servidor no necesita Maven
ni Android SDK para ejecutar estos binarios.

El JAR habilita web movil, visor y API. La APK incluida es debug para laboratorio:
no distribuir como aplicacion productiva ni ingresar claves reales de dominio por HTTP.
Si aun no hay certificado institucional y APK release, habilitar primero la web por
HTTPS y realizar el piloto en un entorno de prueba con cuentas sin privilegios.
No prometer aviso en reposo hasta completar la prueba de campo.

Requisitos en el trabajo: Java 21, servicio existente, MySQL accesible y respaldo
verificado; DNS interno y HTTPS confiable para uso real; acceso Wi-Fi al servidor;
cuentas autorizadas en TAREAS; Nginx ya instalado si se usa proxy. Si falta software,
llevar paquetes y dependencias aprobados para la distribucion/arquitectura Linux.
Un ZIP con el JAR no instala Java ni Nginx.

## 2. Inventario previo y condiciones de parada

Datos historicos del repositorio, a confirmar presencialmente:

- Aplicacion: `/opt/inventario-modular`.
- Unidad: `inventario-modular.service`. NO tocar `inventario.service` del sistema viejo.
- Entorno: `/etc/inventario-modular/inventario-modular.env`.
- ExecStart historico: Java sobre `target/inventario-modular-0.0.1-SNAPSHOT.jar`.
- Usuario/grupo historicos: administrador. Comprobar, no asumir.
- Perfil `local`: MySQL y AD configurable. Perfil `casa`: H2 solo para desarrollo.
- MySQL esperado: `10.15.0.62:3306/inventario_modular`.
- Puerto interno: 8081. Nombre/IP del servidor de aplicacion: confirmar en el trabajo.

```bash
java -version
sudo systemctl show inventario-modular.service \
  -p FragmentPath -p User -p Group -p WorkingDirectory -p ExecStart
sudo systemctl cat inventario-modular.service
sudo systemctl status inventario-modular.service --no-pager
sudo ss -ltnp
timedatectl
df -h /opt
```

Inspeccionar localmente: la unidad podria contener secretos si fue configurada de otra
forma. No pegar su contenido completo en chats. Comprobar hora y zona institucional:
los contadores diarios usan la fecha del servidor.

PARAR si no se conoce la ruta real del JAR, hay cambios locales no comprendidos,
el respaldo falla, MySQL apunta a otra base, falta TLS para credenciales reales o
no hay forma de volver al JAR anterior. No sustituir servicios del inventario viejo.

## 3. Transferencia y preparacion

Transportar el ZIP por el medio interno autorizado, por ejemplo USB o WinSCP.
Descomprimirlo en una carpeta de entrega independiente, no sobre el checkout activo.
Conservar la carpeta completa. Definir ENTREGA con la ruta real; los siguientes
ejemplos suponen que esa carpeta contiene VERSION.txt y SHA256SUMS.

```bash
ENTREGA=/ruta/real/entrega-lan
cd "$ENTREGA"
sha256sum -c SHA256SUMS
cat VERSION.txt
```

Todos los hashes deben ser OK. Los hashes detectan cambios accidentales, no sustituyen
la confianza en quien entrega el paquete. Contrastar el commit con GitLab desde la PC
autorizada que lo preparo. En la LAN aislada no ejecutar git pull ni instalar dependencias.

El bundle permite continuar el codigo sin GitLab. En una copia nueva:

```bash
git clone -b primeros-pasos "$ENTREGA/inventario-modular.bundle" \
  /ruta/de/trabajo/inventario-modular
```

Para actualizar un checkout existente, primero revisar git status y proteger cualquier
cambio propio. No es obligatorio actualizar el checkout para ejecutar el JAR del kit.
Si esta limpio y coincide con la historia entregada:

```bash
cd /opt/inventario-modular
git status --short
git bundle verify "$ENTREGA/inventario-modular.bundle"
git fetch "$ENTREGA/inventario-modular.bundle" \
  refs/heads/primeros-pasos:refs/remotes/entrega/primeros-pasos
git switch primeros-pasos
git merge --ff-only refs/remotes/entrega/primeros-pasos
```

Si el merge no es fast-forward, detenerse y resolver la divergencia en desarrollo.
El bundle contiene historia Git, no solo fuentes: custodiarlo como el repositorio.
Su origen en un clon nuevo sera un archivo local; cambiarlo a GitLab solamente en
una estacion con conectividad y autorizacion, no abrir Internet al servidor por ello.

## 4. Respaldo antes del primer arranque nuevo

Ensayar primero con una copia de MySQL, nunca apuntar pruebas al esquema productivo.
V15 fue probada en H2; el ensayo MySQL es requisito de esta entrega. No restaurar datos
H2 de casa en produccion. Durante el respaldo final, detener solo el servicio modular
y coordinar que no haya otros escritores de esa misma base.

Los comandos siguientes son para una MISMA sesion bash. Sustituir JAR por la ruta
comprobada en ExecStart antes de continuar. Si se pierde la sesion, recuperar la ruta
exacta del respaldo; no generar otra fecha para intentar una reversion.

```bash
set -euo pipefail
JAR=/opt/inventario-modular/target/inventario-modular-0.0.1-SNAPSHOT.jar
test -f "$JAR"
BACKUP="/opt/backups/inventario-modular-$(date +%Y%m%d-%H%M%S)"
sudo install -d -m 700 "$BACKUP"
sudo systemctl stop inventario-modular.service
sudo cp -a "$JAR" "$BACKUP/aplicacion-anterior.jar"
sudo cp -a /etc/inventario-modular/inventario-modular.env \
  "$BACKUP/entorno-anterior.env"
```

Respaldar MySQL con una cuenta autorizada para backup, no necesariamente la de la app.
El comando pide la clave, no la coloca en historial. Sustituir USUARIO_BACKUP por la
cuenta acordada. La redireccion se ejecuta como root y crea el archivo restringido.

```bash
sudo bash -c 'umask 077; mysqldump -h 10.15.0.62 -u USUARIO_BACKUP -p \
  --single-transaction --routines --triggers --events \
  inventario_modular > "$1/base-anterior.sql"' bash "$BACKUP"
sudo test -s "$BACKUP/base-anterior.sql"
```

Exigir salida exitosa y respaldo restaurable; un archivo no vacio por si solo no basta.
Si falla, no continuar el despliegue. Resolver el respaldo o reanudar el servicio viejo
de la aplicacion modular para terminar la ventana sin cambios. No borrar respaldos.

## 5. Entorno, base y publicacion del JAR

Editar el archivo de entorno con `sudoedit`, conservando valores reales existentes.
No copiar passwords desde documentacion ni activar el usuario simulado de casa.
La autenticacion local de cuentas en base es distinta del acceso local simulado.

Configuracion a revisar, no pegar como reemplazo completo del archivo:

```ini
SPRING_PROFILES_ACTIVE=local
INVENTARIO_SERVER_PORT=8081
INVENTARIO_LAN_ONLY=true
INVENTARIO_LOCAL_AUTH_ENABLED=false
INVENTARIO_LOCAL_DB_AUTH_ENABLED=true
INVENTARIO_LDAP_ENABLED=true
INVENTARIO_DB_PRIMARY_URL=jdbc:mysql://10.15.0.62:3306/inventario_modular
INVENTARIO_DB_PRIMARY_USER=inventario_modular_app
```

INVENTARIO_DB_PRIMARY_PASSWORD y parametros LDAP deben conservar los secretos vigentes.
Los alias INVENTARIO_DB_URL/USER/PASSWORD existentes tambien funcionan si no hay valores
PRIMARY que los sobreescriban. LDAP requiere host, dominio, base DN y, para las consultas
de directorio, la cuenta lectora configurada. Confirmar con el administrador del dominio.

El perfil local intenta fallback MySQL cuando falla el principal. No hay interruptor
dedicado de fail-fast. En produccion, para evitar escribir en una base local por error,
configurar INVENTARIO_DB_FALLBACK_URL/USER/PASSWORD con el MISMO destino y credenciales
del principal, o acordar otra politica explicita y probarla. No escribir referencias
como ${OTRA_VARIABLE} dentro del EnvironmentFile: systemd no las expande como un shell.
Si no hay conexion valida, es preferible que el servicio no inicie.

V15 se ejecuta al arrancar por spring.sql.init.mode=always en el perfil local.
Crea dos tablas y una fila de secuencia si faltan. Requiere permisos de creacion y
consulta/escritura acordados con DBA. Flyway esta deshabilitado y Hibernate usa update.
NO activar Flyway: hay versiones V6 duplicadas en el historial. En otro perfil,
revisar su mecanismo de migracion antes de arrancar. Ejecutar V15 manualmente solo
si forma parte del procedimiento aprobado; no ejecutar todas las migraciones historicas.

Con el servicio detenido y respaldado, instalar el JAR validado preservando propietario
y permisos del anterior. ENTREGA, JAR y BACKUP deben seguir definidos y comprobados.

```bash
sudo cp "$ENTREGA/inventario-modular.jar" "${JAR}.nuevo"
sudo chown --reference="$JAR" "${JAR}.nuevo"
sudo chmod --reference="$JAR" "${JAR}.nuevo"
sudo mv "${JAR}.nuevo" "$JAR"
sudo chown root:root /etc/inventario-modular/inventario-modular.env
sudo chmod 600 /etc/inventario-modular/inventario-modular.env
sudo systemctl start inventario-modular.service
sudo systemctl status inventario-modular.service --no-pager
sudo journalctl -u inventario-modular.service -n 120 --no-pager
curl -I http://127.0.0.1:8081/movil/login
```

No hace falta daemon-reload por cambiar solo el EnvironmentFile; si se modifica la
unidad o un override, ejecutar daemon-reload antes de iniciar. Esperar a que termine
el arranque. El log debe indicar conexion al MySQL principal correcto, sin fallback
inesperado ni errores SQL. Con DBA, comprobar tareas_avisos y tareas_aviso_secuencia.
Detener y revertir si el destino de datos o el esquema no son los esperados.

## 6. HTTPS institucional sin afectar otros sistemas

Usar DNS interno estable y certificado emitido por la CA institucional, con ese nombre
en Subject Alternative Name. Instalar la CA publica en los celulares y en el equipo
de prueba; la clave privada del servidor nunca va a telefonos, PDF, Git o APK.
El certificado debe incluir cadena, vigencia y nombre correctos. No usar curl -k ni
desactivar verificacion TLS como solucion productiva.

NO ejecutar automaticamente `scripts/setup-nginx-https.sh`: usa apt-get, genera un
autofirmado sin SAN y puede cambiar el sitio default compartido. La configuracion
historica Nginx contiene IP/nombre de ejemplo; no copiarla sobre un sitio existente.
Inventariar los virtual hosts y reservar un nombre propio, sin afectar inventario viejo.

Ejemplo de un NUEVO virtual host dedicado, a adaptar con el administrador Linux.
Reemplazar tareas.intranet.ejemplo por el nombre interno real y las rutas de certificado.
No activar hasta que Nginx y los certificados ya esten presentes en el servidor.

```nginx
server {
    listen 443 ssl;
    server_name tareas.intranet.ejemplo;
    ssl_certificate /etc/ssl/certs/tareas-cadena.pem;
    ssl_certificate_key /etc/ssl/private/tareas.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Port $server_port;
        proxy_set_header Forwarded "";
    }
}
```

Este ejemplo supone un solo proxy: reemplaza cabeceras recibidas del cliente. Con
otros proxies, definir explicitamente la cadena confiable. No exponer 8081 a clientes
que puedan falsificar cabeceras forwarded. Cuando todo acceso directo y scripts de
inventario ya usen el proxy, establecer SERVER_ADDRESS=127.0.0.1 y
SERVER_SERVLET_SESSION_COOKIE_SECURE=true en el entorno y reiniciar el modular.
Comprobar antes los clientes existentes que usen 8081 para no interrumpirlos.

```bash
sudo nginx -t
sudo systemctl reload nginx
curl --cacert /ruta/CA-institucional.crt \
  -I https://NOMBRE_INTERNO_REAL/movil/login
```

No recargar Nginx si falla la validacion. Limitar 443 a las redes institucionales y
salida a los servicios internos necesarios, sin abrir Internet. No reemplazar reglas
de firewall completas desde este instructivo. Probar que Wi-Fi alcanza DNS/HTTPS;
estar en el mismo segmento no garantiza acceso si hay aislamiento o ACL.

## 7. Instalar Android y validar el circuito

Produccion requiere una APK release firmada. El kit contiene solo piloto debug.
Para un laboratorio autorizado, instalar ese piloto con cuentas de prueba; la APK
acepta HTTP local, pero eso no cifra las credenciales. Preferir HTTPS tambien alli.

Cuando exista la APK autorizada, copiarla a una ruta estable legible por el usuario
del servicio, por ejemplo `/opt/inventario-modular/distribucion/tareas-lan.apk`.
Configurar en el EnvironmentFile y reiniciar el servicio:

```ini
INVENTARIO_MOVIL_APK_PATH=/opt/inventario-modular/distribucion/tareas-lan.apk
```

El enlace de descarga aparece en la web cuando el archivo es legible. No se descarga
anonimamente: requiere login y TAREAS/VER. Tambien puede transferirse por USB/MDM interno.
La APK no esta dentro del JAR ni almacenada en Git. Distribuir solo la version acordada.

1. Confirmar Android 8+ y WebView Chromium 103+. Preparar actualizaciones offline autorizadas si faltan.
2. Instalar la CA publica institucional. Instalar la APK por el mecanismo autorizado.
3. Configurar solo el origen del servidor, por ejemplo https://NOMBRE_INTERNO_REAL,
   sin /movil/tareas. localhost en el telefono es el telefono, no el servidor.
4. Ingresar como tecnico con TAREAS/VER y TAREAS/EDITAR. Activar Avisos y aceptar notificaciones.
5. Ajustar bateria sin restricciones segun fabricante; comprobar volumen, canal y No molestar.
6. Usar Ajustes > Probar sonido. Esperar estado Conectado antes de crear la primera tarea.
7. Desde otra cuenta administradora en PC, crear una tarea libre. Debe aparecer el
   aviso al siguiente ciclo nominal de consulta; registrar demora real, no prometer un plazo fijo.
8. Tocar aviso, tomar tarea, comentar y cerrarla. Verificar responsable y comentario
   en PC y actualizacion del visor. El autor de su propia tarea no recibe sonido.
9. Repetir con pantalla bloqueada 30 minutos, reposo, perdida/reconexion Wi-Fi,
   reinicio del servidor, cierre de sesion y dos tecnicos tomando la misma tarea.

Registrar modelo, Android/WebView, usuario de prueba, hora creacion/recepcion, escenario,
resultado y bateria. El servicio no vuelve solo tras reiniciar el telefono o forzar cierre.
Si una prueba de reposo falla, mantener piloto controlado y no anunciar despliegue general.

## 8. Firma release en una estacion preparada

No es necesario compilar Android en el Linux productivo. Usar una estacion con JDK,
SDK y dependencias previamente preparadas. Desde android/, en Linux:

```bash
sh ./gradlew assembleRelease lintRelease --offline --no-daemon
```

En Windows usar gradlew.bat. --offline requiere que Gradle Wrapper, plugin y todas
las dependencias ya esten en cache; no los incluye el kit. La salida release actual
es unsigned. Firmar con una clave institucional existente y custodiada, nunca con debug.
Ejemplo Linux con Build Tools 35.0.0, desde android/:

```bash
BT="$ANDROID_HOME/build-tools/35.0.0"
"$BT/zipalign" -f -v 4 \
  app/build/outputs/apk/release/app-release-unsigned.apk \
  /ruta/segura/tareas-alineada.apk
"$BT/apksigner" sign --ks /ruta/segura/firma-institucional.jks \
  --out /ruta/segura/tareas-lan-release.apk \
  /ruta/segura/tareas-alineada.apk
"$BT/apksigner" verify --verbose --print-certs \
  /ruta/segura/tareas-lan-release.apk
```

La herramienta pide la clave: no pasarla en linea de comando. Alinear antes de firmar;
no modificar el APK firmado. Registrar hash/certificado firmante y custodiar la clave
para futuras actualizaciones. Incrementar versionCode en cada entrega posterior.
El paquete release y el piloto tienen distinto applicationId; no son la misma app
actualizada y sus sesiones/cursores no se comparten. Desactivar avisos en el piloto
para evitar duplicados cuando se adopte release.

## 9. Aceptacion, problemas y reversion

Aceptar el servidor solo si hay login local/AD real correcto, autorizacion por roles,
creacion/comentarios/toma/cierre, descarga protegida, V15 en la base correcta y HTTPS
sin advertencias. Aceptar la APK solo tras firma y prueba real de fondo. Los contadores
del visor tienen los pendientes descritos en el traspaso: no usarlos aun como reporte
formal de productividad sin corregir la distincion entre cerradas y canceladas.

Diagnostico rapido:

- No conecta: verificar nombre DNS, puerto, Wi-Fi/ACL, listener, certificado y log Linux.
- 401: ingresar de nuevo y activar Avisos. 403: revisar permiso TAREAS y origen de red.
- No suena: probar canal, otra cuenta autora, primera sincronizacion y restricciones de bateria.
- APK no visible/404: revisar ruta configurada, archivo y lectura por el usuario systemd.
- Tabla inexistente: verificar perfil, SQL init, permisos y MySQL seleccionado; no habilitar Flyway a ciegas.
- Visor no cambia: revisar En vivo, formulario con foco o cambios sin guardar, sesion y conexion.

Para revertir binarios, usar la misma ruta BACKUP guardada y JAR verificado:

```bash
sudo systemctl stop inventario-modular.service
sudo cp -a "$BACKUP/aplicacion-anterior.jar" "$JAR"
sudo cp -a "$BACKUP/entorno-anterior.env" \
  /etc/inventario-modular/inventario-modular.env
sudo systemctl start inventario-modular.service
sudo systemctl status inventario-modular.service --no-pager
```

Si se modificaron unidad o Nginx, restaurar sus respaldos verificados con el administrador;
este procedimiento no los modifica automaticamente. Las tablas V15 son aditivas:
dejarlas en la base al volver al JAR anterior. No borrar ni restaurar MySQL a ciegas;
una restauracion elimina operaciones posteriores y requiere coordinacion DBA y ventana
sin escrituras. Si Hibernate altero otra estructura, evaluar compatibilidad antes de volver.

Al finalizar registrar fecha, operador, commit de VERSION.txt, hashes, respaldo usado,
pruebas realizadas y excepciones. Mantener credenciales y datos de produccion fuera de GitLab.
