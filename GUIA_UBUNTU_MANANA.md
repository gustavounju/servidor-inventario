# Guia Ubuntu Manana

Esta guia esta pensada para tu flujo real:

- Desarrollas en Windows.
- Subes cambios a GitLab.
- En el trabajo entras por PuTTY al Ubuntu Server.
- El sistema vive en `/opt/inventario/`.
- El objetivo desde manana es dejar produccion en `Gunicorn + Nginx + systemd`.

## 1. Antes de salir de tu casa

En Windows:

1. Confirma que el codigo nuevo ya esta en GitLab.
2. Lleva anotado que ahora el sistema crea el usuario inicial automaticamente si la tabla `app_users` esta vacia.
3. Credencial inicial del sistema:
   - Usuario: `administrador`
   - Clave: `tdg729tdg`

Notas:

- Ese usuario inicial se crea solo si no existe ningun usuario en `app_users`.
- La idea correcta es entrar una primera vez, crear tu propio superusuario y luego borrar `administrador`.
- Si algun dia borras todos los usuarios del sistema, al reiniciar volvera a crearse el usuario inicial para evitar quedarte afuera.

## 2. Entrar al servidor por PuTTY

Conectate al Ubuntu y ejecuta:

```bash
cd /opt/inventario
git status
git pull
```

Si `git pull` trae cambios de Python o templates, sigue con los pasos de abajo.

## 3. Revisar variables importantes

Verifica el archivo `.env` del servidor.

Minimo recomendado:

```env
FLASK_SECRET_KEY=pon_aqui_una_clave_larga_y_privada
DB_HOST=10.15.3.20
DB_PORT=3306
DB_USER=tu_usuario_mysql
DB_PASS=tu_clave_mysql
DB_NAME=tu_base_mysql

# URL publica del servidor Inventario para las PCs cliente.
# No debe confundirse con DB_HOST.
INVENTARIO_PUBLIC_BASE_URL=https://10.15.2.251:5000
INVENTARIO_PUBLIC_HTTP_FALLBACK_URL=http://10.15.2.251:8080

# Autenticación Inicial
AUTH_MODE=local
BOOTSTRAP_ADMIN_USERNAME=administrador
BOOTSTRAP_ADMIN_PASSWORD=[OCULTA]
INVENTARIO_API_TOKEN=[OCULTA]

# Dejalo en false si todavia entras por HTTP interno.
# Cuando consolides HTTPS con Nginx, cambialo a true.
SESSION_COOKIE_SECURE=false
```

Si el `.env` no existe o esta incompleto, editalo antes de reiniciar.

Importante:

- `DB_HOST` es la IP del servidor MySQL.
- `INVENTARIO_PUBLIC_BASE_URL` es la IP o URL del servidor Inventario al que reportan las PCs.
- Pueden ser maquinas distintas sin problema.

## 4. Instalar dependencias nuevas

Esta version agrega soporte para:

- `gunicorn`
- `ldap3` para Active Directory futuro

En Ubuntu ejecuta:

```bash
cd /opt/inventario
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Si ya quieres dejar Gunicorn + Nginx mañana

### A. Service

```bash
sudo cp /opt/inventario/deployment/inventario.service /etc/systemd/system/inventario.service
sudo systemctl daemon-reload
sudo systemctl enable inventario
```

### B. Nginx

```bash
sudo cp /opt/inventario/deployment/nginx_inventario.conf /etc/nginx/sites-available/inventario
sudo ln -sf /etc/nginx/sites-available/inventario /etc/nginx/sites-enabled/inventario
sudo nginx -t
sudo systemctl restart nginx
```

### C. Reiniciar app

```bash
sudo systemctl restart inventario
sudo systemctl status inventario
sudo journalctl -u inventario -n 100 --no-pager
```

## 6. Que tiene que pasar solo

Al arrancar, el sistema ahora hace esto solo:

1. inicializa MySQL
2. ejecuta migraciones
3. crea la tabla `app_users` si no existe
4. crea el usuario inicial `administrador / [OCULTA]` solo si no hay usuarios cargados

No deberias correr SQL manual para esta parte.

## 7. Primer ingreso manana

Desde tu PC Windows del trabajo:

1. **Conectate a la VPN** (WireGuard) para estar en la red judicial (10.15.x.x)
2. **Abri CMD/PowerShell** (no hace falta PuTTY si usas terminal moderna) y corre:
   ```bash
   ssh administrador@10.15.3.20
   ```
   - Usuario: `administrador`
   - Clave: `[OCULTA]`
3. abre el modal `Usuarios`
4. en la parte `Usuarios del sistema`, crea tu usuario propio marcandolo como `Superusuario`
5. cierra sesion
6. vuelve a entrar con tu nuevo usuario
7. elimina el usuario `administrador`

Eso deja el sistema bajo tu propia cuenta y no dependes mas del usuario bootstrap.

## 8. Si algo falla

### A. El servicio no levanta

Corre:

```bash
sudo journalctl -u inventario -n 200 --no-pager
```

Busca errores de:

- conexion MySQL
- modulo faltante
- error de sintaxis
- variables `.env`

### B. El login no acepta credenciales

Posibles causas:

- la app no reinicio realmente
- la base no tiene creada la tabla `app_users`
- el arranque fallo antes de `ensure_default_admin()`

Chequeo rapido en MySQL:

```sql
SELECT id, username, is_superuser, is_active, must_change_password FROM app_users;
```

Si no aparece `administrador`, revisa logs del servicio.

### C. Quedaste sin usuarios

Si `app_users` queda vacia, reinicia el servicio:

```bash
sudo systemctl restart inventario
```

El usuario bootstrap deberia recrearse solo.

### D. El dictado de voz por IA falla

Si al grabar un audio en la versión móvil salta un mensaje de "Error IA":

1. **Error de permisos (`[Errno 13] Permission denied`)**:
   El servidor no tiene permiso para guardar el archivo de audio. Ejecuta en el servidor:
   ```bash
   cd /opt/inventario
   sudo mkdir -p uploads
   sudo chmod -R 777 uploads
   ```

2. **Error de módulo faltante (`No module named 'groq'`)**:
   El servidor tiene la configuración de Python apuntando a `.venv` (con punto). Asegúrate de instalar la dependencia en esa carpeta exactamente:
   ```bash
   cd /opt/inventario
   sudo /opt/inventario/.venv/bin/pip install groq python-dotenv
   sudo systemctl restart inventario
   ```

## 9. Flujo diario recomendado

Todos los dias en el trabajo:

```bash
cd /opt/inventario
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart inventario
sudo systemctl status inventario
```

Si hubo cambios grandes:

```bash
sudo journalctl -u inventario -n 100 --no-pager
```

## 10. Active Directory futuro

El sistema ya quedo preparado para esto, pero no activado.

Cuando tu administrador de red te habilite AD, en `.env` podras usar algo asi:

```env
AUTH_MODE=hybrid
AD_SERVER=ldap://tu-servidor-ad
AD_DOMAIN=JUSTICIAJUJUY
AD_BASE_DN=DC=justiciajujuy,DC=gov,DC=ar
AD_USE_SSL=false
AD_CONNECT_TIMEOUT=5
AD_SUPERUSERS=tuusuario
```

Mi recomendacion para ese momento:

1. arrancar con `AUTH_MODE=hybrid`
2. probar tu login AD sin borrar usuarios locales
3. dejar un superusuario local de emergencia siempre
