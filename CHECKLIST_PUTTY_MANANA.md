# Checklist PuTTY - Deploy Automatico

## Primera vez (o si el directorio no existe)

```bash
sudo mkdir -p /opt/inventario
sudo git clone https://gitlab.com/gustavoeliasm/servidorinventario.git /opt/inventario
cd /opt/inventario
git checkout feature/migration-mysql
bash deploy_ubuntu.sh
```

## Actualizacion normal (ya existe /opt/inventario)

```bash
cd /opt/inventario
bash deploy_ubuntu.sh
```

El script hace **todo solo**:
- git pull
- instala dependencias
- genera/actualiza el `.env` con los valores conocidos
- solo pide **usuario y clave MySQL** si no están en el `.env`
- copia configs de systemd y nginx
- reinicia los servicios
- muestra el estado y logs al final

## Valores ya configurados en el script

| Variable | Valor |
|---|---|
| DB_HOST | 10.15.3.20 |
| DB_PORT | 3306 |
| DB_NAME | inventario_prod |
| INVENTARIO URL HTTPS | https://10.15.2.251:5000 |
| INVENTARIO URL HTTP | http://10.15.2.251:8080 |

## Solo te preguntara

- `Usuario MySQL` (ej: root)
- `Clave MySQL`

(Solo si no están ya en el `.env`)

## Primer login

- Usuario: `administrador` / Clave: `tdg729tdg`
- Ir a `Usuarios` → crear tu superusuario → cerrar sesion → entrar con el tuyo → borrar `administrador`
