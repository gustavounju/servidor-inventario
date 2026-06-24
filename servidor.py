from flask import Flask, send_from_directory, request, g
import os
import threading
import platform
import socket
import uuid
import json
import logging.handlers
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

# Load environment variables from .env if present (useful for Windows local dev)
load_dotenv()

# Base de datos y Migraciones
from database.db_core import init_db, get_db_connection
from database.migrations import run_all_migrations

# Utils e IA
import time
import logging
import datetime
from utils.constants import UPLOAD_FOLDER, LOG_FOLDER, APP_VERSION, list_fuero_mapping_rows
from services.ai_assistant import train_ai_model

# --- OBSERVABILIDAD E INSTRUMENTACIÓN ---
os.makedirs('logs', exist_ok=True)

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        from flask import has_request_context, g
        if has_request_context():
            record.request_id = getattr(g, 'request_id', 'N/A')
        else:
            record.request_id = 'SYSTEM'
        return True

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'timestamp': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'event': record.getMessage(),
            'request_id': getattr(record, 'request_id', 'N/A')
        }
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
if logger.hasHandlers():
    logger.handlers.clear()

req_filter = RequestIdFilter()

json_handler = logging.handlers.RotatingFileHandler(
    'logs/inventario.json.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
)
json_handler.setFormatter(JsonFormatter())
json_handler.addFilter(req_filter)
logger.addHandler(json_handler)

console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - [%(request_id)s] - %(message)s'))
console_handler.addFilter(req_filter)
logger.addHandler(console_handler)

_GLOBAL_CACHE_LOCK = threading.Lock()
_GLOBAL_CACHE = {
    'timestamp': 0,
    'data': None,
    'authenticated': False
}

def invalidate_global_cache():
    """Invalida el caché global. Llamar después de cualquier INSERT/UPDATE/DELETE."""
    with _GLOBAL_CACHE_LOCK:
        _GLOBAL_CACHE['data'] = None
        _GLOBAL_CACHE['timestamp'] = 0

# Blueprints
from blueprints.bp_dashboard import bp_dashboard
from blueprints.bp_api import bp_api
from blueprints.bp_stock import bp_stock
from blueprints.bp_setup import bp_setup
from blueprints.bp_infrastructure import bp_infrastructure
from blueprints.bp_tasks import bp_tasks
from blueprints.bp_mobile import bp_mobile
from blueprints.bp_tecnicos import bp_tecnicos
from blueprints.bp_operadores import bp_operadores
from blueprints.bp_auth import bp_auth
from blueprints.bp_vault import bp_vault
from blueprints.bp_users import bp_users
from blueprints.bp_maps import bp_maps
from utils.auth import allowed_module_links, auth_guard, auth_mode_label, available_roles, csrf_guard, current_user, ensure_default_admin, generate_csrf_token, has_permission, is_authenticated, role_label
from utils.runtime_urls import get_public_app_base_url, get_public_script_fallback_url
from blueprints.bp_setup import _get_secure_launcher_command

# Inicializar Flask
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000 # 1 year cache for static files
app.secret_key = os.environ.get('FLASK_SECRET_KEY')
if not app.secret_key:
    raise EnvironmentError("FLASK_SECRET_KEY no está definida en el .env. El servidor no puede arrancar de forma segura.")
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
_is_linux = platform.system() != 'Windows'
_secure_env = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
app.config['SESSION_COOKIE_SECURE'] = _is_linux or _secure_env
from datetime import timedelta
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

from utils.extensions import limiter
limiter.init_app(app)

# Asegurar directorios
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(LOG_FOLDER, exist_ok=True)

# Registrar Blueprints
app.register_blueprint(bp_dashboard)
app.register_blueprint(bp_api)
app.register_blueprint(bp_stock)
app.register_blueprint(bp_setup)
app.register_blueprint(bp_tasks)
app.register_blueprint(bp_mobile)
app.register_blueprint(bp_tecnicos)
app.register_blueprint(bp_operadores)
app.register_blueprint(bp_infrastructure)
app.register_blueprint(bp_auth)
app.register_blueprint(bp_vault)
app.register_blueprint(bp_users)
app.register_blueprint(bp_maps)

