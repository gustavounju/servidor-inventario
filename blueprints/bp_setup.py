from flask import Blueprint, request, send_file, render_template, redirect, url_for
from database.db_core import get_db_connection
from io import BytesIO
import re
import hashlib
from utils.runtime_urls import get_public_app_base_url, get_public_script_fallback_url

bp_setup = Blueprint('setup', __name__)


def _build_client_base_url():
    current_host = request.host.split(':')[0]
    return current_host, get_public_app_base_url()


def _rewrite_client_script(content):
    current_host, current_base_url = _build_client_base_url()

    replacements = [
        "__INVENTARIO_SERVER_URL__",
        "https://10.15.2.251:5000",
        "http://10.15.2.251:5000",
        "https://10.15.3.139:5000",
        "http://10.15.3.139:5000",
        "https://localhost:5000",
        "http://localhost:5000",
    ]

    modified_content = content
    for source in replacements:
        modified_content = modified_content.replace(source, current_base_url)

    modified_content = re.sub(r"https?://(?:\d{1,3}\.){3}\d{1,3}:5000", current_base_url, modified_content)
    
    import os
    api_token = os.environ.get("API_TOKEN", "super-secret-token")
    modified_content = modified_content.replace("__API_KEY__", api_token)
    
    return current_host, current_base_url, modified_content

def _get_secure_launcher_command(current_base_url, current_fallback_url):
    try:
        with open("inventario.ps1", "r", encoding="utf-8") as f:
            content = f.read()
        _, _, modified_content = _rewrite_client_script(content)
        sha256_hash = hashlib.sha256(modified_content.encode("utf-8")).hexdigest().upper()
        
        cmd = f"Set-ExecutionPolicy Bypass -Scope Process -Force; try {{ [Net.ServicePointManager]::SecurityProtocol = 3072 }} catch {{}}; try {{ Add-Type -TypeDefinition 'using System.Net; using System.Security.Cryptography.X509Certificates; public class T : ICertificatePolicy {{ public bool CheckValidationResult(ServicePoint s, X509Certificate c, WebRequest r, int p) {{ return true; }} }}' }} catch {{}}; [System.Net.ServicePointManager]::CertificatePolicy = New-Object T; $u='{current_base_url}/script'; $f=$env:TEMP+'\\inv_gold.ps1'; $h='{sha256_hash}'; try {{ (New-Object System.Net.WebClient).DownloadFile($u, $f) }} catch {{ Write-Host 'Fallo HTTPS...' -ForegroundColor Yellow; $u='{current_fallback_url}/script'; (New-Object System.Net.WebClient).DownloadFile($u, $f) }}; if (Test-Path $f) {{ $s=[System.IO.File]::OpenRead($f);$sha=New-Object System.Security.Cryptography.SHA256Managed;$hf=[BitConverter]::ToString($sha.ComputeHash($s)).Replace('-','');$s.Close(); if ($hf -eq $h) {{ Write-Host 'Firma Hash OK.' -ForegroundColor Green; & $f }} else {{ Write-Host 'Error de Seguridad: Hash invalido. MitM bloqueado.' -ForegroundColor Red }}; Remove-Item $f -Force }}"
        return cmd
    except Exception as e:
        return f"Write-Host 'Error interno de servidor generando comando: {e}' -ForegroundColor Red"

@bp_setup.route("/script")
def get_script():
    """Devuelve el contenido del script inventario.ps1 modificado con la IP actual para ser copiado."""
    try:
        with open("inventario.ps1", "r", encoding="utf-8") as f:
            content = f.read()
        _, _, modified_content = _rewrite_client_script(content)
        
        mem = BytesIO()
        mem.write(modified_content.encode("utf-8"))
        mem.seek(0)
        
        return send_file(mem, mimetype="text/plain", as_attachment=False, download_name="inventario.ps1")
    except Exception as e:
        return f"Error al leer script: {e}", 500

