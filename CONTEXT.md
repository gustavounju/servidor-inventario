# Contexto del Sistema de Inventario - Centro Judicial San Pedro, Jujuy

## 📋 Resumen del Proyecto
Sistema de inventario para el Departamento de Informática del Centro Judicial (San Pedro, Jujuy). Desarrollado en Python/Flask con HTML frontend.

## 🚀 Stack Técnico
- **Backend**: Python 3.13, Flask, MySQL
- **Frontend**: HTML, CSS (gold.css), JavaScript
- **Base de datos**: MySQL local (dev) / MySQL remoto (prod)
- **Autenticación**: Sistema propio con roles, futura integración con Active Directory
- **Inventario Modular (nuevo foco)**: proyecto Java/Spring Boot API-first en
  `inventario-modular/`, pensado para reemplazo progresivo por módulos sin apagar el Flask
  actual. Corre localmente en `0.0.0.0:8081`, muestra el login inicial en `/login` y
  expone `/api/v1/health`.
- **Inventario Next**: experimento SvelteKit en `inventario-next/`. Queda pausado y no es
  el foco activo; no debe levantarse salvo pedido explícito.

## 🧪 Inventario Modular (Java, API-first)
- **Objetivo**: construir un sistema modular nuevo en Java, limpio y API-first, manteniendo
  Flask como producción estable hasta validar cada reemplazo.
- **Estado actual**: proyecto base creado en `inventario-modular/` con Spring Boot 4.0.0,
  Java 21, Maven Wrapper, Spring Web MVC, Security, Validation, JPA, LDAP, MySQL y Flyway.
- **Arranque local**: `cd inventario-modular && .\mvnw.cmd spring-boot:run`.
- **URL local de red**: `http://192.168.1.8:8081/` y
  `http://192.168.1.8:8081/login`; health tecnico en
  `http://192.168.1.8:8081/api/v1/health`.
- **Login inicial**: `/` redirige a `/login`; el modo local autentica al administrador
  configurado por `BOOTSTRAP_ADMIN_USERNAME` / `BOOTSTRAP_ADMIN_PASSWORD`. La opcion
  Dominio queda preparada y pendiente de conectar con Active Directory.
- **Primer endpoint**: `/api/v1/health` responde `{"status":"ok","service":"inventario-modular"}`.
- **Primer endpoint protegido**: `/api/v1/modules` expone el catalogo estable de modulos
  (`EQUIPOS`, `ACTAS`, `MUEBLES`, `PATRIMONIO`, `STOCK`, `COMPONENTES`, `USUARIOS`,
  `REPORTES`, `TAREAS`) y responde 401 si no hay usuario autenticado.
- **Convivencia**: el inventario viejo Flask sigue siendo el sistema operativo real. Modular
  no se conecta a producción y todavía excluye temporalmente DataSource/JPA/Flyway hasta
  crear la base local `inventario_modular` y las migraciones iniciales.
- **Documentos de traspaso**:
  - `docs/inventario-modular/README.md`
  - `docs/inventario-modular/requerimientos-sistema.md`
  - `docs/inventario-modular/plan-de-trabajo.md`
  - `docs/inventario-modular/procedimientos.md`
  - `docs/decisions/ADR-002-inventario-modular-api-first.md`

## 🏛️ Sistema Patrimonial y Gemelos Digitales (Novedad Agosto 2026)
- **Modelo de Activos**: La verdad del sistema evoluciona de "inventario centrado en scripts" a "Gemelo Digital Patrimonial".
- **Estado de Validación (`validation_status`)**:
  - `validado`: Coincidencia confirmada entre el activo registrado y la telemetría del script.
  - `pendiente`: Puesto armado y desplegado, esperando primera sincronización del script `.ps1`.
  - `discrepancia`: Alerta por cambio o sustitución de hardware no documentada.
  - `sin_gemelo`: PC reportada por script sin registro patrimonial de activo.
