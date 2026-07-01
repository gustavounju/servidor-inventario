# Contexto del Sistema de Inventario - Centro Judicial San Pedro, Jujuy

## 📋 Resumen del Proyecto
Sistema de inventario para el Departamento de Informática del Centro Judicial (San Pedro, Jujuy). Desarrollado en Python/Flask con HTML frontend.

## 🚀 Stack Técnico
- **Backend**: Python 3.13, Flask, MySQL
- **Frontend**: HTML, CSS (gold.css), JavaScript
- **Base de datos**: MySQL local (dev) / MySQL remoto (prod)
- **Autenticación**: Sistema propio con roles, futura integración con Active Directory

## 🏗️ Infraestructura de Base de Datos
### Desarrollo (Casa/Oficina)
- **Host**: 127.0.0.1
- **Usuario**: root
- **Contraseña**: [OCULTA]
- **Base de datos**: inventario_dev
- **Puerto**: 3306

### Producción (Centro Judicial)
- **Host**: 10.15.3.20
- **Usuario/Contraseña**: Por configurar
- **Puerto**: 3306

## 📁 Estructura del Proyecto
```
ServidorInventario/
├── servidor.py              # Aplicación principal Flask
├── blueprints/              # Módulos de la aplicación
│   ├── bp_dashboard.py      # Dashboard principal
│   ├── bp_api.py           # API endpoints
│   ├── bp_stock.py         # Gestión de stock
│   ├── bp_setup.py         # Configuración
│   ├── bp_infrastructure.py # Infraestructura
│   ├── bp_tasks.py         # Gestión de tareas
│   ├── bp_mobile.py        # Soporte móvil
│   └── bp_auth.py          # Autenticación
├── database/               # Modelos de base de datos
│   ├── db_core.py         # Conexión y configuración
│   └── migrations.py      # Migraciones de base de datos
├── utils/                  # Utilidades
│   ├── auth.py            # Autenticación y roles
│   ├── constants.py       # Constantes globales
│   └── runtime_urls.py    # URLs dinámicas
├── templates/              # Plantillas HTML
├── static/                 # Assets estáticos
├── services/              # Servicios (AI, reporting)
├── tests/                 # Pruebas automatizadas (pytest)
└── logs/                  # Logs del sistema
```

## 👥 Sistema de Autenticación y Roles
### Roles Disponibles
- **Administrador**: Acceso completo a todos los módulos
- **Sistemas**: Dashboard, Infra, Reportes, Mobile
- **Técnico**: Dashboard, Reportes, Mobile
- **Usuario**: Solo lectura básica

### Usuario por Defecto
- **Usuario**: administrador
- **Contraseña**: [OCULTA]
- **Rol**: Administrador (acceso completo)

## 📊 Módulos Disponibles
1. **Dashboard** (`/`): Vista principal con estadísticas
2. **Infraestructura** (`/infra/`): Gestión de equipos y red
3. **Reportes** (`/reportes/`): Generación de informes
4. **Mobile** (`/mobile/`): Soporte para dispositivos móviles
5. **Stock** (`/stock/`): Gestión de inventario
6. **Tareas** (`/tasks/`): Gestión de tareas técnicas
7. **Setup** (`/setup/`): Configuración del sistema

## 🔄 Flujo de Despliegue (Workflow)
1. **Desarrollo local** en Windows (casa/oficina)
2. **Pruebas** con MySQL local
3. **Subida** de cambios a GitLab
4. **Despliegue** en servidor Ubuntu con MySQL remoto (10.15.3.20)
5. **Configuración** de variables de entorno para producción