@bp_setup.route("/install")
def install_page():
    """Página simple para descargar los scripts del cliente."""
    current_host, current_base_url = _build_client_base_url()
    current_fallback_url = get_public_script_fallback_url()
    secure_cmd = _get_secure_launcher_command(current_base_url, current_fallback_url)
    
    return f"""
    <html>
    <head>
        <title>Instalar Inventario</title>
        <style>
            body {{ font-family: sans-serif; padding: 40px; max-width: 600px; margin: 0 auto; background: #f8f9fa; }}
            .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }}
            h1 {{ color: #0d6efd; margin-top: 0; }}
            a.btn {{ display: block; background: #0d6efd; color: white; padding: 15px; text-decoration: none; border-radius: 5px; margin: 10px 0; text-align: center; font-weight: bold; }}
            a.btn:hover {{ background: #0b5ed7; }}
            .step {{ margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>📥 Instalación Cliente</h1>
            <p>Sigue estos pasos en la PC que quieres inventariar (Windows 7/10/11):</p>
            
            <div class="step">
                <strong>1. Crea una carpeta</strong> en el Escritorio llamada <code>Inventario</code>.
            </div>

            <div class="step">
                <strong>2. Descarga los archivos</strong> en esa carpeta:
                <a href="/download/script" class="btn">📄 1. Descargar Script (inventario.ps1)</a>
                <a href="/download/launcher" class="btn">🚀 2. Descargar Ejecutable (ejecutar_inventario.bat)</a>
                <a href="/download/gpo" class="btn" style="background:#198754;">🏢 Descargar Script para GPO (inventario_gpo.ps1)</a>
            </div>

            <div class="step">
                <strong>3. Ejecuta</strong> el archivo <code>ejecutar_inventario.bat</code> (doble clic).
            </div>
            
            <hr>
            <p><small>Si Windows protege la PC, pulsa "Más información" -> "Ejecutar de todas formas".</small></p>
        </div>
        
        <div class="card" style="background-color: #e9ecef;">
            <h2 style="color: #495057; font-size: 1.2rem; margin-top:0;">⚡ Método Rápido (Seguro)</h2>
            <p style="font-size: 0.9rem; color: #6c757d;">Para técnicos: Ejecuta el inventario validando la integridad del código (SHA-256). Abre <b>PowerShell como Administrador</b>, copia este comando y presiona Enter:</p>
            <div id="cmdText" style="background: #212529; color: #20c20e; padding: 15px; border-radius: 5px; font-family: monospace; font-size: 0.85rem; word-break: break-all; margin-bottom: 15px;">
                {secure_cmd}
            </div>
            <button onclick="copyCommand()" style="background: #6c757d; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; font-size: 0.9rem;">Copiar Comando</button>
            <span id="copyMsg" style="color: green; margin-left: 10px; display: none;">¡Copiado!</span>
            <script>
                function copyCommand() {{
                    const cmd = document.getElementById('cmdText').innerText.trim();
                    if (navigator.clipboard && window.isSecureContext) {{
                        navigator.clipboard.writeText(cmd).then(showCopied);
                    }} else {{
                        // Fallback fallback for non-https 
                        let textArea = document.createElement("textarea");
                        textArea.value = cmd;
                        textArea.style.position = "fixed";
                        textArea.style.left = "-999999px";
                        textArea.style.top = "-999999px";
                        document.body.appendChild(textArea);
                        textArea.focus();
                        textArea.select();
                        try {{
                            document.execCommand('copy');
                            showCopied();
                        }} catch (err) {{
                            console.error('Fallback copy failed', err);
                        }}
                        textArea.remove();
                    }}
                }}
                function showCopied() {{
                    const msg = document.getElementById('copyMsg');
                    msg.style.display = 'inline';
                    setTimeout(() => msg.style.display = 'none', 2000);
                }}
            </script>
        </div>
    </body>
    </html>
    """

