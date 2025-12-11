# Guía de Despliegue en Ubuntu 24.04 (IP: 10.15.2.251)

Sigue estos pasos para poner en marcha el servidor de inventario en tu nuevo Linux.

## 1. Preparar el directorio en el servidor

Conéctate por SSH a tu servidor y ejecuta:

```bash
# Crear carpeta
sudo mkdir -p /opt/inventario

# Instalar Python y Pip si no están
sudo apt update
sudo apt install -y python3 python3-pip
```

## 2. Copiar archivos

Copia **todo el contenido** de esta carpeta (`ServidorInventario`) a la carpeta `/opt/inventario` en el servidor.
Puedes usar SCP, WinSCP o FileZilla. Aquí tienes los pasos para **FileZilla**:

### Guía Rápida FileZilla:
1.  **Abrir FileZilla**: Ve a *Archivo* > *Gestor de Sitios*.
2.  **Nuevo Sitio**: Crea uno llamado "Servidor Ubuntu".
3.  **Configuración**:
    *   **Protocolo**: SFTP - SSH File Transfer Protocol
    *   **Servidor**: `10.15.2.251`
    *   **Usuario**: `root` (o el usuario que hayas configurado en la instalación)
    *   **Contraseña**: Tu contraseña de root/usuario.
4.  **Conectar**: Acepta la clave del servidor si es la primera vez.
5.  **Navegar**:
    *   En la derecha (Sitio remoto), sube de nivel hasta llegar a la raíz `/` y luego entra en `opt`. Si no existe la carpeta `inventario`, clic derecho -> *Crear directorio* -> `inventario`. Entra en ella.
    *   En la izquierda (Sitio local), navega a tu carpeta `Desktop/ServidorInventario`.
6.  **Transferir**: Selecciona **todos** los archivos de la izquierda y arrástralos a la derecha.


Asegúrate de que la estructura quede así:
- `/opt/inventario/servidor.py`
- `/opt/inventario/requirements.txt`
- `/opt/inventario/templates/` ...

## 3. Instalar dependencias

En el servidor, ejecuta:

```bash
cd /opt/inventario
# Instalar librerías necesarias
pip3 install -r requirements.txt --break-system-packages
```
*(Nota: En Ubuntu 24.04, pip puede pedir `--break-system-packages` si no usas entorno virtual. Para este uso interno es aceptable).*

## 4. Configurar el servicio (arranque automático)

Copia el archivo `inventario.service` al sistema:

```bash
sudo cp /opt/inventario/inventario.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable inventario
sudo systemctl start inventario
```

## 5. Verificar y abrir Firewall

Verifica que esté corriendo:
```bash
sudo systemctl status inventario
```

Si tienes activado el firewall (ufw), permite el puerto 5000:
```bash
sudo ufw allow 5000
```

## 6. Probar

Desde tu navegador ingresa a:
`http://10.15.2.251:5000`

¡Y listo! El script `inventario.ps1` ya fue actualizado para apuntar a esta IP.