# Filtros para Jinja (si queda alguno que estuviéramos usando, aunque los que se usaban ya están resueltos o no declarados como filters globales en servidor.py original excepto quizas datetime_es, pero lo importabamos donde hiciera falta).
from services.reporting import format_datetime_es
app.jinja_env.filters['datetime_es'] = format_datetime_es
# Contexto Global para todas las plantillas (Jinja2)
@app.context_processor
def inject_global_vars():
    now = time.time()
    user_auth = is_authenticated()
    
    with _GLOBAL_CACHE_LOCK:
        cache_ok = (
            _GLOBAL_CACHE['data'] is not None
            and (now - _GLOBAL_CACHE['timestamp'] < 60)
            and (_GLOBAL_CACHE.get('authenticated', False) == user_auth)
        )
        if cache_ok:
            cached_data = _GLOBAL_CACHE['data']
            kpis = cached_data['kpis']
            extra_data = cached_data['extra_data']
            
    if not cache_ok:
        kpis, extra_data = _load_kpis_from_db(user_auth)
        with _GLOBAL_CACHE_LOCK:
            _GLOBAL_CACHE['data'] = {'kpis': kpis, 'extra_data': extra_data}
            _GLOBAL_CACHE['timestamp'] = time.time()
            _GLOBAL_CACHE['authenticated'] = user_auth

    return {
        'app_version': APP_VERSION,
        'csrf_token': generate_csrf_token,
        'is_authenticated': user_auth,
        'current_user': current_user(),
        'auth_mode_label': auth_mode_label(),
        'has_access': has_permission,
        'module_access_links': allowed_module_links(),
        'current_role_label': role_label(),
        'available_roles': available_roles(),
        'client_script_base_url': get_public_app_base_url(),
        'client_script_fallback_url': get_public_script_fallback_url(),
        'secure_launcher_command': _get_secure_launcher_command(get_public_app_base_url(), get_public_script_fallback_url()),
        'total_pages': 1,
        'page': 1,
        'per_page': 25,
        **kpis,
        **extra_data
    }

