from flask import Flask
import os
import threading
import platform
import socket

# Base de datos y Migraciones
from database.db_core import init_db, get_db_connection
from database.migrations import run_all_migrations

# Utils e IA
from utils.constants import UPLOAD_FOLDER, LOG_FOLDER
from services.ai_assistant import train_ai_model

# Blueprints
from blueprints.bp_dashboard import bp_dashboard
from blueprints.bp_api import bp_api
from blueprints.bp_stock import bp_stock
from blueprints.bp_setup import bp_setup
from blueprints.bp_tasks import bp_tasks
from blueprints.bp_mobile import bp_mobile

# Inicializar Flask
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

# Filtros para Jinja (si queda alguno que estuviéramos usando, aunque los que se usaban ya están resueltos o no declarados como filters globales en servidor.py original excepto quizas datetime_es, pero lo importabamos donde hiciera falta).
from services.reporting import format_datetime_es
app.jinja_env.filters['datetime_es'] = format_datetime_es

# Configuración y Migraciones iniciales
with app.app_context():
    init_db()
    run_all_migrations()
    
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
        print(" Iniciando servidor Flask con HTTPS y HTTP...")
        # Cambiar el host si es necesario
        print(" - HTTPS: https://0.0.0.0:5000 (para PCs)")
        print(" - HTTP:  http://0.0.0.0:8080 (para móviles)")
        print("="*64)
        
        def run_https():
            app.run(host="0.0.0.0", port=5000, debug=False, 
                    ssl_context=('cert.pem', 'key.pem'), use_reloader=False)
        
        def run_http():
            app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)
        
        https_thread = threading.Thread(target=run_https, daemon=True)
        https_thread.start()
        
        run_http()