- **Órdenes de Armado (Build Orders)**:
  - Módulo de gestión en `/build_orders` (`[ ARMADO ]` en toolbar).
  - Permite agrupar componentes del stock (`CPU`, `Monitor`, `Teclado`, `Mouse`, `Impresora`), asociarlos a un remito/OC y desplegarlos a un puesto judicial en 1-clic.
  - Generación de doble etiqueta QR (Gabinete + Monitor) linkeada a la ficha viva `/pc/<pc_name>`.

## 🏗️ Infraestructura de Base de Datos
### Desarrollo (Casa/Oficina)
- **Host**: 127.0.0.1
- **Usuario**: root
- **Contraseña**: [OCULTA]
- **Base de datos**: inventario_dev
- **Puerto**: 3306

### Producción (Centro Judicial)
- **Host**: 10.15.2.251
- **Usuario/Contraseña**: Por configurar
- **Puerto**: 3306

## 📁 Estructura del Proyecto
```
ServidorInventario/
├── servidor.py              # Aplicación principal Flask
├── inventario-modular/      # Aplicación Java/Spring Boot API-first en desarrollo
├── inventario-next/         # Experimento SvelteKit pausado
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
- **Administrador**: Acceso completo a todos los módulos.
- **Funcionario (Nuevo)**: Carga y gestión de Remitos/Stock y Visor de Tareas en modo lectura únicamente.
- **Sistemas / Infraestructura**: Dashboard, Infra, Reportes, Mobile, Audit Racks.
- **Técnico**: Dashboard, Reportes, Mobile. Permiso de `manage_stock` configurable en panel de usuarios.
- **Operador**: Módulo simplificado de operadores.
- **Consulta**: Acceso únicamente a reportes.

### Usuario por Defecto
- **Usuario**: administrador
- **Contraseña**: [OCULTA]
- **Rol**: Administrador (acceso completo)

## 📊 Módulos Disponibles
1. **Dashboard** (`/`): Vista principal con estadísticas
2. **Infraestructura** (`/infra/`): Gestión de equipos y red
3. **Carga de Stock** (`/stock/`): Recepción por Remito (ej: NOVA, OC 185-2026), auto-generación de IDs internos y asignación por Active Directory (Persona + Fuero autocompletado).
4. **Reportes** (`/reportes/`): Generación de informes
5. **Mobile** (`/mobile/`): Soporte para dispositivos móviles
6. **Tareas** (`/tasks/`): Visor y gestión de tareas técnicas
7. **Setup** (`/setup/`): Configuración del sistema

### Inventario Next (rutas locales)
Next queda pausado/deshabilitado como foco de trabajo. No levantar `inventario-next` salvo
pedido explícito.

### Inventario Modular (rutas locales)
1. **Login Modular** (`http://192.168.1.8:8081/` y `/login`): login local del nuevo sistema con opcion Dominio pendiente.
2. **Health Modular** (`/api/v1/health`): endpoint tecnico de arranque.
3. **Panel Modular** (`/app`): primer panel interno con listado de modulos disponibles.
4. **Catálogo de módulos** (`/api/v1/modules`): endpoint protegido con el listado base de módulos activables.

## 🔄 Flujo de Despliegue (Workflow)
1. **Desarrollo local** en Windows (casa/oficina)
2. **Pruebas** con MySQL local
3. **Subida** de cambios a GitLab
4. **Despliegue** en servidor Ubuntu con MySQL remoto (10.15.0.62)
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

# Green-API WhatsApp (Configurado vía .env)
GREEN_API_ID_INSTANCE=[TU_ID_INSTANCE]
GREEN_API_TOKEN_INSTANCE=[TU_TOKEN_INSTANCE]
GREEN_API_PHONE=[TU_GRUPO_WHATSAPP]@g.us

