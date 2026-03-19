from flask import Flask
import os
import threading
import platform
import socket
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

# Load environment variables from .env if present (useful for Windows local dev)
load_dotenv()

# Base de datos y Migraciones
from database.db_core import init_db, get_db_connection
from database.migrations import run_all_migrations

# Utils e IA
from utils.constants import UPLOAD_FOLDER, LOG_FOLDER, APP_VERSION
from services.ai_assistant import train_ai_model

# Blueprints
from blueprints.bp_dashboard import bp_dashboard
from blueprints.bp_api import bp_api
from blueprints.bp_stock import bp_stock
from blueprints.bp_setup import bp_setup
from blueprints.bp_infrastructure import bp_infrastructure
from blueprints.bp_tasks import bp_tasks
from blueprints.bp_mobile import bp_mobile
from blueprints.bp_auth import bp_auth
from utils.auth import allowed_module_links, auth_guard, auth_mode_label, available_roles, csrf_guard, current_user, ensure_default_admin, generate_csrf_token, has_permission, is_authenticated, role_label
from utils.runtime_urls import get_public_app_base_url, get_public_script_fallback_url

# Inicializar Flask
app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'default_dev_secret_key_12345')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

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
app.register_blueprint(bp_infrastructure)
app.register_blueprint(bp_auth)

# Filtros para Jinja (si queda alguno que estuviéramos usando, aunque los que se usaban ya están resueltos o no declarados como filters globales en servidor.py original excepto quizas datetime_es, pero lo importabamos donde hiciera falta).
from services.reporting import format_datetime_es
app.jinja_env.filters['datetime_es'] = format_datetime_es

# Contexto Global para todas las plantillas (Jinja2)
@app.context_processor
def inject_global_vars():
    # KPIs Globales para el Header Premium (Command Center)
    kpis = {}
    if is_authenticated():
        try:
            with get_db_connection() as conn:
                kpis['kpi_total_activas'] = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND pc_name NOT IN ('PC Generica', 'Infraestructura')").fetchone()["c"]
                kpis['kpi_total_graveyard'] = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'False'").fetchone()["c"]
                kpis['kpi_win7'] = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND os_name LIKE %s AND pc_name NOT IN ('PC Generica', 'Infraestructura')", ("%Windows 7%",)).fetchone()["c"]
                kpis['kpi_alerta_ram'] = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND alerta_ram_baja = 1 AND pc_name NOT IN ('PC Generica', 'Infraestructura')").fetchone()["c"]
                
                # Impresoras
                net_pr = conn.execute("SELECT COUNT(*) as c FROM network_printers").fetchone()["c"]
                loc_pr = conn.execute("""
                    SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' 
                    AND (printer_model IS NOT NULL AND printer_model != '' AND printer_model != 'N/A' AND UPPER(printer_model) NOT LIKE '%%SIN IMPRESORA%%')
                    AND (printer_port IS NULL OR printer_port NOT LIKE '\\\\\\\\%%') AND alerta_impresora_red = 0
                """).fetchone()["c"]
                kpis['kpi_total_impresoras'] = net_pr + loc_pr
                
                kpis['kpi_tareas_hoy'] = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado = 'Hecha' AND DATE(completed_at) = CURDATE()").fetchone()["c"]
                kpis['kpi_total_pendientes'] = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado != 'Hecha'").fetchone()["c"]
        except Exception as e:
            print(f"Error in context processor KPIs: {e}")

    return {
        'app_version': APP_VERSION,
        'csrf_token': generate_csrf_token,
        'is_authenticated': is_authenticated(),
        'current_user': current_user(),
        'auth_mode_label': auth_mode_label(),
        'has_access': has_permission,
        'module_access_links': allowed_module_links(),
        'current_role_label': role_label(),
        'available_roles': available_roles(),
        'client_script_base_url': get_public_app_base_url(),
        'client_script_fallback_url': get_public_script_fallback_url(),
        **kpis 
    }


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

# Configuración y Migraciones iniciales
with app.app_context():
    init_db()
    run_all_migrations()
    default_admin_created = ensure_default_admin()
    if default_admin_created:
        print("Usuario inicial creado: administrador / tdg729tdg")
    
    def ensure_generic_pc():
        """Asegura que exista una PC genérica y una de Infraestructura para asignar tareas a hardware no inventariado."""
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

if __name__ == "__main__":
    sistema = platform.system()
    
    if sistema == "Windows":
        print("\n" + "="*64)
        print(" MODO DESARROLLO (Windows)")
        print(f" Servidor iniciado en hostname: {socket.gethostname()}")
        print("="*64)
        app.run(host="0.0.0.0", port=5000, debug=True)
    else:
        print("\n" + "="*64)
        print(" MODO PRODUCCIÓN (Linux)")
        
        # Intentar detectar certificados SSL
        cert_file = 'cert.pem'
        key_file = 'key.pem'
        
        # Si no existe cert.pem, probar con inventario-cert.crt (que vimos en el listado de archivos)
        if not os.path.exists(cert_file) and os.path.exists('inventario-cert.crt'):
            cert_file = 'inventario-cert.crt'
            print(f" - Usando certificado alternativo: {cert_file}")

        use_ssl = os.path.exists(cert_file) and os.path.exists(key_file)

        if use_ssl:
            print(" Iniciando servidor Flask con HTTPS y HTTP...")
            print(f" - HTTPS: https://0.0.0.0:5000 (Cert: {cert_file})")
            print(" - HTTP:  http://0.0.0.0:8080 (para móviles)")
            
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
        
        # El hilo principal corre el puerto 8080 (móviles/fallback)
        app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)