## ⚙️ Variables de Entorno (.env)
```env
# Claves principales
FLASK_SECRET_KEY=[OCULTA]
GEMINI_API_KEY=[OCULTA]

# Base de Datos
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASS=[OCULTA]
DB_NAME=inventario_dev

# Configuración de Servidor y Sesión
SESSION_COOKIE_SECURE=false
INVENTARIO_PUBLIC_BASE_URL=
INVENTARIO_PUBLIC_HTTP_FALLBACK_URL=

# Autenticación y Usuarios
AUTH_MODE=local
BOOTSTRAP_ADMIN_USERNAME=administrador
BOOTSTRAP_ADMIN_PASSWORD=[OCULTA]
INVENTARIO_API_TOKEN=

# Green-API WhatsApp
GREEN_API_ID_INSTANCE=7107547800
GREEN_API_TOKEN_INSTANCE=5d291257bd7045a6b85b3c7b19d60cf3b59e0f9845124c8e83
GREEN_API_PHONE=120363407471144144@g.us

# OCR (Opcional)
PDF_OCR_LANG=spa+eng
PDF_OCR_DPI=300
PDF_OCR_MIN_CHARS=20
TESSERACT_CMD=
```

## 🚀 Comandos de Ejecución
### Desarrollo (Windows)
```bash
python servidor.py
```

### Producción (Ubuntu/Linux)
```bash
# Con SSL si existen certificados
python servidor.py

# Sin SSL
python servidor.py (modo HTTP en puerto 8080 para móviles)
```

## 📞 URLs de Acceso
- **Local**: http://127.0.0.1:5000
- **Red local**: http://192.168.1.8:5000
- **Login**: http://127.0.0.1:5000/login

## 🛠️ Problemas Conocidos
1. **Menú duplicado**: El menú superior se repite en la parte inferior de la misma interfaz
2. **Advertencia SSL**: Warning de certificado no verificado para sigj.justiciajujuy.gov.ar
3. **Favicon.ico**: No existe, genera error 404

## 🔮 Próximas Mejoras
1. Integración con Active Directory
2. Mejora de interfaz móvil
3. Optimización de consultas a base de datos
4. Implementación de WebSockets para notificaciones en tiempo real
5. Sistema de backup automático