@bp_setup.route("/download/script")
def download_client_script():
    try:
        with open("inventario.ps1", "r", encoding="utf-8") as f:
            content = f.read()
        _, _, modified_content = _rewrite_client_script(content)
        
        mem = BytesIO()
        mem.write(modified_content.encode("utf-8"))
        mem.seek(0)
        
        return send_file(mem, as_attachment=True, download_name="inventario.ps1")
    except Exception as e:
        return f"Error: {e}", 404

@bp_setup.route("/download/launcher")
def download_client_launcher():
    try:
        return send_file("ejecutar_inventario.bat", as_attachment=True, download_name="ejecutar_inventario.bat")
    except Exception as e:
        return f"Error: {e}", 404

@bp_setup.route("/download/gpo")
def download_gpo_script():
    """Devuelve el script inventario_gpo.ps1 con las IPs corregidas para despliegue por GPO."""
    try:
        with open("deployment/inventario_gpo.ps1", "r", encoding="utf-8") as f:
            content = f.read()
        _, _, modified_content = _rewrite_client_script(content)
        
        mem = BytesIO()
        mem.write(modified_content.encode("utf-8"))
        mem.seek(0)
        
        return send_file(mem, as_attachment=True, download_name="inventario_gpo.ps1")
    except Exception as e:
        return f"Error: {e}", 404

@bp_setup.route("/download-cert")
def download_certificate():
    """Permite descargar el certificado SSL para instalarlo en dispositivos móviles."""
    try:
        return send_file(
            "cert.pem",
            as_attachment=True,
            download_name="inventario-cert.crt",
            mimetype="application/x-x509-ca-cert"
        )
    except Exception as e:
        return f"Error: {e}", 404

@bp_setup.route("/efemerides", methods=["GET"])
def view_efemerides():
    from datetime import datetime
    hoy_str = datetime.now().strftime("%m-%d")
    with get_db_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM efemerides ORDER BY (dia_mes >= %s) DESC, dia_mes ASC",
            (hoy_str,)
        ).fetchall()
        
        # Convert to dictionary to pre-evaluate is_past and is_today
        efemerides = []
        for r in rows:
            e_dict = dict(r)
            e_dict['is_past'] = e_dict['dia_mes'] < hoy_str
            e_dict['is_today'] = e_dict['dia_mes'] == hoy_str
            efemerides.append(e_dict)
            
        custom_msg_row = conn.execute("SELECT * FROM app_settings WHERE setting_key = 'custom_global_message'").fetchone()
        custom_message = {
            'active': bool(custom_msg_row['is_active']) if custom_msg_row else False,
            'text': custom_msg_row['setting_value'] if custom_msg_row else ""
        }
            
    return render_template("admin_efemerides.html", efemerides=efemerides, custom_message=custom_message)

from flask import jsonify

@bp_setup.route("/api/custom_message", methods=["POST"])
def update_custom_message():
    data = request.json
    text = data.get("text", "")
    is_active = 1 if data.get("is_active") else 0
    
    with get_db_connection() as conn:
        conn.execute(
            """
            INSERT INTO app_settings (setting_key, setting_value, is_active)
            VALUES ('custom_global_message', %s, %s)
            ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value), is_active = VALUES(is_active)
            """,
            (text, is_active)
        )
        conn.commit()
    return jsonify({"status": "success"})

@bp_setup.route("/efemerides/<int:ef_id>/toggle", methods=["POST"])
def toggle_efemeride(ef_id):
    with get_db_connection() as conn:
        conn.execute("UPDATE efemerides SET is_active = 0")
        conn.execute("UPDATE efemerides SET is_active = 1 WHERE id = %s", (ef_id,))
        conn.commit()
    return redirect(url_for('setup.view_efemerides'))

@bp_setup.route("/efemerides/turn_off", methods=["POST"])
def turn_off_efemerides():
    with get_db_connection() as conn:
        conn.execute("UPDATE efemerides SET is_active = 0")
        conn.commit()
    return redirect(url_for('setup.view_efemerides'))

