# Arquitectura Visual: Modern Card-Based Admin Shell

La arquitectura visual implementada en el sistema `inventario-modular` se puede denominar **"Modern Card-Based Admin Shell"** (Interfaz Administrativa Moderna Basada en Tarjetas) o **"Clean Enterprise Panel Architecture"**.

## Principios de Diseño
Esta arquitectura está diseñada para sistemas empresariales que requieren claridad, rapidez y un enfoque centrado en los datos.

### 1. Colores y Esquema (Soft Corporate Light)
- **Fondo General**: `#f6f7f9` (Gris claro muy sutil para reducir fatiga visual).
- **Texto Principal**: `#1d252d` y `#415366` para jerarquía de lectura legible.
- **Acentos Primarios**: `#23405f` (Azul marino corporativo) para acciones primarias.
- **Indicadores de Estado**: `#146c43` (Verde éxito) y `#82071e` (Rojo error/alerta).
- **Paneles y Tarjetas**: `#ffffff` (Blanco puro) sobre el fondo gris para crear separación visual y elevación.

### 2. Disposición Visual (Layout)
- **El Contenedor `shell`**: Actúa como un marco principal responsivo utilizando CSS Grid para centrar y distribuir el contenido, soportando variantes como `shell-wide` para paneles extendidos.
- **Sistema de Tarjetas (`status-panel`, `module-card`)**: Agrupación lógica de información con bordes sutiles (`#d9e0e7`), radio de borde (`8px`) y sombras suaves para dar profundidad.
- **Grillas Semánticas (`identity-grid`, `runtime-grid`)**: Uso de `display: grid` acoplado con elementos `<dt>` y `<dd>` para mostrar metadatos de forma estructurada y adaptable a múltiples tamaños de pantalla.
- **Tablas Responsivas**: Las tablas (`.responsive-table`) colapsan en móviles transformando cada fila en un bloque de tipo tarjeta con etiquetas de datos autogeneradas (`data-label`), garantizando la usabilidad en dispositivos pequeños sin scroll horizontal excesivo.

### 3. Reusabilidad y Estandarización
Para aplicar esta arquitectura en otros lugares, debes extraer y usar las siguientes clases estructurales como componentes estándar:
- `.shell` y `.shell-wide`: Para los contenedores base de cualquier página.
- `.status-panel`: Para contenedores de formularios, detalles o configuración.
- `.primary-action` / `.secondary-action`: Para la botonera estándar.
- `.empty-state`, `.success-message`, `.error-message`: Para comunicación de estados.

## Recomendación de Nuevos Módulos
Continuando con la evolución modular, los siguientes módulos serían los pasos naturales para expandir el `inventario-modular`:

1. **Módulo de Redes (Networking)**: Gestión de switches, routers, IPs, VLANs y puertos.
2. **Módulo de Software y Licencias**: Seguimiento de sistemas operativos, software ofimático y fechas de expiración de licencias instaladas en los equipos.
3. **Módulo de Mantenimiento y Tickets**: Registro de incidentes, mantenimientos preventivos/correctivos asociados a los equipos.
4. **Módulo de Reportes y Auditoría**: Trazabilidad de cambios (quién movió qué equipo o asignó qué recurso) y exportación a PDF/Excel.
