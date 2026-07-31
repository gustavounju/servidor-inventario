# Guía de Despliegue en Producción — API Contable
## Servidor Ubuntu Server (Poder Judicial) — Conexión vía PuTTY / SSH

**Fecha de ejecución:** Mañana / Despliegue Programado  
**Servidor Objetivo:** Ubuntu Server (`10.15.2.251`)  
**Base de Datos:** MySQL (`inventario_prod`)  
**Rama Git con Cambios:** `feature/contable-external-api`  

---

### 1. Conexión al Servidor Ubuntu (PuTTY)

1. Abre **PuTTY** en tu computadora de trabajo.
2. En **Host Name (or IP address)** ingresa la IP del servidor: `10.15.2.251` (Puerto `22`).
3. Haz clic en **Open** e ingresa tu usuario y contraseña de administrador en Ubuntu.
4. Navega al directorio del proyecto (por defecto `/var/www/servidorinventario` o la carpeta donde está alojado el sistema):
   ```bash
   cd /var/www/servidorinventario
   ```

---

### 2. Descargar Cambios y Cambiar a la Rama

Ejecuta los siguientes comandos en la terminal de Ubuntu para traer la rama que contiene la API contable:

```bash
# 1. Obtener las últimas ramas y commits desde GitLab
git fetch origin

# 2. Cambiar a la rama de la API Contable
git checkout feature/contable-external-api

# 3. Asegurar que esté actualizada al último commit
git pull origin feature/contable-external-api
```

> **Verificación:** Al ejecutar `git status`, verás: `On branch feature/contable-external-api`.

---

### 3. Configurar la Clave Privada en el archivo `.env` de Producción

Debes definir el token secreto que utilizará el sistema contable para autenticarse.

#### Paso A: Generar un Token Seguro (Opcional pero Recomendado)
Puedes generar un token aleatorio seguro ejecutando en la terminal:
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```
*Copia el token generado.*

#### Paso B: Editar el archivo `.env` en Ubuntu
Abre el archivo `.env` con el editor `nano`:
```bash
nano .env
```

Baja al final del archivo y agrega o modifica la variable `CONTABLE_API_TOKEN`:
```ini
# Token dedicado para la API de Integración con el Sistema Contable
CONTABLE_API_TOKEN=pega_aqui_tu_clave_secreta_generada_para_produccion
```

Guarda los cambios en `nano`:
- Presiona `Ctrl + O` y luego `Enter` (para guardar).
- Presiona `Ctrl + X` (para salir de nano).

---

### 4. Actualización de la Base de Datos (`inventario_prod`)

> 💡 **IMPORTANTE — No requiere comandos SQL manuales:**  
> El sistema cuenta con migración automática. Al reiniciar el servicio, Python ejecutará la **Migración V47** y creará automáticamente los índices de rendimiento `idx_comp_oc_number` y `idx_comp_invoice_number` en la tabla `components` de la base de datos `inventario_prod`.

Si deseas ejecutar la migración de base de datos manualmente antes de reiniciar todo, puedes correr:
```bash
python3 database/run_migrations.py
```

---

### 5. Reiniciar los Servicios en Producción

Reinicia el servicio systemd del inventario (Gunicorn / Flask) para que tome el nuevo código y las variables de entorno:

```bash
# Reiniciar el servicio principal
sudo systemctl restart inventario

# Verificar que el servicio esté activo y sin errores (debe decir 'active (running)')
sudo systemctl status inventario
```

*(Si usas Nginx como proxy inverso, opcionalmente puedes recargarlo: `sudo systemctl reload nginx`)*

---

### 6. Verificación de Funcionamiento en Producción (Smoke Test)

Una vez reiniciado, realiza una prueba de conexión directa desde la terminal de Ubuntu usando `curl`:

#### Prueba A: Verificar rechazo sin token (401 Unauthorized)
```bash
curl -i http://localhost:5000/api/external/purchase-orders
```

#### Prueba B: Verificar respuesta con el token de producción (200 OK)
```bash
curl -i -H "Authorization: Bearer TU_TOKEN_PROD" http://localhost:5000/api/external/purchase-orders
```

---

### 7. Datos para Entregar al Sistema Contable

Una vez finalizado el despliegue, entrega al otro programador o equipo contable la siguiente información:

- **Documento PDF de Especificación:** `docs/api_contable_spec.pdf`
- **URL HTTPS Producción:** `https://10.15.2.251:5000`
- **URL HTTP Producción (Fallback):** `http://10.15.2.251:8080`
- **Token de Producción:** *(El valor que configuraste en `CONTABLE_API_TOKEN`)*

---

### 🔄 Resumen de Comandos Rápidos (Copia y Pega para Mañana)

```bash
cd /var/www/servidorinventario
git fetch origin
git checkout feature/contable-external-api
git pull origin feature/contable-external-api
nano .env   # (Agregar CONTABLE_API_TOKEN)
sudo systemctl restart inventario
sudo systemctl status inventario
```