def _load_kpis_from_db(user_auth):
    from utils.auth import list_app_users
    kpis = {
        'kpi_total_activas': 0, 'kpi_total_graveyard': 0, 'kpi_win7': 0,
        'kpi_alerta_ram': 0, 'kpi_total_impresoras_oficial': 0,
        'kpi_tareas_hoy': 0, 'kpi_total_pendientes': 0,
        'kpi_alerta_media': 0, 'kpi_criticas': 0
    }
    extra_data = {
        'ad_users_list': [], 'fueros': {}, 'technicians': [],
        'app_users_list': [], 'all_pcs': [], 'kpi_usuarios_pendientes': 0
    }
    
    efemeride_actual = None
    
    try:
        with get_db_connection() as conn:
            efemeride_activa = conn.execute("SELECT * FROM efemerides WHERE is_active = 1 LIMIT 1").fetchone()
            if efemeride_activa:
                efemeride_actual = dict(efemeride_activa)
            else:
                today_mmdd = datetime.datetime.now().strftime("%m-%d")
                efemeride_hoy = conn.execute("SELECT * FROM efemerides WHERE dia_mes = %s LIMIT 1", (today_mmdd,)).fetchone()
                if efemeride_hoy:
                    efemeride_actual = dict(efemeride_hoy)
    except Exception as e:
        logging.error(f"Error fetching efemerides: {e}")
        
    if not efemeride_actual:
        mensajes_motivacionales = [
            {'titulo': 'Trabajo en equipo', 'descripcion': 'El talento gana partidos, pero el trabajo en equipo gana campeonatos.', 'icono': '🤝'},
            {'titulo': 'Innovación Diaria', 'descripcion': 'La innovación distingue a los líderes de los seguidores. ¡A crear!', 'icono': '💡'},
            {'titulo': 'Código Limpio', 'descripcion': 'Cualquier tonto puede escribir código que un ordenador entienda. Los buenos programadores escriben código que los humanos entienden.', 'icono': '💻'},
            {'titulo': 'Mejora Continua', 'descripcion': 'No busques culpables, busca soluciones. Un paso a la vez.', 'icono': '📈'},
            {'titulo': 'Actitud Positiva', 'descripcion': 'Tu actitud, no tu aptitud, determinará tu altitud. ¡Que tengas una excelente jornada!', 'icono': '🚀'},
            {'titulo': 'Soporte IT', 'descripcion': '¿Ya intentaste apagarlo y volverlo a encender? (La vieja confiable).', 'icono': '🔌'},
            {'titulo': 'Cero Bugs', 'descripcion': 'Que tu café sea fuerte y tus errores de compilación sean pocos.', 'icono': '☕'},
            {'titulo': 'Resolución', 'descripcion': 'Todo problema es una oportunidad disfrazada. ¡Vamos por esos tickets!', 'icono': '🛠️'},
            {'titulo': 'Ciberseguridad', 'descripcion': 'La cadena es tan fuerte como su eslabón más débil. Nunca subestimes la seguridad.', 'icono': '🔒'},
            {'titulo': 'Eficiencia IT', 'descripcion': 'Automatiza lo aburrido para tener más tiempo de construir lo asombroso.', 'icono': '⚙️'}
        ]
        today_yday = datetime.datetime.now().timetuple().tm_yday
        # Use modulo arithmetic to ensure a guaranteed different phrase every day
        index = (today_yday * 3) % len(mensajes_motivacionales)
        efemeride_actual = mensajes_motivacionales[index]
        
    extra_data['efemeride_actual'] = efemeride_actual
    
    if user_auth:
        try:
            with get_db_connection() as conn:
                kpis['kpi_total_activas'] = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 1 AND pc_name NOT IN ('PC Generica', 'Infraestructura', 'PC-Generica')").fetchone()["c"]
                kpis['kpi_total_graveyard'] = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 0").fetchone()["c"]
                kpis['kpi_win7'] = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 1 AND os_name LIKE %s AND pc_name NOT IN ('PC Generica', 'Infraestructura', 'PC-Generica')", ("%Windows 7%",)).fetchone()["c"]
                kpis['kpi_alerta_ram'] = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 1 AND alerta_ram_baja = 1 AND pc_name NOT IN ('PC Generica', 'Infraestructura', 'PC-Generica')").fetchone()["c"]
                
                kpis['kpi_total_impresoras_oficial'] = conn.execute("SELECT COUNT(*) as c FROM network_printers").fetchone()["c"]
                kpis['kpi_tareas_hoy'] = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado = 'Hecha' AND DATE(completed_at) = CURDATE()").fetchone()["c"]
                kpis['kpi_total_pendientes'] = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado != 'Hecha'").fetchone()["c"]
                
                extra_data['kpi_usuarios_pendientes'] = conn.execute("SELECT COUNT(*) as c FROM app_users WHERE is_active = 0").fetchone()["c"]

                fueros_rows = conn.execute("SELECT DISTINCT fuero FROM pcs WHERE fuero IS NOT NULL AND fuero != '' AND fuero != 'Desconocido' ORDER BY fuero").fetchall()
                known_fueros = {row['fuero']: row['fuero'] for row in fueros_rows}
                for item in list_fuero_mapping_rows():
                    known_fueros.setdefault(item['label'], item['label'])
                known_fueros.setdefault("PC Generica", "PC Generica")
                known_fueros.setdefault("Infraestructura", "Infraestructura")
                extra_data['fueros'] = dict(sorted(known_fueros.items(), key=lambda item: item[0].lower()))

                sys_users = list_app_users()
                extra_data['app_users_list'] = sys_users
                sys_usernames = {str(u['username']).strip().lower() for u in sys_users}

                ad_users_query = """
                    SELECT LOWER(TRIM(username)) as username, real_name, phone, 1 as is_official
                    FROM ad_users
                    ORDER BY real_name
                """
                all_ad_raw = [dict(row) for row in conn.execute(ad_users_query).fetchall()]

                seen_usernames = {}
                ad_usernames = set()
                
                for u in all_ad_raw:
                    uname = str(u['username']).strip().lower()
                    if u['is_official']:
                        ad_usernames.add(uname)

                    if uname in sys_usernames:
                        continue
                    
                    if uname in seen_usernames:
                        if u['is_official'] and not seen_usernames[uname]['is_official']:
                            seen_usernames[uname] = u
                        continue
                    
                    seen_usernames[uname] = u
                
                directorio_filtrado = list(seen_usernames.values())
                directorio_filtrado.sort(key=lambda x: str(x['real_name']).lower())
                
                extra_data['directorio_filtrado'] = directorio_filtrado
                extra_data['ad_usernames'] = ad_usernames
                
                extra_data['all_pcs'] = [dict(row) for row in conn.execute(
                    """SELECT pc_name, fuero, last_user FROM pcs 
                       WHERE is_active = 1 OR pc_name IN ('PC Generica', 'Infraestructura', 'PC-GENERICA')
                       ORDER BY CASE WHEN pc_name LIKE 'PC%%GENERICA%%' THEN 0 WHEN pc_name LIKE 'INFRAESTRUCTURA%%' THEN 1 ELSE 2 END, pc_name ASC"""
                ).fetchall()]
                
        except Exception as e:
            logging.error(f"Error in context processor KPIs: {e}")
            
    return kpis, extra_data


@app.before_request
def enforce_authentication():
    auth_response = auth_guard()
    if auth_response is not None:
        return auth_response

    csrf_response = csrf_guard()
    if csrf_response is not None:
        return csrf_response

@app.route('/sw.js')
def serve_sw():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')

@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json', mimetype='application/json')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 
                               'icon-192.png', mimetype='image/png')

