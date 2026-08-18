from flask import Blueprint, request, send_file, render_template, redirect, url_for, abort
from database.db_core import get_db_connection
from io import BytesIO
import os
import re
import hashlib
from utils.runtime_urls import get_public_app_base_url, get_public_script_fallback_url
from utils.auth import (
    current_user,
    generate_inventory_script_download_token,
    generate_inventory_submit_token,
    has_ephemeral_scope_token,
    is_authenticated,
    is_superuser,
    permission_required,
    login_required,
)

bp_setup = Blueprint('setup', __name__)


def _build_client_base_url():
    current_host = request.host.split(':')[0]
    return current_host, get_public_app_base_url()


def _script_access_metadata():
    user = current_user() if is_authenticated() else {}
    issued_for = request.args.get("pc_name", "").strip() or request.remote_addr or "desconocido"
    issued_by = (
        user.get("username")
        or user.get("display_name")
        or user.get("technician_name")
        or "launcher"
    )
    return issued_for, issued_by


def _resolve_script_submit_token(explicit_token=None):
    provided = (explicit_token or request.args.get("submit_token") or "").strip()
    if provided:
        if not has_ephemeral_scope_token(provided, "inventory:submit"):
            abort(403)
        return provided

    issued_for, issued_by = _script_access_metadata()
    return generate_inventory_submit_token(issued_for=issued_for, issued_by=issued_by)


def build_inventory_script_access_url():
    issued_for, issued_by = _script_access_metadata()
    download_token = generate_inventory_script_download_token(issued_for=issued_for, issued_by=issued_by)
    submit_token = generate_inventory_submit_token(issued_for=issued_for, issued_by=issued_by)
    return url_for("setup.get_script", download_token=download_token, submit_token=submit_token)


def _build_inventory_script_access():
    issued_for, issued_by = _script_access_metadata()
    download_token = generate_inventory_script_download_token(issued_for=issued_for, issued_by=issued_by)
    submit_token = generate_inventory_submit_token(issued_for=issued_for, issued_by=issued_by)
    relative_url = url_for("setup.get_script", download_token=download_token, submit_token=submit_token)
    return {
        "download_token": download_token,
        "submit_token": submit_token,
        "relative_url": relative_url,
    }


def get_quiet_inventory_command(current_base_url=None):
    current_base_url = current_base_url or get_public_app_base_url()
    access = _build_inventory_script_access()
    script_url = f"{current_base_url}{access['relative_url']}"

    with open("inventario.ps1", "r", encoding="utf-8") as f:
        content = f.read()
    _, _, modified_content = _rewrite_client_script(content, submit_token=access["submit_token"])
    sha256_hash = hashlib.sha256(modified_content.encode("utf-8")).hexdigest().upper()

    return (
        "Set-ExecutionPolicy Bypass -Scope Process -Force; "
        "try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}; "
        f"$u='{script_url}'; "
        "$f=Join-Path $env:TEMP 'inv_gold.ps1'; "
        f"$h='{sha256_hash}'; "
        "try { "
        "(New-Object System.Net.WebClient).DownloadFile($u, $f); "
        "$s=[System.IO.File]::OpenRead($f); "
        "$sha=New-Object System.Security.Cryptography.SHA256Managed; "
        "$hf=[BitConverter]::ToString($sha.ComputeHash($s)).Replace('-',''); "
        "$s.Close(); "
        "if ($hf -eq $h) { & $f } else { Write-Host 'Error de seguridad: hash de script invalido.' -ForegroundColor Red }; "
        "} catch { Write-Host 'Error al descargar o ejecutar el relevamiento.' -ForegroundColor Red } "
        "finally { Remove-Item $f -Force -ErrorAction SilentlyContinue }"
    )


def _has_interactive_script_access():
    if not is_authenticated():
        return False
    user = current_user()
    return bool(
        user.get("is_superuser")
        or user.get("permissions", {}).get("mobile")
        or user.get("permissions", {}).get("dashboard")
        or user.get("permissions", {}).get("manage_stock")
    )


def _authorize_script_download():
    if _has_interactive_script_access():
        return True

    download_token = (request.args.get("download_token") or "").strip()
    if has_ephemeral_scope_token(download_token, "inventory:download_script"):
        return True

    abort(403)


def _rewrite_client_script(content, submit_token=None):
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

    inventory_submit_token = _resolve_script_submit_token(explicit_token=submit_token)
    modified_content = modified_content.replace("__INVENTORY_BEARER_TOKEN__", inventory_submit_token)
    modified_content = modified_content.replace("__API_KEY__", inventory_submit_token)
    
    return current_host, current_base_url, modified_content


def _certificate_file_sha256():
    with open("cert.pem", "rb") as cert_file:
        return hashlib.sha256(cert_file.read()).hexdigest().upper()

