# Integración Sistema Inventario → Sistema Contable
## Especificación Técnica de API — Consulta de Órdenes de Compra y Remitos

**Versión de API:** 1.0  
**Formato de Intercambio:** JSON (UTF-8)  
**Protocolo / Transporte:** HTTP / HTTPS  
**Autenticación:** Token Bearer (`Authorization: Bearer <token>`)  

---

### 1. Modelo de Datos Disponible en Inventario

El sistema de inventario almacena el detalle de componentes físicos recibidos en stock. Cada unidad física registrada guarda los siguientes campos relevantes para contabilidad:

| Campo | Tipo | Descripción | Ejemplo |
| :--- | :--- | :--- | :--- |
| `oc_number` | String | Número de Orden de Compra | `OC-2026-0451` |
| `invoice_number` | String | Número de Remito de entrega | `REM-00871` |
| `supplier` | String | Nombre / Razón Social del Proveedor | `Insumos SRL` |
| `component_type` | String | Categoría del producto | `Monitor`, `CPU`, `Teclado` |
| `brand_model` | String | Marca y modelo del producto | `Dell P2422H` |
| `serial_number` | String | Número de serie físico de la unidad | `ZA12606000514` |
| `created_at` | DateTime | Fecha y hora de recepción/carga | `2026-07-15 10:32:00` |

> ⚠️ **Nota aclaratoria de alcance:**  
> 1. **Sin Precios / Montos:** El sistema de inventario no registra importes monetarios ni valores unitarios. La gestión de precios queda a cargo del Sistema Contable.  
> 2. **Remitos Parciales:** Una misma Orden de Compra puede incluir múltiples remitos si las entregas del proveedor fueron fraccionadas en el tiempo.

---

### 2. Autenticación y Seguridad

Todas las peticiones deben incluir la cabecera HTTP `Authorization` utilizando el esquema `Bearer`:

```http
Authorization: Bearer <TOKEN_PRIVADO_CONTABLE>
```

#### ¿Cómo funciona este mecanismo de seguridad?
- **Cabecera `Authorization`:** Es el campo estándar HTTP que usa la aplicación cliente (ej. Postman o el Sistema Contable) para identificarse ante el servidor en cada consulta.
- **Esquema `Bearer`:** Significa *"Token al portador"* (quien posee la clave tiene la autorización). Es el estándar de la industria (RFC 6750) para proteger APIs REST de forma limpia sin usar contraseñas ni sesiones de usuario.
- **`CONTABLE_API_TOKEN`:** Es la **llave privada secreta**. En el servidor de inventario se configura en el archivo `.env`. Cuando llega una petición, el servidor valida de forma segura si la clave presentada en la cabecera coincide exactamente con la guardada. Si no coincide o falta, el servidor rechaza el acceso con un código **`401 Unauthorized`**.
- **Limitación de Tasa (Rate Limit):** La API limita las peticiones a un máximo de 60 por minuto para proteger la disponibilidad del servidor de inventario.

---

### 3. Endpoints de la API

#### 3.1. Consultar Orden de Compra por Número

Recupera todos los remitos, productos agrupados por modelo, cantidad total recibida y números de serie físicos pertenecientes a una Orden de Compra.

- **Método:** `GET`
- **Ruta:** `/api/external/purchase-orders/{oc_number}`

##### Ejemplo de Solicitud:
```http
GET /api/external/purchase-orders/OC-2026-0451 HTTP/1.1
Host: inventario.pjju.gob.ar
Authorization: Bearer test-contable-secret-token-2026
```

##### Ejemplo de Respuesta (200 OK):
```json
{
  "status": "success",
  "oc_number": "OC-2026-0451",
  "total_items": 24,
  "total_remitos": 1,
  "remitos": [
    {
      "invoice_number": "REM-00871",
      "supplier": "Insumos SRL",
      "received_at": "2026-07-15",
      "items": [
        {
          "component_type": "Monitor",
          "brand_model": "Dell P2422H",
          "quantity": 12,
          "serials": [
            "ZA12606000514",
            "ZA12606000515"
          ]
        },
        {
          "component_type": "Teclado",
          "brand_model": "Logitech K120",
          "quantity": 12,
          "serials": [
            "LOGK120-001",
            "LOGK120-002"
          ]
        }
      ]
    }
  ]
}
```

##### Respuesta cuando la OC no existe (404 Not Found):
```json
{
  "status": "error",
  "message": "Orden de compra 'OC-2026-0451' no encontrada en el inventario"
}
```

---

#### 3.2. Listar / Barrido de Órdenes de Compra (Con Filtros por Fecha)

Permite obtener un listado paginado de Órdenes de Compra registradas en el inventario. Ideal para conciliaciones periódicas o barridos mensuales del sistema contable.