# Web Push / notificaciones con celular bloqueado
# Requiere HTTPS confiable en Android y salida del servidor hacia FCM.
ALLOW_WEB_PUSH=false
VAPID_PUBLIC_KEY=
VAPID_PRIVATE_KEY=
VAPID_CLAIMS_EMAIL=mailto:admin@example.invalid

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
1. Mejora de interfaz móvil
2. Optimización de consultas a base de datos
3. Evaluar WebSockets solo para vistas abiertas; con celular bloqueado el canal soportado es Web Push.
4. Sistema de backup automático
5. **Módulo de Armado de Puestos Completos (Combos), QR Par (CPU+Monitor) y Reemplazo por Falla** (ver detalles completos en [PLAN_GESTION_PUESTOS_Y_REEMPLAZOS.md](file:///g:/unju2025/google%20gravity/ServidorInventario/PLAN_GESTION_PUESTOS_Y_REEMPLAZOS.md)).

## 🆕 Últimos Cambios (Changelog)
- **Agosto 2026 (Inventario Modular - Proyecto base)**: Se creó el proyecto
  `inventario-modular/` con Spring Boot 4.0.0, Java 21 y Maven Wrapper. El servidor corre
  localmente en `0.0.0.0:8081` y expone `/api/v1/health`, probado con `.\mvnw.cmd test`.
  El arranque local no se conecta a producción y deja DataSource/JPA/Flyway temporalmente
  excluidos hasta crear la base `inventario_modular` y las migraciones iniciales.
- **Agosto 2026 (Inventario Modular - Catálogo de módulos)**: Se agregó el primer contrato
  de módulos activables en `inventario-modular/src/main/java/.../modules`. El endpoint
  protegido `GET /api/v1/modules` devuelve el catálogo base y la suite Java verifica orden,
  unicidad, formato de códigos y respuesta 401 para acceso anónimo.
- **Agosto 2026 (Inventario Modular - login local)**: `/` redirige a `/login`, que permite
  ingresar en modo Local con el administrador configurado por entorno o `.env`. La sesion
  habilita `/app` y permite consultar `/api/v1/modules`; la opcion Dominio queda pendiente
  para el modulo Active Directory. Se documentaron procedimientos de arranque,
  verificacion, pruebas y push a GitHub en `docs/inventario-modular/procedimientos.md`.
- **Agosto 2026 (Web Push móvil y certificados locales)**: Se reparó el flujo de notificaciones para técnicos en Android. La vista móvil ahora registra el service worker con cache-busting, muestra errores concretos de permisos/certificado/suscripción y deja públicos `/sw.js` y `/manifest.json` para que el navegador pueda instalarlos antes de autenticarse. Se agregó soporte de certificado local con CA propia mediante `tools/generate_certs.py`; el certificado que se instala en celulares es la CA pública (`inventario-local-ca.crt`), nunca la clave privada. Para que las notificaciones lleguen con el celular bloqueado, producción debe tener `ALLOW_WEB_PUSH=true`, claves VAPID configuradas y salida HTTPS permitida hacia FCM (`fcm.googleapis.com`).
- **Agosto 2026 (Gestión de usuarios restaurada)**: Se restauró el acceso `[ USUARIOS ]` en la navegación de gestión y se agregó el permiso modular `manage_users`, disponible solo para administradores/superusuarios.
- **Julio 2026 (Roles y Permisos Modulares - v3.1.0)**: Reestructuración y granulado del sistema de control de accesos. Se implementó una lógica de overrides de permisos a nivel de usuario en base de datos. Se protegieron rutas críticas de backend en `bp_tasks.py` y `bp_dashboard.py`. Se rediseñó el panel de usuarios para incluir edición directa de cuentas y permisos. Se resolvió la evasión del modo móvil en celulares agregando validaciones de dispositivo híbridas (User-Agent en backend y detección de Viewport/UA en cliente mediante script en `_module_switcher.html`).
- **Julio 2026 (Sincronización AD)**: Se implementó la sincronización de equipos desde Active Directory. La nueva herramienta (ubicada en Infraestructura) extrae la OU (Unidad Organizativa) del `distinguishedName` de cada computadora en el AD y mapea automáticamente el Fuero correspondiente en la tabla local de PCs. Además, el Dashboard ahora cruza correctamente el nombre de sesión (ej. GMURAD) con el nombre real (ej. Gustavo Murad) obtenido de los usuarios del AD, mejorando drásticamente la legibilidad del inventario.
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
- **UI/UX (2 Julio 2026)**: Rediseño global completo del sistema a estética **Industrial / High-Vis**. Este cambio sobreescribe y reemplaza definitivamente al anterior diseño "Impeccable" (Midnight Radar / bordes redondeados). Se implementó el tema *Industrial Void* en `gold.css` con fondos `#09090B`, reduciendo todos los radios de borde a `2px` (esquinas rígidas), eliminando sombras difuminadas, usando fuentes monoespaciadas (`JetBrains Mono`/`Courier New`) para métricas/datos tabulares e incorporando alertas visuales de alto contraste como franjas de peligro y tiras de LED de estado en Dashboard, Visor, Efemérides, Usuarios y vista móvil.
- **Configuración y Seguridad (6 Julio 2026)**: Implementación del panel de **Ajustes Globales** (Backend) para Administradores. Se migró la configuración de Active Directory del archivo `.env` a la base de datos (`app_settings`). Como resultado de una auditoría de seguridad (`/cso`), se implementó cifrado de datos sensibles en reposo utilizando `cryptography.fernet` para las contraseñas de sincronización AD (`AD_SYNC_PASSWORD`), utilizando la `FLASK_SECRET_KEY` como base para la llave de cifrado. Además se protegió la interfaz usando `is_superuser()` asegurando que sólo los administradores puedan configurar la sincronización de AD.
- **UI/UX & Seguridad (7 Julio 2026)**: Migración de los paneles de Configuración y Mantenimiento a ventanas modales (`_modal_config.html`, `_modal_maintenance.html`) integradas en el Dashboard, eliminando la necesidad de navegar a páginas separadas. Se unificó su diseño al tema *Industrial Void*. Se corrigió una vulnerabilidad de experiencia/lógica en el Modo Mantenimiento, el cual ahora rechaza proactivamente los intentos de inicio de sesión de técnicos (usuarios no administradores) directamente en el formulario (`/login`), mostrando una advertencia clara en pantalla y evitando estados ambiguos o redirecciones en bucle.
- **UI/UX & SQL (12 Julio 2026)**: Refactorización profunda del layout y las tablas del Visor de Tareas (`visor_tareas.html`). Se rediseñó el panel superior eliminando texto redundante (ej. "Control y Registro"), se compactaron las tarjetas de métricas para maximizar espacio, y se resolvieron superposiciones de datos de "Fuero" asegurando una carga correcta desde `pcs` o `tasks`. Además, se agregó la columna *Técnico Asignado* al listado de Historial.
- **UI/UX & AD Integration (13 Julio 2026)**: Se integró la funcionalidad de coincidencias de Active Directory (`_attach_task_user_matches`) en el *Panel de Tareas de PC Genérica*, mostrando sugerencias automáticas de PC real y Fuero basadas en el usuario solicitante para facilitar la reasignación. También se mejoró el contraste de las descripciones en los modales oscuros.
- **Hotfix (15 Julio 2026)**: Restauración del script cliente `inventario.ps1` al directorio raíz del servidor tras haber sido borrado incidentalmente en un commit previo. Se corrigió el botón de copia del script en la barra de herramientas del operador (`_module_switcher.html`) inyectando el atributo `data-command` faltante. Se corrigió además la función `copyScript` en `gold.js` y `login.html` eliminando el escapado redundante `\\r\\n` a favor de un salto de línea real (`\r\n`), permitiendo que el comando se autoejecute al ser pegado en PowerShell.
- **Feature (16 Julio 2026)**: Implementación del Repositorio Público de Software y Drivers (`/descargas`). Se creó una interfaz web (`descargas.html`) que lee dinámicamente un catálogo local (`catalog.json`) y escanea el disco (`static/downloads/`) para servir ejecutables de instalación a velocidad LAN a los técnicos. Además, se implementó auditoría de descargas almacenando el historial (IP, categoría, archivo) en la tabla `software_download_logs` para su revisión por parte de Administradores.
- **UI/UX & Interactive 3D (22 Julio 2026)**: Rediseño completo de la navegación del Repositorio de Software. Se reemplazó el botón estático de "Repositorio SW" en la página de inicio/login por un **carrusel de cilindro giratorio 3D** interactivo (prisma pentagonal) que auto-rota lentamente al estar inactivo, responde al desplazamiento horizontal del mouse al pasar por encima y redirige a la sección/categoría correspondiente en un clic. Adicionalmente, se implementó un dial de cilindro 2D vertical en la barra superior de operadores (evitando el aplanamiento CSS en menús overflow-hidden), y se corrigió el diseño de tarjetas en `/descargas` agregando truncamiento de nombres largos (`text-overflow: ellipsis`) con tooltips al pasar el mouse.

- **Julio 2026 (Puestos Completos, QR Par y Reemplazo por Falla - v3.3.0)**:
  1. **Persistencia Multi-Worker y Auto-Cierre Móvil**: Migración de las sesiones de escáner en vivo a base de datos MySQL (`scan_sessions`), resolviendo la sincronización en arquitecturas Gunicorn multi-worker de produción. Auto-cierre de la sesión en el celular al confirmar la carga o cerrar el modal desde la PC.
  2. **Asignación Flexible y Combo de Puestos Completos (1-Clic)**: Modal en `stock.html` para vinculación de equipos a Usuarios (AD), Fueros o PCs con campos 100% opcionales (soporta desde la entrega de 1 periférico suelto hasta el combo completo de 5 elementos: CPU, Monitor, Teclado, Mouse e Impresora).
  3. **Impresión de Etiquetas QR Par (CPU + Monitor)**: Vista `/pc/<pc_name>/qr_label` con diseño de doble etiqueta (Gabinete + Trasera de Monitor) optimizada para impresoras térmicas y papel A4.
  4. **Flujo de Reemplazo por Falla (Sustitución Directa de Repuesto)**: Acción atómica `⚡ Sustituir por Falla` en `pc_detail.html` que da de baja el componente averiado a estado `Retirado` (Scrap) y asigna el repuesto del Stock en un solo clic.

- **Agosto 2026 (Monolito Modular Endurecido - Fases 1 a 7 Completadas)**:
  1. **Fase 1 (Seguridad Urgente y Secretos)**: Eliminación de secretos hardcodeados, sanitización contra inyección LDAP en Active Directory, requerimiento estricto de autenticación Bearer/Token en ingesta y protección CSRF en acciones mutativas del Vault.
  2. **Fase 2 (Autenticación y API Scopes)**: Implementación de control granular de acceso a nivel de API (`utils/auth.py`) con permisos parametrizados por ámbitos (*scopes* como `inventory:submit`, `external:read_purchase_orders`, `external:read_remitos`, `maintenance:read`).
  3. **Fase 3 (Migraciones Versionadas y Capa de Repositorios)**: Sistema autónomo de migraciones versionadas en `database/migrator.py` e introducción de la capa `repositories/` (`PcRepository`, `ComponentRepository`, `TaskRepository`, `UserRepository`) para desacoplar SQL directo en Blueprints.
  4. **Fase 4 (Auditoría y Backups)**: Centralización de eventos en `services/audit_service.py` (Vault, gestión de usuarios, cambios patrimoniales) y respaldos automatizados e íntegros en `scripts/backup_db.py` con prueba autónoma de descompresión GZip y firmas SQL.
  5. **Fase 5 (Arquitectura de Servicios - Lógica de Negocio)**: Extracción de la lógica de negocio de los blueprints hacia la capa de `services/` (`TaskService`, `StockService`, `VaultService`), desacoplando el enrutamiento HTTP del núcleo de reglas de negocio.
  6. **Fase 6 (Contratos API Estrictos y Observabilidad)**: Implementación de contratos estandarizados (`utils/api_responses.py`) asegurando salidas consistentes (success/data/error) y creación del endpoint de observabilidad en `/api/health` para monitoreo proactivo de los servicios subyacentes.
  7. **Fase 7 (Tests y Release)**: Creación de la suite completa de pruebas automatizadas (`tests/`), logrando alta cobertura de integración para API, lógica y repositorios. Limpieza general del repositorio de scripts temporales y ajuste final de la documentación.
---

**Última actualización**: 21 de Agosto 2026
**Versión del sistema**: Según APP_VERSION en utils/constants.py