def _get_secure_launcher_command(current_base_url, current_fallback_url):
    try:
        with open("inventario.ps1", "r", encoding="utf-8") as f:
            content = f.read()
        access = _build_inventory_script_access()
        submit_token = access["submit_token"]
        _, _, modified_content = _rewrite_client_script(content, submit_token=submit_token)
        sha256_hash = hashlib.sha256(modified_content.encode("utf-8")).hexdigest().upper()
        cert_sha256 = _certificate_file_sha256()
        download_url = f"{current_base_url}{access['relative_url']}"
        cert_url = f"{current_fallback_url}/download-cert"

        if current_base_url.startswith("http://"):
            cmd = (
                "Set-ExecutionPolicy Bypass -Scope Process -Force; "
                f"$scriptUrl='{download_url}'; "
                "$scriptFile=$env:TEMP+'\\inv_gold.ps1'; "
                f"$scriptHash='{sha256_hash}'; "
                "function Get-FileSha256($path) { $stream=[System.IO.File]::OpenRead($path); try { "
                "$sha=New-Object System.Security.Cryptography.SHA256Managed; "
                "return [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-','') "
                "} finally { $stream.Close() } }; "
                "try { (New-Object System.Net.WebClient).DownloadFile($scriptUrl, $scriptFile) } "
                "catch { Write-Host 'No se pudo descargar el script por HTTP.' -ForegroundColor Red; exit 1 }; "
                "if ((Get-FileSha256 $scriptFile) -eq $scriptHash) { "
                "Write-Host 'Hash OK en modo compatibilidad.' -ForegroundColor Yellow; & $scriptFile } "
                "else { Write-Host 'Error de seguridad: hash del script invalido.' -ForegroundColor Red }; "
                "Remove-Item $scriptFile -Force -ErrorAction SilentlyContinue"
            )
            return cmd

        cmd = (
            "Set-ExecutionPolicy Bypass -Scope Process -Force; "
            "try { [Net.ServicePointManager]::SecurityProtocol = 3072 } catch {}; "
            f"$certUrl='{cert_url}'; $scriptUrl='{download_url}'; "
            "$certFile=$env:TEMP+'\\inventario-cert.crt'; $scriptFile=$env:TEMP+'\\inv_gold.ps1'; "
            f"$certHash='{cert_sha256}'; $scriptHash='{sha256_hash}'; "
            "function Get-FileSha256($path) { $stream=[System.IO.File]::OpenRead($path); try { "
            "$sha=New-Object System.Security.Cryptography.SHA256Managed; "
            "return [BitConverter]::ToString($sha.ComputeHash($stream)).Replace('-','') "
            "} finally { $stream.Close() } }; "
            "try { (New-Object System.Net.WebClient).DownloadFile($certUrl, $certFile) } "
            "catch { Write-Host 'No se pudo descargar el certificado del servidor.' -ForegroundColor Red; exit 1 }; "
            "if ((Get-FileSha256 $certFile) -ne $certHash) { "
            "Write-Host 'Error de seguridad: certificado inesperado.' -ForegroundColor Red; "
            "Remove-Item $certFile -Force -ErrorAction SilentlyContinue; exit 1 }; "
            "try { Import-Certificate -FilePath $certFile -CertStoreLocation Cert:\\CurrentUser\\Root | Out-Null } "
            "catch { try { certutil -user -addstore Root $certFile | Out-Null } catch { "
            "Write-Host 'No se pudo instalar el certificado.' -ForegroundColor Red; exit 1 } }; "
            "try { (New-Object System.Net.WebClient).DownloadFile($scriptUrl, $scriptFile) } "
            "catch { Write-Host 'Fallo la descarga segura del script por HTTPS.' -ForegroundColor Red; exit 1 }; "
            "if ((Get-FileSha256 $scriptFile) -eq $scriptHash) { "
            "Write-Host 'Firma Hash OK.' -ForegroundColor Green; & $scriptFile } "
            "else { Write-Host 'Error de seguridad: hash del script invalido.' -ForegroundColor Red }; "
            "Remove-Item $certFile -Force -ErrorAction SilentlyContinue; "
            "Remove-Item $scriptFile -Force -ErrorAction SilentlyContinue"
        )
        return cmd
    except Exception as e:
        return f"Write-Host 'Error interno de servidor generando comando: {e}' -ForegroundColor Red"