## 🆕 Últimos Cambios (Changelog)
- **Junio 2026 (UI Mensajes Directos)**: Se unificó el sistema de comunicación directa entre administradores y técnicos en un nuevo *Buzón de Comunicaciones* modal (con diseño premium y protecciones XSS). Se eliminó el botón clásico "[ MSJS ]" y la tarjeta suelta en el visor de tareas, moviendo el acceso principal "[ COMUNICACIÓN ]" directamente al panel superior de navegación.
- **Junio 2026**: Se implementó la **Auditoría Transparente de Racks**. Al cargar el estado de un Rack desde la vista móvil, el sistema agrupa automáticamente los registros de cada técnico en una única "Tarea Diaria" (Auditoría de Racks - [Fecha]) en estado "Hecha". Inyecta cada rack revisado como una nueva Acción dentro del historial de esa tarea, resolviendo la concurrencia y optimizando el tiempo del técnico en terreno al no requerir iniciar o finalizar sesiones manualmente.
- **Hotfix (18 Junio 2026)**: Restauración del bloque de interfaz gráfica (carrusel de métricas) en la vista móvil de Técnicos (`tecnicos.html`). Esto soluciona un bug crítico de JavaScript que provocaba que las métricas personales del técnico no se actualizaran (quedaran en 0) y devuelve el reporte de visibilidad global a los usuarios en terreno.
- **Feature (18 Junio 2026)**: Se amplió el cuadro de texto para la "Solución" en la vista móvil (ahora permite multilinea y es redimensionable). Además, se habilitó la edición de la solución para tareas que ya se encuentran en estado "Hecha". El sistema ahora hace un seguimiento de estas modificaciones agregando un flag `is_edited` a la BD y mostrando un ícono de lápiz junto a la solución si ésta fue modificada a posteriori.
- **Hotfix (19 Junio 2026)**: Exposición pública de las métricas de estado e historial de racks para el Visor General (`/visor`). Adicionalmente, se configuró una base incial para testing automatizado integrando `pytest` al stack técnico y agregando pruebas automatizadas para políticas de acceso de la API.
- **Seguridad (21 Junio 2026)**: Auditoría y remediación de seguridad sobre la carpeta `.agents/skills` usando la herramienta SkillSpector. Se mitigaron riesgos de inyección de prompt (P1), exposición de credenciales (PE3), permisos de herramientas (TM1) y se reforzó la prevención de toma de decisiones autónomas destructivas (EA2) introduciendo cláusulas estrictas de "Human-in-the-loop". Además, se incluyó el código de la herramienta de escaneo en la carpeta `tools/` y un script de escaneo automatizado (`audit_all.bat`).
- **UI/UX Redesign (22 Junio 2026)**: Rediseño completo del Visor de Trabajos (`/visor`) a un estilo "Cyberpunk/Midnight", eliminando el menú lateral innecesario para priorizar visualización.
- **Feature (22 Junio 2026)**: Sistema de Frases Motivacionales dinámicas. Se incorporó su visualización directamente en el Nav global del Visor y se reescribió la lógica de selección diaria en el servidor mediante aritmética modular para evitar repeticiones por PRNG y garantizar rotación diaria.
- **Bugfix (22 Junio 2026)**: Se resolvió un bug con la zona horaria (GMT) en el frontend de Visor que impedía el resaltado visual correcto de las métricas de los racks tomadas en el día actual.
- **Hotfix (22 Junio 2026)**: Se eliminó el uso de CDNs externos (Bootstrap, Chart.js) en todos los templates a favor de assets locales, y se parametrizaron todas las rutas estáticas usando `url_for` para evitar bloqueos del firewall en otras oficinas del tribunal y resolver conflictos de base URL ("Mixed Content") cuando el sistema corre detrás del proxy Nginx (`taller-sp.justiciajujuy.gov.ar`). Además, se corrigió el CSS layout del Visor (`visor_tareas.html`, `gold.css`) compactando agresivamente paddings, gaps y desbordamientos (flex nowrap) para garantizar que todo el dashboard entre en un único viewport horizontal y vertical sin roturas por frases largas.
- **UI/UX (23 Junio 2026)**: Ajustes visuales en el Visor de Trabajos (`/visor`) para reubicar la tarjeta de Efemérides por debajo de la barra de herramientas, centrarla y asegurar que no desborde horizontalmente (removiendo el max-width restrictivo).
- **Seguridad (24 Junio 2026)**: Auditoría de código que comprobó la seguridad contra inyecciones SQL (gracias a queries parametrizadas) e implementación activa de mitigaciones OWASP para prevenir ataques DoS y fuerza bruta. Se integró `Flask-Limiter` protegiendo de forma estricta los endpoints de autenticación (`/login`, `/change_password`) y estableciendo límites por minuto para endpoints de la API pública (`/api/racks/status`, `/submit_inventory`, `/api/local/pdf-ocr`).
- **Bugfix & Feature (24 Junio 2026)**: Se corrigió el funcionamiento de los botones "Apagar Modo Manual" y "Ocultar Fechas Pasadas" en el panel de Efemérides asegurando que recarguen el contexto global del dashboard (`target="_parent"`) al estar dentro de un iframe. Además, se expandió el pool de frases motivacionales dinámicas (de 10 a 30 opciones) y se optimizó su ciclo de rotación mensual para prevenir repetición en ausencia de efemérides.
- **Feature (24 Junio 2026)**: Implementación de la Sincronización Manual de Usuarios desde Active Directory (`services/ad_sync_service.py`). Se añadió un botón en la interfaz de Gestión de Usuarios que permite extraer todos los usuarios del dominio (requiere configurar `AD_SYNC_USER` y `AD_SYNC_PASSWORD` en `.env` sin exponer credenciales en el código base) e insertarlos en la tabla local `ad_users`. Esto garantiza que los nuevos empleados aparezcan en el desplegable de "Solicitante" automáticamente al crear tareas.
- **UI/UX & Seguridad (24 Junio 2026)**: Extensión de la estética 'Cyberpunk/Midnight' a la pantalla de Gestión de Usuarios y sus modales (`_shared_modals.html`), consolidando la identidad visual premium en las vistas administrativas. Además, como parte de la mejora en la navegación del modal (que sufría cierres prematuros o recargas incorrectas), se implementó `_safe_next_url()` en `bp_users.py`. Esto previene vulnerabilidades de *Open Redirect*, asegurando que el parámetro `next_url` solo redirija a rutas internas validadas.
- **Bugfix CSS (24 Junio 2026)**: Remediación de un fallo de compatibilidad de CSS Flexbox (`gap` vs `margin-right`) en el diseño del modal de usuarios y eliminación de clases conflictivas (`op-toolbar`), garantizando la correcta visualización de la cabecera del modal en versiones legacy de Google Chrome (< v84) muy comunes en las PCs de escritorio del tribunal.
- **Feature (25 Junio 2026)**: Módulo de mensajería interna. Se implementó un nuevo botón `[ COMUNICAR ]` en el Visor de Tareas, exclusivo para el rol Administrador, que permite enviar notificaciones de forma individual a un técnico específico o a todos a la vez.
- **Arquitectura & Seguridad (25 Junio 2026)**: Se reemplazó la dependencia externa de Firebase Cloud Messaging (FCM) por un sistema propio de *Short Polling* y cola en base de datos (`tech_messages`). Esto responde a políticas estrictas de seguridad (cero conexiones al exterior de la red judicial). Además, la transmisión de mensajes globales ("a todos") utiliza un modelo de *Fan-Out*, garantizando que la lectura de un usuario no cancele el mensaje para el resto.
- **UI/UX & Sonido (25 Junio 2026)**: Rediseño completo de la interfaz móvil (`tecnicos.html`) guiado por la skill de diseño *Impeccable* y la estética "Midnight Radar / Centro de Operaciones". Se eliminó el "glassmorfismo" pesado en favor de fondos sólidos, tipografía monoespaciada para datos técnicos y bordes de alto contraste. Se introdujeron alertas visuales (modales no intrusivos que se cierran al tocar el fondo) y señales audibles diferenciadas (alarma suave para mensajes de administrador, alarma estridente para nuevas tareas de infraestructura).
- **UI/UX & Mobile (1 Julio 2026)**: Optimización del flujo de acciones en tareas para el Visor General (`visor_tareas.html`) y la vista de Técnicos (`tecnicos.html`). Ahora se muestra por defecto únicamente la última acción registrada en una tarea, ocultando el historial detrás de un botón interactivo 'VER+' (ahorrando espacio vertical significativo). Además, se unificó la terminología de 'Notas' a 'Acciones' en todo el sistema.
- **UI/UX (1 Julio 2026)**: Reorganización del panel de métricas en el Visor General (`visor_tareas.html`). Se trasladó la alerta de 'Tareas Pendientes' de la columna izquierda a la derecha, reemplazando el indicador numérico básico por una tarjeta de prioridad accionable.
- **Feature (1 Julio 2026)**: Mejora en el sistema de Efemérides y Frases Motivacionales (`servidor.py`, `gold.css`). Se restauró la animación de marquesina (*marquee*) para el Visor General. Adicionalmente, el motor de backend ahora inyecta *siempre* el mensaje motivacional diario al final de la descripción de la efeméride del día, unificando ambas notificaciones en un mismo flujo visual.
- **Bugfix & UI/UX (1 Julio 2026)**: Optimización del sistema de notificaciones y bandeja de "Mensajes". Se eliminó la notificación push de "Nueva Tarea" desde la vista móvil (`bp_mobile.py`) para evitar spam. Además, la función `notify_all_technicians` ahora filtra los avisos de tipo `system` para que no inunden la bandeja interna de mensajes de los técnicos (`tech_messages`), reservándola exclusivamente para comunicados directos y notificaciones de acciones específicas.
---

**Última actualización**: 1 de Julio 2026  
**Versión del sistema**: Según APP_VERSION en utils/constants.py