# 📌 Plan de Trabajo: Gestión de Combos/Puestos Completos, QR Par (CPU+Monitor) y Reemplazo por Falla

Este documento define la especificación completa del nuevo módulo de **Gestión de Puestos Completos, Etiquetado QR Doble y Reemplazo por Falla** para el Sistema de Inventario del Centro Judicial (San Pedro, Jujuy).

---

## 🎯 Contexto y Objetivos

1. **Recepción e Ingreso de Stock (Se Mantiene 100% Intacto)**:
   - La carga masiva de remitos componente por componente (con escáner móvil en vivo, Auto ID individual/vacíos y pegado por bloque) **permanece como el primer paso del ciclo de vida**.
   - Los insumos se guardan individualmente en la base de datos en estado `Stock`.

2. **Nuevo Módulo: Armado y Entrega de Puesto Completo / Combo (1-Clic)**:
   - Herramienta para cuando el equipo de informática arma un puesto de trabajo para llevar a un juzgado/oficina.
   - Permite vincular en 1 sola pantalla:
     - 🖥️ **CPU / Gabinete** (Buscando ítem en Stock o escaneando)
     - 📺 **Monitor** (Buscando ítem en Stock o escaneando)
     - ⌨️ **Teclado** (Buscando ítem en Stock o escaneando)
     - 🖱️ **Mouse** (Buscando ítem en Stock o escaneando)
     - 🖨️ **Impresora / Periférico Extra** (Opcional)
   - Permite agregar un componente nuevo que no estuviera previamente cargado en Stock mediante el botón `+ Cargar Nuevo Ítem`.
   - Al confirmar, asigna todos los componentes a la PC, Usuario y Fuero simultáneamente.

3. **Etiquetas QR Dobles (Gabinete + Monitor)**:
   - Al finalizar el armado, el sistema genera **dos stickers QR idénticos**: uno para el gabinete de la CPU y otro para la parte posterior del Monitor.
   - **QR Dinámico 100% en Vivo**: El sticker se imprime **una sola vez**. Contiene el enlace permanente a la ficha de la PC (`/pc/<pc_name>`).
   - Al escanear el QR del Monitor, muestra a qué CPU, Usuario y Fuero pertenece ese monitor.
   - Al escanear el QR de la CPU, muestra la lista completa de periféricos (monitor S/N, teclado S/N, etc.) que deben estar en esa mesa.

4. **Flujo de Reemplazo por Falla (Sustitución Directa de Repuesto)**:
   - Escenario: Se quema un disco rígido o falla un monitor en una PC de la red.
   - Botón directo **`⚡ Sustituir por Falla`** en la ficha del equipo o componente:
     - Marca el componente averiado como **`Retirado`** especificando el motivo (*"Disco quemado / Falla técnica - Scrap"*).
     - Permite seleccionar el nuevo repuesto del Stock.
     - Asigna el nuevo componente a la PC en 1 solo paso.
     - Como el QR es dinámico, el sticker del gabinete/monitor no necesita reimprimirse; al escanearlo reflejará automáticamente el nuevo número de serie.

---

## 📐 Especificación Técnica de Implementación

### Backend (`blueprints/bp_stock.py` y `blueprints/bp_pc.py`)
- `POST /api/components/assign_bundle`: Endpoint para recibir el arreglo de números de serie (`cpu_serial`, `monitor_serial`, `keyboard_serial`, `mouse_serial`, `printer_serial`), el `pc_name`, `assigned_user` y `assigned_fuero`.
- `POST /api/components/swap_failing_component`: Endpoint atómico que recibe `old_serial`, `new_serial`, `retire_reason` y `pc_name`.
- `GET /pc/<pc_name>/qr_label`: Endpoint que renderiza la plantilla de impresión de doble etiqueta QR (Gabinete + Monitor) optimizada para impresoras térmicas de etiquetas o papel A4.

### Frontend (`templates/stock.html` y `templates/pc_detail.html`)
- Modal `assignBundleModal` en `templates/stock.html` con selectores/buscadores de componentes en Stock e integración con el escáner móvil en vivo.
- Botón **"Imprimir Par de QR (CPU + Monitor)"** en la vista de detalle de PC.
- Botón **"Sustituir por Falla"** junto a cada componente instalado.

---

## 🚀 Cómo invocar este plan mañana en tu trabajo:

Cuando inicies sesión mañana con la IA (Antigravity / Gemini CLI), simplemente puedes decir:

> **"Hola, continuemos con el plan definido en `PLAN_GESTION_PUESTOS_Y_REEMPLAZOS.md`."**

Y el agente leerá este archivo automáticamente y sabrá exactamente qué hacer paso por paso.