@app.route('/uploads/<path:filename>')
def serve_upload(filename):
    """Sirve archivos subidos (planos, etc)."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Configuracin y Migraciones iniciales
with app.app_context():
    init_db()
    run_all_migrations()
    default_admin_created = ensure_default_admin()
    if default_admin_created:
        logging.info("Usuario inicial 'administrador' creado.")
    
    def ensure_generic_pc():
        """Asegura que exista una PC genrica y una de Infraestructura para asignar tareas a hardware no inventariado."""
        try:
            with get_db_connection() as conn:
                exists = conn.execute("SELECT 1 FROM pcs WHERE pc_name = 'PC Generica'").fetchone()
                if not exists:
                    print("Creando 'PC Generica'...")
                    conn.execute(
                        "INSERT INTO pcs (pc_name, os_name, is_active) VALUES ('PC Generica', 'Virtual/Pendiente', 'True')"
                    )
                    conn.commit()
                
                exists_infra = conn.execute("SELECT 1 FROM pcs WHERE pc_name = 'Infraestructura'").fetchone()
                if not exists_infra:
                    print("Creando 'Infraestructura'...")
                    conn.execute(
                        "INSERT INTO pcs (pc_name, os_name, is_active) VALUES ('Infraestructura', 'Equipos de Red/Servidores', 'True')"
                    )
                    conn.commit()
        except Exception as e:
            print(f"Error creando PCs base: {e}")

    ensure_generic_pc()
    train_ai_model()

# --- SECURITY HARDENING & OBSERVABILITY ---
@app.before_request
def inject_request_id():
    g.request_id = request.headers.get('X-Request-Id', str(uuid.uuid4()))
    app.logger.info(f"Incoming Request: {request.method} {request.path}")

@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    # response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval'; img-src 'self' data:;"
    return response

@app.errorhandler(500)
def handle_500_error(e):
    from flask import jsonify, request
    app.logger.error(f"Server Error: {e}")
    if request.path.startswith('/api/'):
        return jsonify({"status": "error", "message": "Error interno del servidor. Contacte al administrador."}), 500
    return "Error interno del servidor. Contacte al administrador.", 500

@app.errorhandler(Exception)
def handle_unhandled_exception(e):
    from flask import jsonify, request
    # Ignorar HttpExceptions como 404
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        return e
    app.logger.error(f"Unhandled Exception: {e}")
    if request.path.startswith('/api/'):
        return jsonify({"status": "error", "message": "Ocurrió un problema inesperado."}), 500
    return "Ocurrió un problema inesperado.", 500

if __name__ == "__main__":
    sistema = platform.system()
    
    if sistema == "Windows":
        print("\n" + "="*64)
        print(" MODO DESARROLLO (Windows)")
        print(f" Servidor iniciado en hostname: {socket.gethostname()}")
        print(" - Principal: http://0.0.0.0:5000")
        print(" - Fallback:  http://0.0.0.0:8080")
        print("="*64)
        
        def run_fallback():
            try:
                app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)
            except Exception as e:
                print(f"Error en fallback 8080: {e}")
        
        threading.Thread(target=run_fallback, daemon=True).start()
        debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
        app.run(host='0.0.0.0', port=5000, debug=debug_mode, use_reloader=False)
    else:
        print("\n" + "="*64)
        print(" MODO PRODUCCIÓN (Linux)")
        
        cert_file = 'cert.pem'
        key_file = 'key.pem'
        
        if not os.path.exists(cert_file) and os.path.exists('inventario-cert.crt'):
            cert_file = 'inventario-cert.crt'
            print(f" - Usando certificado alternativo: {cert_file}")

        use_ssl = os.path.exists(cert_file) and os.path.exists(key_file)

        if use_ssl:
            print(" Iniciando servidor Flask con HTTPS y HTTP...")
            print(f" - HTTPS: https://0.0.0.0:5000 (Cert: {cert_file})")
            print(" - HTTP:  http://0.0.0.0:8080 (para mviles)")
            
            def run_https():
                try:
                    app.run(host="0.0.0.0", port=5000, debug=False, 
                            ssl_context=(cert_file, key_file), use_reloader=False)
                except Exception as e:
                    print(f"ERROR al iniciar HTTPS: {e}")
            
            https_thread = threading.Thread(target=run_https, daemon=True)
            https_thread.start()
        else:
            print(" WARNING: No se encontraron certificados SSL (cert.pem/key.pem).")
            print(" Iniciando servidor SOLO en modo HTTP (Puerto 5000 y 8080).")
            
            def run_http_alt():
                app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
            
            threading.Thread(target=run_http_alt, daemon=True).start()

        print("="*64)
        app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)
