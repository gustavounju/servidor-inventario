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

Todas las peticiones deben incluir la cabecera HTTP `Authorization` con el esquema `Bearer`:

```http
Authorization: Bearer <TOKEN_PRIVADO_CONTABLE>
```

- Las peticiones sin token o con token incorrecto recibirán una respuesta `401 Unauthorized`.
- El token es exclusivo para esta integración y se configura en las variables de entorno del servidor.
- La API cuenta con limitador de tasa de peticiones (Rate Limit: 60 peticiones/minuto).

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