- **Método:** `GET`
- **Ruta:** `/api/external/purchase-orders`
- **Parámetros Query (opcionales):**
  - `since`: Fecha inicio en formato `YYYY-MM-DD` (ej. `2026-07-01`).
  - `until`: Fecha fin en formato `YYYY-MM-DD` (ej. `2026-07-31`).
  - `page`: Número de página (por defecto `1`).
  - `per_page`: Cantidad de resultados por página (por defecto `50`, máximo `200`).

##### Ejemplo de Solicitud:
```http
GET /api/external/purchase-orders?since=2026-07-01&until=2026-07-31&page=1&per_page=50 HTTP/1.1
Host: inventario.pjju.gob.ar
Authorization: Bearer test-contable-secret-token-2026
```

##### Ejemplo de Respuesta (200 OK):
```json
{
  "status": "success",
  "page": 1,
  "per_page": 50,
  "total_purchase_orders": 3,
  "total_pages": 1,
  "purchase_orders": [
    {
      "oc_number": "OC-2026-0451",
      "last_received_at": "2026-07-15",
      "total_items": 24,
      "remitos_count": 1
    },
    {
      "oc_number": "OC-2026-0440",
      "last_received_at": "2026-07-10",
      "total_items": 10,
      "remitos_count": 2
    }
  ]
}
```

---

#### 3.3. Consultar Remito Específico por Número

Permite al sistema contable consultar los ítems correspondientes a un número de remito en particular.

- **Método:** `GET`
- **Ruta:** `/api/external/remitos/{invoice_number}`

##### Ejemplo de Solicitud:
```http
GET /api/external/remitos/REM-00871 HTTP/1.1
Host: inventario.pjju.gob.ar
Authorization: Bearer test-contable-secret-token-2026
```

##### Ejemplo de Respuesta (200 OK):
```json
{
  "status": "success",
  "invoice_number": "REM-00871",
  "oc_number": "OC-2026-0451",
  "supplier": "Insumos SRL",
  "received_at": "2026-07-15",
  "total_items": 24,
  "items": [
    {
      "component_type": "Monitor",
      "brand_model": "Dell P2422H",
      "quantity": 12,
      "serials": ["ZA12606000514", "ZA12606000515"]
    }
  ]
}
```

---

### 4. Resumen de Respuestas HTTP

| Código HTTP | Descripción |
| :--- | :--- |
| **`200 OK`** | Consulta exitosa, retorna datos en formato JSON. |
| **`400 Bad Request`** | Parámetros obligatorios faltantes o formato de fecha inválido. |
| **`401 Unauthorized`** | Token de autorización no provisto o inválido. |
| **`404 Not Found`** | Orden de compra o remito no encontrado. |
| **`429 Too Many Requests`** | Se excedió el límite de peticiones (máx 60 por minuto). |
| **`500 Internal Server Error`** | Error interno no controlado en el servidor. |

---

### 5. Guía de Pruebas con Postman (Servidor de Trabajo)

Para realizar pruebas directamente desde la red de trabajo conectándose al servidor de producción:

- **Base URL HTTPS (Puerto 5000):** `https://10.15.2.251:5000`
- **Base URL HTTP (Puerto 8080 - Fallback):** `http://10.15.2.251:8080`

> ⚠️ **Configuración SSL Requerida en Postman:**  
> Al conectarse a la IP `https://10.15.2.251:5000` utilizando certificado de red interna / autofirmado, se debe desactivar la verificación de certificado SSL en Postman:  
> 1. En Postman, abra **Settings** (ícono de engranaje ⚙️ en la esquina superior derecha).  
> 2. En la pestaña **General**, cambie la opción **SSL certificate verification** a **OFF**.  

#### Pasos para ejecutar la prueba:

1. **Crear una nueva Petición (Request):**
   - Establezca el método HTTP en **`GET`**.

2. **Ingresar la URL del Endpoint:**
   - **Consulta de OC:** `https://10.15.2.251:5000/api/external/purchase-orders/OC-2026-0451`
   - **Listado / Barrido:** `https://10.15.2.251:5000/api/external/purchase-orders?since=2026-07-01&until=2026-07-31`
   - **Consulta de Remito:** `https://10.15.2.251:5000/api/external/remitos/REM-00871`

3. **Configurar la Autenticación:**
   - Diríjase a la pestaña **Authorization**.
   - En el menú desplegable **Type**, seleccione **`Bearer Token`**.
   - En el campo **Token**, ingrese la clave privada (`CONTABLE_API_TOKEN`).

4. **Enviar la Petición:**
   - Haga clic en el botón **Send**.
   - Verifique que la respuesta retorne código **`200 OK`** con los datos estructurados en formato JSON.

