# Sistema de Inventario - Centro Judicial San Pedro

Sistema de inventario interno para el Departamento de Informática del Centro Judicial (San Pedro, Jujuy). Permite gestionar PCs, racks, switches, impresoras, stock y registrar las tareas técnicas.

> **ℹ️ Nota importante para desarrolladores:**  
> Este `README.md` es un resumen rápido. La verdadera fuente de verdad con la arquitectura, el modelo de roles, variables de entorno y problemas conocidos está en el archivo **[`CONTEXT.md`](./CONTEXT.md)**. Revísalo antes de tocar código.

## 🚀 Características Principales

*   **Dashboard**: Estadísticas generales del parque informático.
*   **Infraestructura**: Gestión visual y detallada de equipos, racks y red.
*   **Gestión de Tareas**: Registro y seguimiento de intervenciones técnicas con soporte móvil.
*   **Stock**: Inventario general de piezas y repuestos.
*   **IA & OCR**: Asistente con IA (Gemini) y procesamiento de documentos por OCR.

## 🛠️ Stack Técnico

*   **Backend:** Python 3.13, Flask, MySQL
*   **Frontend:** HTML, CSS (Vanilla / `gold.css`), JS
*   **Despliegue:** Ubuntu + Systemd + Nginx + Gunicorn (en Producción)

## 💻 Entorno de Desarrollo (Windows)

1.  **Clonar el repositorio:**
    ```bash
    git clone https://gitlab.com/gustavoeliasm/servidorinventario.git
    cd servidorinventario
    ```
2.  **Entorno virtual y dependencias:**
    ```bash
    python -m venv .venv
    .\.venv\Scripts\activate
    pip install -r requirements.txt
    ```
3.  **Configurar `.env`:**
    *   Copia `.env.example` a `.env`.
    *   Completa los datos de conexión a tu base de datos MySQL local (`inventario_dev`).
4.  **Ejecutar el servidor local:**
    ```bash
    .\ejecutar_inventario.bat
    # O directamente: python servidor.py
    ```
5.  Acceder a la aplicación en [http://127.0.0.1:5000](http://127.0.0.1:5000)

## ⚙️ Despliegue en Producción

El servidor de producción corre en Ubuntu. **No utilizamos CI/CD automático**. El despliegue se hace manualmente a través de SSH ejecutando un pull y un script de actualización.

Para instrucciones detalladas paso a paso sobre cómo desplegar de manera segura, debes utilizar el skill `/deploy` (revisar el runbook en `.agents/skills/deploy/SKILL.md`).

---
*Centro Judicial San Pedro, Jujuy - Departamento de Informática*
