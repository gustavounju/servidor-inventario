# Despliegue Ubuntu 24.04

Esta version queda preparada para tu flujo real:

- Desarrollo en Windows 10.
- Codigo en GitLab.
- Actualizacion en Ubuntu por PuTTY con `git pull`.
- Codigo en `/opt/inventario`.
- Produccion con `Gunicorn + Nginx + systemd`.

## 1. Paquetes del servidor

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx mysql-client
```

## 2. Usuario y directorio

Si `/opt/inventario` ya existe, usa el que ya tienes. Si no:

```bash
sudo mkdir -p /opt/inventario
sudo chown -R $USER:www-data /opt/inventario
sudo chmod -R 775 /opt/inventario
```

## 3. Obtener el codigo desde GitLab

Si ya tienes repo clonado:

```bash
cd /opt/inventario
git pull
```

Si es la primera vez:

```bash
git clone <URL_DE_TU_REPO_GITLAB> /opt/inventario
cd /opt/inventario
```

## 4. Entorno virtual e instalacion

```bash
cd /opt/inventario
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## 5. Archivo .env

Crea `/opt/inventario/.env` usando `.env.example` como base:

```bash
cp .env.example .env
nano .env
```

Valores minimos recomendados:

```env
FLASK_SECRET_KEY=pon_una_clave_larga_y_privada

DB_HOST=10.15.3.20
DB_PORT=3306
DB_USER=tu_usuario_mysql
DB_PASS=tu_clave_mysql
DB_NAME=tu_base_mysql

SESSION_COOKIE_SECURE=false

# URL publica a la que apuntan las PCs cliente.
# Esto es el servidor Inventario, NO el MySQL.
INVENTARIO_PUBLIC_BASE_URL=https://10.15.2.251:5000
INVENTARIO_PUBLIC_HTTP_FALLBACK_URL=http://10.15.2.251:8080

BOOTSTRAP_ADMIN_USERNAME=administrador
BOOTSTRAP_ADMIN_PASSWORD=tdg729tdg

AUTH_MODE=local

AD_SERVER=
AD_DOMAIN=
AD_BASE_DN=
AD_USE_SSL=false
AD_CONNECT_TIMEOUT=5
AD_SUPERUSERS=
```

Notas:

- Mientras sigas entrando por HTTP interno o configuracion mixta, deja `SESSION_COOKIE_SECURE=false`.
- Cuando Nginx/HTTPS ya quede firme, cambialo a `true`.
- `AUTH_MODE=local` es el modo actual recomendado.
- Mas adelante puedes usar `AUTH_MODE=hybrid` o `AUTH_MODE=ad` para Active Directory.
- `DB_HOST` puede ser otra IP completamente distinta al servidor web.
- `INVENTARIO_PUBLIC_BASE_URL` define a donde enviaran datos las PCs cliente.

## 6. Probar localmente Gunicorn

Antes de tocar systemd:

```bash
cd /opt/inventario
source .venv/bin/activate
gunicorn --workers 3 --bind 127.0.0.1:5001 servidor:app
```

Si arranca bien, corta con `Ctrl+C`.

## 7. Configurar systemd

Instala el archivo de servicio:

```bash
sudo cp deployment/inventario.service /etc/systemd/system/inventario.service
sudo systemctl daemon-reload
sudo systemctl enable inventario
sudo systemctl restart inventario
sudo systemctl status inventario
```

## 8. Configurar Nginx

Instala la configuracion:

```bash
sudo cp deployment/nginx_inventario.conf /etc/nginx/sites-available/inventario
sudo ln -sf /etc/nginx/sites-available/inventario /etc/nginx/sites-enabled/inventario
sudo nginx -t
sudo systemctl restart nginx
```

Si usas `ufw`:

```bash
sudo ufw allow 5000/tcp
sudo ufw allow 8080/tcp
```

## 9. Primer ingreso

Al primer arranque, si la tabla `app_users` esta vacia, se crea automaticamente:

- usuario: `administrador`
- clave: `tdg729tdg`

Luego entra al sistema y haz esto:

1. ir al modal `Usuarios`
2. crear tu propio superusuario
3. cerrar sesion
4. volver a entrar con tu cuenta propia
5. borrar `administrador`

Ese usuario bootstrap solo reaparece si algun dia la tabla `app_users` queda completamente vacia.

## 10. Preparado para Active Directory

Todavia no queda activado por defecto, pero el sistema ya soporta el camino futuro.

Modos posibles:

- `AUTH_MODE=local`: solo usuarios locales de la tabla `app_users`
- `AUTH_MODE=hybrid`: primero local y luego Active Directory
- `AUTH_MODE=ad`: solo Active Directory

Variables previstas para AD:

```env
AUTH_MODE=hybrid
AD_SERVER=ldap://tu-controlador-o-ip
AD_DOMAIN=JUSTICIAJUJUY
AD_BASE_DN=DC=justiciajujuy,DC=gov,DC=ar
AD_USE_SSL=false
AD_CONNECT_TIMEOUT=5
AD_SUPERUSERS=tuusuario,otroadmin
```

Comportamiento previsto:

- si el usuario autentica contra AD, entra al sistema
- se crea o actualiza un registro local sombra en `app_users`
- el rol superusuario se decide con `AD_SUPERUSERS`
- puedes seguir conservando un usuario local de emergencia

## 11. Flujo diario de actualizacion

```bash
cd /opt/inventario
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart inventario
sudo systemctl status inventario
```

Revisa logs si algo falla:

```bash
sudo journalctl -u inventario -n 100 --no-pager
sudo journalctl -u inventario -f
```

## 12. Checks rapidos

App:

```bash
curl http://127.0.0.1:5001/health
```

Nginx:

```bash
curl http://127.0.0.1:8080/health
```

## 13. Siguiente paso natural

Cuando tu admin de red te habilite AD real, solo habra que:

1. cargar variables `AD_*` en `.env`
2. poner `AUTH_MODE=hybrid`
3. reiniciar `inventario`
4. probar con tu usuario de Active Directory
