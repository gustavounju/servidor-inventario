
import os
import shutil
import subprocess
from datetime import datetime
from flask import Blueprint, render_template, jsonify, send_file, request, Response
from utils.auth import is_superuser, login_required
from database.db_core import get_db_connection
from utils.settings import get_app_setting

bp_maintenance = Blueprint('maintenance', __name__)

@bp_maintenance.route("/maintenance", methods=["GET"])
@login_required
def maintenance_index():
    if not is_superuser():
        from flask import redirect, url_for
        return redirect(url_for('dashboard.dashboard'))
    return redirect(url_for('dashboard.dashboard'))

@bp_maintenance.route("/maintenance/api/health", methods=["GET"])
@login_required
def api_health():
    if not is_superuser():
        return jsonify({"status": "error", "message": "Acceso denegado"}), 403
    
    health = {
        "db": {"status": "unknown"},
        "ad": {"status": "unknown"},
        "disk": {"status": "unknown", "free_gb": 0, "total_gb": 0, "percent_free": 0}
    }

    # DB Check
    try:
        with get_db_connection() as conn:
            conn.execute("SELECT 1")
        health["db"]["status"] = "ok"
    except Exception as e:
        health["db"]["status"] = "error"
        health["db"]["error"] = str(e)

    # Disk Check
    try:
        total, used, free = shutil.disk_usage(os.path.abspath(os.sep))
        total_gb = total // (2**30)
        free_gb = free // (2**30)
        percent = round((free / total) * 100, 1) if total > 0 else 0
        health["disk"] = {
            "status": "ok" if percent > 10 else "warning",
            "free_gb": free_gb,
            "total_gb": total_gb,
            "percent_free": percent
        }
    except Exception as e:
        health["disk"]["status"] = "error"

    # AD Check
    ad_server = get_app_setting("AD_SERVER", "").strip()
    if ad_server:
        try:
            from ldap3 import Server, Connection, NONE
            use_ssl = get_app_setting("AD_USE_SSL", "false").lower() == "true"
            connect_timeout = int(get_app_setting("AD_CONNECT_TIMEOUT", "2"))
            server = Server(ad_server, use_ssl=use_ssl, get_info=NONE, connect_timeout=connect_timeout)
            # Try anonymous bind just to check connectivity
            conn = Connection(server, auto_bind=True, receive_timeout=connect_timeout)
            conn.unbind()
            health["ad"]["status"] = "ok"
        except Exception as e:
            health["ad"]["status"] = "error"
            health["ad"]["error"] = "No se puede alcanzar el servidor AD"
    else:
        health["ad"]["status"] = "disabled"
        health["ad"]["error"] = "No configurado"

    try:
        health["maintenance_mode"] = get_app_setting("MAINTENANCE_MODE", "0")
    except:
        health["maintenance_mode"] = "0"

    return jsonify(health)

@bp_maintenance.route("/maintenance/api/logs", methods=["GET"])
@login_required
def api_logs():
    if not is_superuser():
        return jsonify({"status": "error", "message": "Acceso denegado"}), 403
    
    log_path = os.path.join("logs", "inventario.json.log")
    lines = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                # Read last 100 lines
                all_lines = f.readlines()
                lines = all_lines[-100:]
        except Exception as e:
            lines = [f"Error al leer logs: {str(e)}"]
    else:
        lines = ["No se encontró el archivo de log."]
    
    return jsonify({"lines": lines})

@bp_maintenance.route("/maintenance/api/sync_ad", methods=["POST"])
@login_required
def api_sync_ad():
    if not is_superuser():
        return jsonify({"status": "error", "message": "Acceso denegado"}), 403
    
    from services.ad_sync_service import sync_ad_users
    try:
        result = sync_ad_users()
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@bp_maintenance.route("/maintenance/api/sync_ad_pcs", methods=["POST"])
@login_required
def api_sync_ad_pcs():
    if not is_superuser():
        return jsonify({"status": "error", "message": "Acceso denegado"}), 403
    
    from services.ad_sync_service import sync_computers_from_ad
    try:
        result = sync_computers_from_ad()
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@bp_maintenance.route("/maintenance/api/clear_cache", methods=["POST"])
@login_required
def api_clear_cache():
    if not is_superuser():
        return jsonify({"status": "error", "message": "Acceso denegado"}), 403
    
    try:
        from servidor import invalidate_global_cache
        invalidate_global_cache()
        return jsonify({"status": "success", "message": "Caché limpiada correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@bp_maintenance.route("/maintenance/backup_db", methods=["GET"])
@login_required
def backup_db():
    if not is_superuser():
        from flask import redirect, url_for
        return redirect(url_for('dashboard.dashboard'))
        
    db_user = os.environ.get("DB_USER", "root")
    db_pass = os.environ.get("DB_PASS", "")
    db_host = os.environ.get("DB_HOST", "127.0.0.1")
    db_name = os.environ.get("DB_NAME", "inventario_prod")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"backup_{db_name}_{timestamp}.sql"
    
    # mysqldump command
    cmd = ["mysqldump", "-h", db_host, "-u", db_user]
    if db_pass:
        cmd.append(f"-p{db_pass}")
    cmd.append(db_name)
    
    def generate():
        try:
            # We use subprocess.Popen to stream the output directly to the response
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            while True:
                chunk = process.stdout.read(4096)
                if not chunk:
                    break
                yield chunk
            
            process.stdout.close()
            process.wait()
            if process.returncode != 0:
                err = process.stderr.read().decode('utf-8')
                yield f"\n\n-- ERROR: Fallo al generar el dump: {err}\n".encode('utf-8')
        except FileNotFoundError:
            yield b"-- ERROR: El comando mysqldump no se encuentra en el PATH. Esta funcion requiere que las herramientas de MySQL esten instaladas."
        except Exception as e:
            yield f"\n\n-- ERROR INESPERADO: {str(e)}\n".encode('utf-8')

    return Response(
        generate(),
        mimetype='application/sql',
        headers={'Content-Disposition': f'attachment;filename={filename}'}
    )

@bp_maintenance.route("/maintenance/api/toggle_maintenance", methods=["POST"])
@login_required
def api_toggle_maintenance():
    if not is_superuser():
        return jsonify({"status": "error", "message": "Acceso denegado"}), 403
    
    data = request.json
    active = data.get("active", False)
    val = "1" if active else "0"
    
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO app_settings (setting_key, setting_value, is_active)
                VALUES ('MAINTENANCE_MODE', %s, 1)
                ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value), is_active = 1
                """,
                (val,)
            )
            conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})