@bp_setup.route("/efemerides/add", methods=["POST"])
def add_efemeride():
    dia_mes = request.form.get("dia_mes")
    titulo = request.form.get("titulo")
    descripcion = request.form.get("descripcion")
    icono = request.form.get("icono", "📅")
    if dia_mes and titulo:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO efemerides (dia_mes, titulo, descripcion, icono) VALUES (%s, %s, %s, %s)",
                (dia_mes, titulo, descripcion, icono)
            )
            conn.commit()
    return redirect(url_for('setup.view_efemerides'))

@bp_setup.route("/efemerides/<int:ef_id>/edit", methods=["POST"])
def edit_efemeride(ef_id):
    dia_mes = request.form.get("dia_mes")
    titulo = request.form.get("titulo")
    descripcion = request.form.get("descripcion")
    icono = request.form.get("icono", "📅")
    if dia_mes and titulo:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE efemerides SET dia_mes=%s, titulo=%s, descripcion=%s, icono=%s WHERE id=%s",
                (dia_mes, titulo, descripcion, icono, ef_id)
            )
            conn.commit()
    return redirect(url_for('setup.view_efemerides'))

@bp_setup.route("/efemerides/<int:ef_id>/delete", methods=["POST"])
def delete_efemeride(ef_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM efemerides WHERE id=%s", (ef_id,))
        conn.commit()
    return redirect(url_for('setup.view_efemerides'))

from utils.auth import is_superuser, current_user, login_required
from utils.crypto import encrypt_secret, decrypt_secret
from utils.settings import get_app_setting

@bp_setup.route("/config", methods=["GET"])
@login_required
def config_page():
    from flask import redirect, url_for
    # Ya no usamos setup_config.html separado, es un modal
    return redirect(url_for('dashboard.dashboard'))

@bp_setup.route("/config/api/get", methods=["GET"])
@login_required
def config_api_get():
    from flask import jsonify
    if not is_superuser():
        return jsonify({"status": "error", "message": "No autorizado"}), 403
        
    settings = {}
    try:
        with get_db_connection() as conn:
            for row in conn.execute("SELECT setting_key, setting_value FROM app_settings").fetchall():
                key = row['setting_key']
                val = row['setting_value']
                if key.endswith("PASSWORD") and val:
                    val = "********"
                settings[key] = val
        
        # Fallback para que los campos no se vean vacíos si sólo existen en el .env
        for key in ["AD_SERVER", "AD_BASE_DN", "AD_SYNC_USER", "AD_SYNC_PASSWORD"]:
            if not settings.get(key):
                val = get_app_setting(key, "")
                if key.endswith("PASSWORD") and val:
                    val = "********"
                settings[key] = val
                
        return jsonify({"status": "success", "data": settings})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_setup.route("/config/save", methods=["POST"])
@login_required
def save_config():
    if not is_superuser():
        return jsonify({"status": "error", "message": "Acceso denegado"}), 403
        
    data = request.json
    
    with get_db_connection() as conn:
        for key, value in data.items():
            if value is not None:
                str_value = str(value)
                if key.endswith("PASSWORD"):
                    if not str_value or str_value == "********":
                        continue
                    # If it's already encrypted (should not happen from form, but just in case)
                    if not str_value.startswith("ENC:"):
                        str_value = encrypt_secret(str_value)
                
                conn.execute(
                    """
                    INSERT INTO app_settings (setting_key, setting_value, is_active)
                    VALUES (%s, %s, 1)
                    ON DUPLICATE KEY UPDATE setting_value = VALUES(setting_value), is_active = 1
                    """,
                    (key, str_value)
                )
        conn.commit()
        
    return jsonify({"status": "success"})


@bp_setup.route("/config/test_ad", methods=["POST"])
@login_required
def test_ad_connection():
    if not is_superuser():
        return jsonify({"status": "error", "message": "Acceso denegado"}), 403
        
    data = request.json
    ad_server = data.get("AD_SERVER", "").strip()
    sync_user = data.get("AD_SYNC_USER", "").strip()
    sync_password = data.get("AD_SYNC_PASSWORD", "")
    base_dn = data.get("AD_BASE_DN", "").strip()

    if not ad_server or not sync_user or not sync_password or not base_dn:
        return jsonify({"status": "error", "message": "Todos los campos de AD (Servidor, Base DN, Usuario, Contraseña) son obligatorios para probar la conexión."})

    if sync_password == "********":
        sync_password = get_app_setting("AD_SYNC_PASSWORD", "")

    try:
        from ldap3 import Server, Connection, SIMPLE, NONE
    except ImportError:
        return jsonify({"status": "error", "message": "La librería ldap3 no está instalada."})

    from utils.auth import _ad_default_domain
    domain = _ad_default_domain()
    use_ssl = get_app_setting("AD_USE_SSL", "false").lower() == "true"
    connect_timeout = int(get_app_setting("AD_CONNECT_TIMEOUT", "5"))

    server = Server(ad_server, use_ssl=use_ssl, get_info=NONE, connect_timeout=connect_timeout)
    bind_user = f"{sync_user}@{domain}" if domain and "\\" not in sync_user and "@" not in sync_user else sync_user

    try:
        conn = Connection(server, user=bind_user, password=sync_password, authentication=SIMPLE, auto_bind=True)
        conn.unbind()
        return jsonify({"status": "success", "message": "Conexión y autenticación exitosas."})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Fallo la conexión: {str(e)}"})


@bp_setup.route("/descargas")
def descargas():
    import os
    import json
    from flask import current_app, render_template
    from database.db_core import get_db_connection
    
    # 1. Cargar el catálogo descriptivo
    catalog_path = os.path.join(current_app.root_path, "static", "downloads", "catalog.json")
    catalog = {}
    if os.path.exists(catalog_path):
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
        except Exception as e:
            current_app.logger.error(f"Error cargando catalog.json: {e}")
            
    # 2. Escanear el directorio físico y combinar con el catálogo
    downloads_dir = os.path.join(current_app.root_path, "static", "downloads")
    categories = list(catalog.keys())
    
    # Escanear el directorio físico (1 nivel de profundidad para subcarpetas)
    if os.path.exists(downloads_dir):
        for entry in os.scandir(downloads_dir):
            if entry.is_dir():
                if entry.name not in categories:
                    categories.append(entry.name)
                # Escanear subnivel
                for subentry in os.scandir(entry.path):
                    if subentry.is_dir():
                        subcat = f"{entry.name}/{subentry.name}"
                        if subcat not in categories:
                            categories.append(subcat)

    # Garantizar que existan las 4 básicas si no hay nada
    for cat in ["red", "drivers", "ofimatica", "sistema"]:
        if cat not in categories:
            categories.append(cat)
            
    categories.sort()
    
    # Creamos las carpetas físicas si no existen
    for cat in categories:
        try:
            os.makedirs(os.path.join(downloads_dir, cat.replace('/', os.sep)), exist_ok=True)
        except Exception as e:
            current_app.logger.warning(f"No se pudo crear la carpeta {cat}: {e}")
        
    available_files = {}
    for cat in categories:
        cat_dir = os.path.join(downloads_dir, cat.replace('/', os.sep))
        files = []
        if os.path.exists(cat_dir):
            for fname in os.listdir(cat_dir):
                if os.path.isfile(os.path.join(cat_dir, fname)) and fname != "catalog.json":
                    meta = None
                    if cat in catalog:
                        for item in catalog[cat]:
                            if item.get("filename") == fname:
                                meta = item
                                break
                    
                    if meta:
                        files.append({
                            "filename": fname,
                            "name": meta.get("name", fname),
                            "description": meta.get("description", "Sin descripción disponible.")
                        })
                    else:
                        files.append({
                            "filename": fname,
                            "name": fname,
                            "description": "Subido recientemente. Sin descripción de catálogo."
                        })
        if files:
            available_files[cat] = files
        
    # 3. Si el usuario es administrador, cargamos los logs de auditoría
    audit_logs = []
    from utils.auth import is_authenticated, current_user
    is_admin = is_authenticated() and (current_user().get('role') == 'administrador' or current_user().get('is_superuser'))
        
    if is_admin:
        try:
            with get_db_connection() as conn:
                audit_logs = conn.execute(
                    """
                    SELECT filename, category, ip_address, downloaded_at 
                    FROM software_download_logs 
                    ORDER BY downloaded_at DESC 
                    LIMIT 100
                    """
                ).fetchall()
        except Exception as e:
            current_app.logger.error(f"Error cargando logs de descargas: {e}")
            
    return render_template("descargas.html", files=available_files, audit_logs=audit_logs)


@bp_setup.route("/descargas/descargar/<path:category>/<filename>")
def download_file(category, filename):
    import os
    from flask import send_from_directory, request, current_app
    from database.db_core import get_db_connection
    
    # Prevenir Directory Traversal escapando '..'
    category = category.replace('..', '')
    filename = os.path.basename(filename)
    
    base_dir = os.path.join(current_app.root_path, "static", "downloads", category.replace('/', os.sep))
    file_path = os.path.join(base_dir, filename)
    if not os.path.exists(file_path):
        return "El archivo solicitado no existe en el servidor local.", 404
        
    ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    if ip_address and ',' in ip_address:
        ip_address = ip_address.split(',')[0].strip()
        
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO software_download_logs (filename, category, ip_address)
                VALUES (%s, %s, %s)
                """,
                (filename, category, ip_address)
            )
    except Exception as e:
        current_app.logger.error(f"Error al registrar descarga en DB: {e}")
        
    return send_from_directory(base_dir, filename, as_attachment=True)


@bp_setup.route("/api/upload_software", methods=["POST"])
def upload_software():
    from flask import request, jsonify, current_app
    import os
    import json
    from werkzeug.utils import secure_filename
    from utils.auth import is_authenticated, current_user

    if not is_authenticated() or not (current_user().get('role') == 'administrador' or current_user().get('is_superuser')):
        return jsonify({"status": "error", "message": "Acceso denegado. Se requieren permisos de administrador."}), 403

    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No se envió ningún archivo."}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "Nombre de archivo vacío."}), 400

    category = request.form.get('category', '').strip()
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not category:
        return jsonify({"status": "error", "message": "Categoría inválida."}), 400
        
    # Sanitizar categoría permitiendo anidamiento con '/'
    category = category.replace('..', '')

    filename = secure_filename(file.filename)
    if not filename:
        return jsonify({"status": "error", "message": "Nombre de archivo no válido."}), 400

    base_dir = os.path.join(current_app.root_path, "static", "downloads", category.replace('/', os.sep))
    os.makedirs(base_dir, exist_ok=True)
    file_path = os.path.join(base_dir, filename)

    try:
        file.save(file_path)
    except Exception as e:
        current_app.logger.error(f"Error guardando archivo: {e}")
        return jsonify({"status": "error", "message": f"Error al guardar el archivo: {str(e)}"}), 500

    # Actualizar catalog.json
    catalog_path = os.path.join(current_app.root_path, "static", "downloads", "catalog.json")
    catalog = {}
    if os.path.exists(catalog_path):
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
        except Exception as e:
            current_app.logger.error(f"Error leyendo catalog.json: {e}")
            catalog = {}

    if category not in catalog:
        catalog[category] = []

    # Verificar si ya existe para actualizarlo
    found = False
    for item in catalog[category]:
        if item.get("filename") == filename:
            item["name"] = name if name else filename
            item["description"] = description
            found = True
            break
            
    if not found:
        catalog[category].append({
            "filename": filename,
            "name": name if name else filename,
            "description": description
        })

    try:
        with open(catalog_path, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
    except Exception as e:
        current_app.logger.error(f"Error escribiendo catalog.json: {e}")
        return jsonify({"status": "error", "message": "Archivo subido pero no se pudo actualizar el catálogo."}), 500

    return jsonify({"status": "success", "message": f"Archivo '{filename}' subido correctamente al repositorio."})
