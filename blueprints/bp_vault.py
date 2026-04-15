import os
import json
import time
from flask import Blueprint, render_template, request, session, redirect, url_for, send_from_directory, flash
from utils.auth import current_user, is_authenticated

bp_vault = Blueprint("vault", __name__)

# Directorio base para los archivos privados
VAULT_BASE = os.path.join("uploads", "vault")
DEFAULT_LIMIT_MB = 300

# Usuarios autorizados para el Vault
VAULT_ALLOWED_USERS = ['gmurad', 'dquiros']
# Carpeta compartida única para estos usuarios
VAULT_SHARED_FOLDER = "shared_admin_vault"

def is_vault_authorized(username):
    """Verifica si el usuario actual está en la lista de permitidos."""
    return username in VAULT_ALLOWED_USERS

def get_vault_path():
    """Obtiene o crea la carpeta compartida para el vault."""
    path = os.path.join(VAULT_BASE, VAULT_SHARED_FOLDER)
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
    
    # Migración: Si existe la carpeta vieja de 'gmurad', mover archivos a la compartida
    old_path = os.path.join(VAULT_BASE, "gmurad")
    if os.path.exists(old_path) and old_path != path:
        try:
            for item in os.listdir(old_path):
                s = os.path.join(old_path, item)
                d = os.path.join(path, item)
                if not os.path.exists(d):
                    os.rename(s, d)
            # Intentar borrar carpeta vieja si está vacía
            if not os.listdir(old_path):
                os.rmdir(old_path)
        except:
            pass
            
    return path

def get_vault_config():
    """Lee la configuración de espacio compartido (límite)."""
    path = get_vault_path()
    config_file = os.path.join(path, ".config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                return json.load(f)
        except:
            pass
    return {"limit_mb": DEFAULT_LIMIT_MB}

def save_vault_config(config):
    """Guarda la configuración de espacio compartido."""
    path = get_vault_path()
    config_file = os.path.join(path, ".config.json")
    with open(config_file, "w") as f:
        json.dump(config, f)

def get_folder_size(path):
    """Calcula el tamaño total en bytes de los archivos en la carpeta (excluyendo ocultos)."""
    total = 0
    if not os.path.exists(path):
        return 0
    for entry in os.scandir(path):
        if entry.is_file() and not entry.name.startswith("."):
            total += entry.stat().st_size
    return total

@bp_vault.route("/recursos_internos")
def vault_index():
    if not is_authenticated():
        return redirect(url_for("auth.login"))
    
    user = current_user()
    if not is_vault_authorized(user.get('username')):
        return redirect(url_for("dashboard.dashboard"))
    
    path = get_vault_path()
    config = get_vault_config()
    
    files = []
    if os.path.exists(path):
        for entry in os.scandir(path):
            if entry.is_file() and not entry.name.startswith("."):
                files.append({
                    "name": entry.name,
                    "size": entry.stat().st_size,
                    "mtime": entry.stat().st_mtime,
                    "date": time.strftime('%d/%m/%Y %H:%M', time.localtime(entry.stat().st_mtime))
                })
    
    # Ordenar por fecha (más reciente arriba)
    files.sort(key=lambda x: x['mtime'], reverse=True)
    
    used_bytes = get_folder_size(path)
    limit_mb = config.get('limit_mb', DEFAULT_LIMIT_MB)
    limit_bytes = limit_mb * 1024 * 1024
    
    pct_used = round((used_bytes / limit_bytes) * 100, 1) if limit_bytes > 0 else 0
    
    return render_template("vault.html", 
                           files=files, 
                           used_bytes=used_bytes, 
                           limit_bytes=limit_bytes, 
                           limit_mb=limit_mb,
                           pct_used=pct_used)

@bp_vault.route("/recursos_internos/upload", methods=["POST"])
def upload_file():
    user = current_user()
    if not is_authenticated() or not is_vault_authorized(user.get('username')):
        return redirect(url_for("dashboard.dashboard"))
    
    if 'file' not in request.files:
        flash("No se seleccionó ningún archivo.", "warning")
        return redirect(url_for("vault.vault_index"))
    
    file = request.files['file']
    if file.filename == '':
        flash("Nombre de archivo vacío.", "warning")
        return redirect(url_for("vault.vault_index"))
    
    path = get_vault_path()
    config = get_vault_config()
    
    current_size = get_folder_size(path)
    limit_bytes = config.get('limit_mb', DEFAULT_LIMIT_MB) * 1024 * 1024
    
    file_path = os.path.join(path, file.filename)
    file.save(file_path)
    
    if get_folder_size(path) > limit_bytes:
        os.remove(file_path)
        flash("Error: El archivo excede el límite de espacio compartido disponible.", "danger")
    else:
        flash(f"Archivo '{file.filename}' subido correctamente.", "success")
        
    return redirect(url_for("vault.vault_index"))

@bp_vault.route("/recursos_internos/download/<path:filename>")
def download_file(filename):
    user = current_user()
    if not is_authenticated() or not is_vault_authorized(user.get('username')):
        return redirect(url_for("dashboard.dashboard"))
    
    path = get_vault_path()
    return send_from_directory(path, filename, as_attachment=True)

@bp_vault.route("/recursos_internos/delete/<path:filename>")
def delete_file(filename):
    user = current_user()
    if not is_authenticated() or not is_vault_authorized(user.get('username')):
        return redirect(url_for("dashboard.dashboard"))
    
    path = get_vault_path()
    file_path = os.path.join(path, filename)
    
    if os.path.exists(file_path) and os.path.isfile(file_path):
        os.remove(file_path)
        flash(f"Archivo '{filename}' eliminado.", "info")
    
    return redirect(url_for("vault.vault_index"))

@bp_vault.route("/recursos_internos/expand", methods=["POST"])
def expand_storage():
    user = current_user()
    if not is_authenticated() or not is_vault_authorized(user.get('username')):
        return redirect(url_for("dashboard.dashboard"))
    
    config = get_vault_config()
    config['limit_mb'] = config.get('limit_mb', DEFAULT_LIMIT_MB) + 300
    save_vault_config(config)
    
    flash(f"Espacio compartido ampliado a {config['limit_mb']} MB.", "success")
    return redirect(url_for("vault.vault_index"))
