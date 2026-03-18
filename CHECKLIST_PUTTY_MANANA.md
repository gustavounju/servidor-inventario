# Checklist PuTTY Manana

## Si ya existe `/opt/inventario`

```bash
cd /opt/inventario
git pull
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
nano .env
sudo cp deployment/inventario.service /etc/systemd/system/inventario.service
sudo cp deployment/nginx_inventario.conf /etc/nginx/sites-available/inventario
sudo ln -sf /etc/nginx/sites-available/inventario /etc/nginx/sites-enabled/inventario
sudo systemctl daemon-reload
sudo nginx -t
sudo systemctl restart inventario
sudo systemctl restart nginx
sudo systemctl status inventario --no-pager
sudo journalctl -u inventario -n 80 --no-pager
```

## Variables clave en `.env`

- `DB_HOST` = IP del servidor MySQL
- `INVENTARIO_PUBLIC_BASE_URL` = URL/IP del servidor Inventario para las PCs
- `INVENTARIO_PUBLIC_HTTP_FALLBACK_URL` = fallback HTTP para equipos legacy

No tienen que ser la misma maquina.

## Primer login

- Usuario: `administrador`
- Clave: `tdg729tdg`
- Ir a `Usuarios`
- Crear tu superusuario
- Cerrar sesion
- Entrar con tu usuario
- Borrar `administrador`

## Si luego quieres AD

- Editar `.env`
- Poner `AUTH_MODE=hybrid`
- Completar `AD_SERVER`, `AD_DOMAIN`, `AD_BASE_DN`, `AD_SUPERUSERS`
- `sudo systemctl restart inventario`
