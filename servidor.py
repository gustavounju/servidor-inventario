from flask import Flask, send_from_directory
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
from utils.constants import UPLOAD_FOLDER, LOG_FOLDER, APP_VERSION, list_fuero_mapping_rows
APP_VERSION = "3.0.1"
from services.ai_assistant import train_ai_model

# Blueprints
from blueprints.bp_dashboard import bp_dashboard
from blueprints.bp_api import bp_api
from blueprints.bp_stock import bp_stock
from blueprints.bp_setup import bp_setup
from blueprints.bp_infrastructure import bp_infrastructure
from blueprints.bp_tasks import bp_tasks
from blueprints.bp_mobile import bp_mobile
from blueprints.bp_tecnicos import bp_tecnicos
from blueprints.bp_auth import bp_auth
from blueprints.bp_vault import bp_vault
from blueprints.bp_users import bp_users
from blueprints.bp_maps import bp_maps
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
app.register_blueprint(bp_tecnicos)
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
    from utils.auth import list_app_users, list_technician_users
    
    # KPIs Globales para el Header Premium (Command Center)
    kpis = {}
    extra_data = {
        'ad_users_list': [],
        'fueros': {},
        'technicians': [],
        'app_users_list': [],
        'all_pcs': [],
        'kpi_usuarios_pendientes': 0
    }
    
    if is_authenticated():
        try:
            with get_db_connection() as conn:
                kpis['kpi_total_activas'] = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND UPPER(pc_name) NOT IN ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA')").fetchone()["c"]
                kpis['kpi_total_graveyard'] = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'False'").fetchone()["c"]
                kpis['kpi_win7'] = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND os_name LIKE %s AND UPPER(pc_name) NOT IN ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA')", ("%Windows 7%",)).fetchone()["c"]
                kpis['kpi_alerta_ram'] = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND alerta_ram_baja = 1 AND UPPER(pc_name) NOT IN ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA')").fetchone()["c"]
                
                # Impresoras: Solo contar las que están en el catálogo oficial (Infraestructura)
                kpis['kpi_total_impresoras_oficial'] = conn.execute("SELECT COUNT(*) as c FROM network_printers").fetchone()["c"]
                
                kpis['kpi_tareas_hoy'] = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado = 'Hecha' AND DATE(completed_at) = CURDATE()").fetchone()["c"]
                kpis['kpi_total_pendientes'] = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado != 'Hecha'").fetchone()["c"]
                
                extra_data['kpi_usuarios_pendientes'] = conn.execute("SELECT COUNT(*) as c FROM app_users WHERE is_active = 0").fetchone()["c"]

                fueros_rows = conn.execute("SELECT DISTINCT fuero FROM pcs WHERE fuero IS NOT NULL AND fuero != '' AND fuero != 'Desconocido' ORDER BY fuero").fetchall()
                known_fueros = {row['fuero']: row['fuero'] for row in fueros_rows}
                for item in list_fuero_mapping_rows():
                    known_fueros.setdefault(item['label'], item['label'])
                extra_data['fueros'] = dict(sorted(known_fueros.items(), key=lambda item: item[0].lower()))

                # Extra Data for Shared Modals
                # 1. Obtener usuarios del sistema actuales
                sys_users = list_app_users()
                extra_data['app_users_list'] = sys_users
                sys_usernames = {str(u['username']).strip().lower() for u in sys_users}

                # 2. Obtener usuarios potenciales de AD
                # 2. Obtener usuarios oficiales del directorio (AD_USERS)
                # Ya no incluimos UNION con PCS para evitar "basura" de nombres detectados por scripts
                ad_users_query = """
                    SELECT LOWER(TRIM(username)) as username, real_name, phone, 1 as is_official
                    FROM ad_users
                    ORDER BY real_name
                """
                all_ad_raw = [dict(row) for row in conn.execute(ad_users_query).fetchall()]

                
                # 3. Filtrar y Deduplicar: SI el usuario ya existe en el sistema superior, NO sale en el directorio
                # Deduplicación para casos donde un registro histórico (PCS) coincide con uno oficial (ad_users)
                seen_usernames = {} # username -> user_obj
                ad_usernames = set() # usernames que sabemos que son de AD
                
                for u in all_ad_raw:
                    uname = str(u['username']).strip().lower()
                    if u['is_official']:
                        ad_usernames.add(uname)

                    if uname in sys_usernames:
                        continue
                    
                    # Si ya vimos este username
                    if uname in seen_usernames:
                        # Prioridad al oficial
                        if u['is_official'] and not seen_usernames[uname]['is_official']:
                            seen_usernames[uname] = u
                        continue
                    
                    seen_usernames[uname] = u
                
                directorio_filtrado = list(seen_usernames.values())
                directorio_filtrado.sort(key=lambda x: str(x['real_name']).lower())
                
                extra_data['directorio_filtrado'] = directorio_filtrado
                extra_data['ad_usernames'] = ad_usernames
                
                # Debug log
                import datetime
                now = datetime.datetime.now().strftime("%H:%M:%S")
                print(f"DEBUG [{now}]: AppUsers={len(sys_usernames)} Directorio={len(directorio_filtrado)} AD_Total={len(ad_usernames)}")

                extra_data['all_pcs'] = [dict(row) for row in conn.execute(
                    "SELECT pc_name, fuero, last_user FROM pcs WHERE is_active = 'True' ORDER BY pc_name"
                ).fetchall()]
                
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
        **kpis,
        **extra_data
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

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 
                               'icon-192.png', mimetype='image/png')

# Configuracin y Migraciones iniciales
with app.app_context():
    init_db()
    run_all_migrations()
    default_admin_created = ensure_default_admin()
    if default_admin_created:
        print("Usuario inicial creado: administrador / tdg729tdg")
    
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
        app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)
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