@bp_setup.route("/qr-code")
def qr_code_image():
    payload = (request.args.get("data") or "").strip()
    size = max(80, min(int(request.args.get("size", "180")), 512))
    if not payload:
        abort(400)

    try:
        import qrcode
    except ImportError as exc:
        return f"Dependencia faltante para QR local: {exc}", 500

    qr = qrcode.QRCode(
        box_size=max(2, size // 32),
        border=2,
    )
    qr.add_data(payload)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    output = BytesIO()
    image.save(output, format="PNG")
    output.seek(0)
    return send_file(output, mimetype="image/png", max_age=31536000)

@bp_setup.route("/script")
def get_script():
    """Devuelve el contenido del script inventario.ps1 modificado con la IP actual para ser copiado."""
    _authorize_script_download()
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
@permission_required("mobile")
def install_page():
    """Página simple para descargar los scripts del cliente."""
    current_host, current_base_url = _build_client_base_url()
    current_fallback_url = get_public_script_fallback_url()
    secure_cmd = _get_secure_launcher_command(current_base_url, current_fallback_url)
    raw_script_url = build_inventory_script_access_url()
    
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
            <h1>📥 Inventario Manual</h1>
            <p>Este es el método recomendado para su entorno. No requiere instalar nada ni abrir PowerShell como administrador.</p>
            
            <div class="step">
                <strong>1. En la PC a inventariar</strong>, abre PowerShell normal.
            </div>

            <div class="step">
                <strong>2. Abre el script seguro</strong> desde esta misma sesión:
                <a href="{raw_script_url}" class="btn">📋 Abrir Script Para Copiar y Pegar</a>
            </div>

            <div class="step">
                <strong>3. Copia todo el contenido</strong>, pégalo en PowerShell y presiona Enter.
            </div>
            
            <div class="step">
                <strong>4. El script se autoejecuta</strong> y envía los datos al servidor central usando un token efímero solo para inventario.
            </div>
        </div>
        
        <div class="card" style="background-color: #e9ecef;">
            <h2 style="color: #495057; font-size: 1.2rem; margin-top:0;">⚡ Método Alternativo</h2>
            <p style="font-size: 0.9rem; color: #6c757d;">Solo si necesitas automatizar la descarga. Puede requerir PowerShell con más permisos según la PC. El método principal para ustedes sigue siendo copiar y pegar el script manual.</p>
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

        <div class="card">
            <h2 style="color: #495057; font-size: 1.2rem; margin-top:0;">Archivos Legacy</h2>
            <p style="font-size: 0.9rem; color: #6c757d;">Estos accesos quedan disponibles solo por compatibilidad o tareas puntuales.</p>
            <a href="/download/script" class="btn">📄 Descargar inventario.ps1</a>
            <a href="/download/launcher" class="btn">🚀 Descargar ejecutar_inventario.bat</a>
            <a href="/download/gpo" class="btn" style="background:#198754;">🏢 Descargar Script para GPO</a>
        </div>
    </body>
    </html>
    """

@bp_setup.route("/download/script")
@permission_required("mobile")
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
@permission_required("mobile")
def download_client_launcher():
    try:
        return send_file("ejecutar_inventario.bat", as_attachment=True, download_name="ejecutar_inventario.bat")
    except Exception as e:
        return f"Error: {e}", 404

@bp_setup.route("/download/gpo")
@permission_required("mobile")
def download_gpo_script():
    """Devuelve el script inventario_gpo.ps1 con las IPs corregidas para despliegue por GPO."""
    try:
        if os.environ.get("ALLOW_LEGACY_INVENTORY_STATIC_TOKEN", "false").strip().lower() != "true":
            return (
                "El script GPO legado está deshabilitado. "
                "Activa ALLOW_LEGACY_INVENTORY_STATIC_TOKEN=true solo si necesitas compatibilidad temporal.",
                503,
            )
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
        
        # Fallback inteligente desde .env / os.environ / valores por defecto del sistema
        defaults = {
            "DB_HOST": os.environ.get("DB_HOST", "10.15.0.62"),
            "DB_PORT": os.environ.get("DB_PORT", "3306"),
            "DB_NAME": os.environ.get("DB_NAME", "inventario_prod"),
            "DB_USER": os.environ.get("DB_USER", "inventario_user"),
            "DB_PASSWORD": os.environ.get("DB_PASS") or os.environ.get("DB_PASSWORD", ""),
            "AD_SERVER": os.environ.get("AD_SERVER", "10.15.0.62"),
            "AD_BASE_DN": os.environ.get("AD_BASE_DN", "DC=poderjudicial,DC=local"),
            "AD_SYNC_USER": os.environ.get("AD_SYNC_USER", "admin_ad"),
            "AD_SYNC_PASSWORD": os.environ.get("AD_SYNC_PASSWORD", "")
        }

        for key, default_val in defaults.items():
            if not settings.get(key):
                val = get_app_setting(key, default_val)
                if not val:
                    val = default_val
                if (key.endswith("PASSWORD") or key == "DB_PASS") and val:
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
            
    return render_template("descargas.html", files=available_files, audit_logs=audit_logs, is_admin=is_admin)


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


@bp_setup.route("/descargas/tree")
def descargas_tree():
    """Devuelve el árbol de archivos disponibles para descargar como JSON.
    Público (no requiere login) — solo lista metadatos, no descarga nada.
    """
    import os
    import json
    from flask import current_app, jsonify

    catalog_path = os.path.join(current_app.root_path, "static", "downloads", "catalog.json")
    catalog = {}
    if os.path.exists(catalog_path):
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
        except Exception:
            pass

    downloads_dir = os.path.join(current_app.root_path, "static", "downloads")
    
    # Construir árbol de categorías raíz
    root_categories = ["drivers", "red", "ofimatica", "sistema"]
    tree = {}

    for root_cat in root_categories:
        cat_dir = os.path.join(downloads_dir, root_cat)
        node = {"type": "folder", "name": root_cat, "children": {}, "files": []}

        if os.path.exists(cat_dir):
            for entry in os.scandir(cat_dir):
                if entry.is_dir():
                    # Subcarpeta
                    subcat_key = f"{root_cat}/{entry.name}"
                    sub_node = {"type": "folder", "name": entry.name, "children": {}, "files": []}
                    for fname in os.listdir(entry.path):
                        fpath = os.path.join(entry.path, fname)
                        if os.path.isfile(fpath) and not fname.startswith(".") and fname.lower() not in ["catalog.json", "desktop.ini", "thumbs.db"]:
                            size_bytes = os.path.getsize(fpath)
                            meta_list = catalog.get(subcat_key, [])
                            label = fname
                            desc = ""
                            for m in meta_list:
                                if m.get("filename") == fname:
                                    label = m.get("name", fname)
                                    desc = m.get("description", "")
                                    break
                            sub_node["files"].append({
                                "filename": fname,
                                "label": label,
                                "description": desc,
                                "size": size_bytes,
                                "download_url": f"/descargas/descargar/{subcat_key}/{fname}"
                            })
                    node["children"][entry.name] = sub_node
                elif entry.is_file() and not entry.name.startswith(".") and entry.name.lower() not in ["catalog.json", "desktop.ini", "thumbs.db"]:
                    size_bytes = entry.stat().st_size
                    meta_list = catalog.get(root_cat, [])
                    label = entry.name
                    desc = ""
                    for m in meta_list:
                        if m.get("filename") == entry.name:
                            label = m.get("name", entry.name)
                            desc = m.get("description", "")
                            break
                    node["files"].append({
                        "filename": entry.name,
                        "label": label,
                        "description": desc,
                        "size": size_bytes,
                        "download_url": f"/descargas/descargar/{root_cat}/{entry.name}"
                    })

        tree[root_cat] = node

    return jsonify(tree)


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
        return jsonify({"status": "error", "message": f"Archivo subido pero no se pudo actualizar el catálogo. Error: {str(e)}"}), 500

    return jsonify({"status": "success", "message": f"Archivo '{filename}' subido correctamente al repositorio."})

@bp_setup.route("/api/delete_software", methods=["POST"])
def delete_software():
    from flask import request, jsonify, current_app
    import os
    import json
    from utils.auth import is_authenticated, current_user

    if not is_authenticated() or not (current_user().get('role') == 'administrador' or current_user().get('is_superuser')):
        return jsonify({"status": "error", "message": "Acceso denegado. Se requieren permisos de administrador."}), 403

    category = request.form.get('category', '').strip()
    filename = request.form.get('filename', '').strip()

    if not category or not filename:
        return jsonify({"status": "error", "message": "Parámetros incompletos."}), 400

    # 1. Borrar el archivo físico
    base_dir = os.path.join(current_app.root_path, "static", "downloads", category.replace('/', os.sep))
    file_path = os.path.join(base_dir, filename)
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        current_app.logger.error(f"Error borrando archivo físico {file_path}: {e}")
        return jsonify({"status": "error", "message": "No se pudo borrar el archivo físico."}), 500

    # 2. Actualizar el catalog.json
    catalog_path = os.path.join(current_app.root_path, "static", "downloads", "catalog.json")
    if os.path.exists(catalog_path):
        try:
            with open(catalog_path, "r", encoding="utf-8") as f:
                catalog = json.load(f)
                
            if category in catalog:
                catalog[category] = [item for item in catalog[category] if item.get("filename") != filename]
                
                # Eliminar la categoría entera si queda vacía
                if not catalog[category]:
                    del catalog[category]
                    
            with open(catalog_path, "w", encoding="utf-8") as f:
                json.dump(catalog, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            current_app.logger.error(f"Error actualizando catalog.json tras borrado: {e}")
            return jsonify({"status": "error", "message": "Archivo borrado pero falló la actualización del catálogo."}), 500

    return jsonify({"status": "success", "message": f"Archivo '{filename}' borrado correctamente."})
