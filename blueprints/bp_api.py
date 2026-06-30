import json
import traceback
import os
from flask import Blueprint, request, jsonify, redirect, url_for
import json
import datetime
import os
import re

from database.db_core import get_db_connection
from utils.constants import detect_fuero
from utils.extensions import limiter

bp_api = Blueprint('api', __name__)


def _normalize_printer_endpoint(value):
    raw = (value or "").strip()
    if not raw or raw.upper() == "N/A":
        return ""

    raw = re.sub(r"\s+\((RED|LOCAL)\)$", "", raw, flags=re.IGNORECASE).strip()
    raw = re.sub(r"\s+\[DESCONECTADA\]$", "", raw, flags=re.IGNORECASE).strip()

    if raw.startswith("\\"):
        raw = re.sub(r"\\+", r"\\", raw)
        parts = [part.strip().lower() for part in raw.split("\\") if part.strip()]
        if len(parts) >= 2:
            return f"\\\\{parts[0]}\\{parts[1]}"
        if len(parts) == 1:
            return f"\\\\{parts[0]}"
        return ""

    token = raw.split(" ")[0].strip().lower()
    token = token.rstrip("\\/")
    return token


def _normalize_printer_model(value):
    model = (value or "").strip().lower()
    if not model or model == "n/a":
        return ""

    model = re.sub(r"\bseries\b", " ", model)
    model = re.sub(r"\bprinter\b", " ", model)
    model = re.sub(r"\bclass driver\b", " ", model)
    model = re.sub(r"\bpcl\d*\b", " ", model)
    model = re.sub(r"\s+", " ", model)
    return model.strip()


def _build_printer_match_key(model, port):
    normalized_model = _normalize_printer_model(model)
    normalized_port = _normalize_printer_endpoint(port)
    if normalized_model and normalized_port:
        return f"{normalized_model}|{normalized_port}"
    return ""

def process_inventory_data(data):
    from utils.constants import clean_hex_string
    debug_logs = []
    pc_name = data.get("PC_Nombre")
    if not pc_name: raise ValueError("Falta PC_Nombre en el JSON")

    last_user = data.get("Usuario_Actual", "N/A")
    fecha_raw = data.get("Fecha_Reporte", str(datetime.datetime.now()))
    last_report = fecha_raw["value"] if isinstance(fecha_raw, dict) else str(fecha_raw)

    sistema = data.get("Sistema", {})
    os_name = sistema.get("OsName", "N/A")
    processor = sistema.get("Procesador", "N/A")
    ram_gb = sistema.get("RAM (GB)", 0)
    office_version = sistema.get("Office", "N/A")

    red = data.get("Red", [])
    ip_address = red[0].get("IPAddress") if red else "N/A"
    mac_address = red[0].get("MACAddress") if red else "N/A"

    ram_detalles = data.get("RAM_Detalles", "N/A")
    disk_models = data.get("Disk_Models", "N/A")
    disk_speeds_rpm = data.get("Disk_Speeds_RPM", "N/A")
    motherboard_model = data.get("Motherboard_Model", "N/A")
    printer_model = data.get("Printer_Model", "N/A")
    printer_port = data.get("Printer_Port", "N/A")
    printer_sn = clean_hex_string(data.get("Printer_SN", "N/A"))
        
    # ----------------------------------------------------
    # TRADUCCIÓN DE SIGLAS EDID DE MONITORES
    # ----------------------------------------------------
    raw_monitors = data.get("Monitors", "N/A")
    edid_dict = {
        "SAM": "Samsung",
        "GSM": "LG",
        "DEL": "Dell",
        "PHL": "Philips",
        "ACR": "Acer",
        "AOC": "AOC",
        "VSC": "ViewSonic",
        "HPQ": "HP",
        "HPN": "HP",
        "LEN": "Lenovo",
        "BNQ": "BenQ",
        "ASU": "Asus",
        "SNY": "Sony"
    }
    
    if raw_monitors and raw_monitors != "N/A":
        # Divide por si hay múltiples monitores (ej. "SAM | DEL")
        parts = [p.strip() for p in raw_monitors.split("|")]
        translated_parts = []
        for p in parts:
            # Reemplaza si el string completo es la sigla, o si empieza con la sigla
            for sigla, nombre in edid_dict.items():
                if sigla in p:
                    p = p.replace(sigla, nombre)
            translated_parts.append(p)
        monitors = " | ".join(translated_parts)
    else:
        monitors = raw_monitors
    # ----------------------------------------------------

    ping_ms = "N/A"
    ping_loss_pct = "N/A"

    try: ram_val = float(ram_gb)
    except Exception: ram_val = 0.0
    alerta_ram_baja = 1 if ram_val < 8 else 0

    pm = (printer_model or "").upper()
    pp = (printer_port or "").upper()
    
    esta_desconectada = "DESCONECTADA" in pp
    es_local = pp.startswith("USB") or pp.startswith("LPT")
    sin_modelo = pm in ("", "N/A", "NINGUNA", "SIN IMPRESORA", "GENERICO", "GENERIC")

    # Si la impresora está desconectada y es local, tratarla como SIN IMPRESORA
    # (Solo si realmente no hay un modelo válido o es puramente genérica)
    if esta_desconectada and es_local and sin_modelo:
        printer_model = "SIN IMPRESORA"
        printer_port = "N/A"
        data["Printer_Model"] = "SIN IMPRESORA"
        data["Printer_Port"] = "N/A"
        pm = "SIN IMPRESORA"
        pp = "N/A"
        esta_desconectada = False
        sin_modelo = True

    es_virtual = ("PDF" in pm) or ("XPS" in pm) or ("ONENOTE" in pm)
    es_compartida_unc = pp.startswith("\\\\")
    es_red_directa = ("IP_" in pp) or ("WSD" in pp) or ("." in pp and not es_compartida_unc)
    
    # --- MEJORA: Herencia de Serial para Impresoras Compartidas ---
    if es_compartida_unc and (printer_sn == "N/A" or not printer_sn):
        try:
            # Extraer el nombre del host (ej: \\PC01\Printer -> PC01 o \\10.x.x.x\Printer)
            parts = [p for p in printer_port.split("\\") if p]
            if len(parts) >= 2:
                # El host es la primera parte después de los backslashes iniciales
                host_raw = parts[0].upper()
                # Limpiar FQDN (ej: PC01.dominio.local -> PC01) para el LIKE
                host_ref = host_raw.split(".")[0].strip()
                
                with get_db_connection() as conn:
                    if host_ref:
                        # Buscamos la PC host por nombre (LIKE para manejar NetBIOS/FQDN) o por IP
                        # Priorizamos coincidencia exacta o por IP
                        host_info = conn.execute(
                            """
                            SELECT printer_sn, printer_model, pc_name 
                            FROM pcs 
                            WHERE (pc_name = %s OR pc_name LIKE %s OR ip_address = %s) 
                            AND printer_sn IS NOT NULL AND printer_sn != 'N/A' AND printer_sn != '' 
                            ORDER BY (pc_name = %s) DESC, last_report DESC 
                            LIMIT 1
                            """, 
                            (host_ref, f"{host_ref}%", host_raw, host_ref)
                        ).fetchone()
                        
                        if host_info and host_info['printer_sn'] and host_info['printer_sn'] != 'N/A':
                            printer_sn = host_info['printer_sn']
                            # Si el cliente no reportó modelo, heredamos el del host
                            if not printer_model or printer_model == "N/A":
                                printer_model = host_info['printer_model']
                            print(f"[HERENCIA] Serial {printer_sn} heredado del host {host_info['pc_name']} para {pc_name}")
                        else:
                            print(f"[HERENCIA] No se encontró serial válido en el host {host_ref} para la PC {pc_name}")
        except Exception as e:
            print(f"[HERENCIA] Error procesando herencia para {pc_name}: {e}")
    # -------------------------------------------------------------

    if esta_desconectada and es_local and not sin_modelo:
        alerta_impresora_red = 1
        alerta_sin_impresora = 1
    else:
        if sin_modelo or es_virtual or esta_desconectada: 
            alerta_sin_impresora = 1
        else: 
            alerta_sin_impresora = 0

        # Solo alertar si es red DIRECTA (IP/WSD). Las compartidas se manejan como local/link
        alerta_impresora_red = 1 if (not sin_modelo and not es_virtual and es_red_directa) else 0

    salud = data.get("Salud", {})
    alerta_disco = 0
    discos_smart = salud.get("Discos_SMART", [])
    for d in discos_smart:
        status = str(d.get("Status", "OK")).upper()
        if status != "OK":
            alerta_disco = 1
            break
            
    if alerta_disco == 0:
        discos_espacio = salud.get("Discos_Espacio", [])
        for v in discos_espacio:
            try:
                free_gb = float(v.get("FreeGB", 100))
                if free_gb < 5.0:
                    alerta_disco = 1
                    break
            except: pass

    alerta_uptime = 0
    uptime_dias = salud.get("Uptime_Dias", 0)
    try:
        if float(uptime_dias) > 15.0: alerta_uptime = 1
    except: pass

    full_json = json.dumps(data, ensure_ascii=False)
    fuero_reportado = str(data.get("Fuero") or data.get("fuero") or "").strip()
    fuero_detectado = fuero_reportado or detect_fuero(pc_name)

    # Initial states for new calculations
    alerta_nombre_duplicado = 0
    reactivado = False
    
    with get_db_connection() as conn:
        current_pc = conn.execute("SELECT * FROM pcs WHERE pc_name = %s", (pc_name,)).fetchone()
        if current_pc:
            # Check for reactivation from Cementerio
            if current_pc.get("is_active") == 0 or current_pc.get("is_active") == False or str(current_pc.get("is_active")) == "False":
                reactivado = True
                conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                             (pc_name, "Estado de PC", "Cementerio (Baja)", "Reactivado (Activo)", "SISTEMA", "INVENTARIO_AUTOMATICO", request.remote_addr))

            # Deduplicate check: if hardware (motherboard & processor) drastically changed, it's likely another physical machine
            old_mb = str(current_pc.get("motherboard_model", "")).strip()
            old_proc = str(current_pc.get("processor", "")).strip()
            
            # Solo si el equipo anterior tenia datos utiles
            if old_mb and old_mb != "N/A" and old_proc and old_proc != "N/A":
                # Si ambos difieren completamente (no son substrings)
                if (motherboard_model != "N/A" and motherboard_model != old_mb) and \
                   (processor != "N/A" and processor != old_proc):
                    alerta_nombre_duplicado = 1
            
            fields_to_check = {
                "ram_gb": str(current_pc.get("ram_gb", "")), "disk_models": str(current_pc.get("disk_models", "")),
                "processor": str(current_pc.get("processor", "")), "os_name": str(current_pc.get("os_name", "")), "ip_address": str(current_pc.get("ip_address", ""))
            }
            new_values_map = {
                "ram_gb": str(ram_gb), "disk_models": str(disk_models), "processor": str(processor), "os_name": str(os_name), "ip_address": str(ip_address), "mac_address": str(mac_address)
            }
            for field, old_val in fields_to_check.items():
                new_val = new_values_map.get(field, "N/A")
                if old_val.strip() != new_val.strip():
                    conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                                 (pc_name, field, old_val, new_val, "SISTEMA", "INVENTARIO_AUTOMATICO", request.remote_addr))


    # --- OBTENER VALORES ANTIGUOS PARA LIMPIEZA ---
    old_printer_sn = "N/A"
    with get_db_connection() as conn:
        old_pc = conn.execute("SELECT printer_sn FROM pcs WHERE pc_name = %s", (pc_name,)).fetchone()
        if old_pc: old_printer_sn = old_pc["printer_sn"] or "N/A"

    sql = """
    INSERT INTO pcs (pc_name, fuero, os_name, processor, ram_gb, ip_address, mac_address, last_user, last_report, ram_detalles, disk_models, disk_speeds_rpm, motherboard_model, monitors, printer_model, printer_port, printer_sn, office_version, ping_ms, ping_loss_pct, alerta_ram_baja, alerta_sin_impresora, alerta_impresora_red, alerta_disco, alerta_uptime, alerta_nombre_duplicado, is_active, full_json_data)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 1, %s)
    ON DUPLICATE KEY UPDATE
        fuero=VALUES(fuero), os_name=VALUES(os_name), processor=VALUES(processor), ram_gb=VALUES(ram_gb), ip_address=VALUES(ip_address), mac_address=VALUES(mac_address), last_user=VALUES(last_user), last_report=VALUES(last_report), ram_detalles=VALUES(ram_detalles), disk_models=VALUES(disk_models), disk_speeds_rpm=VALUES(disk_speeds_rpm), motherboard_model=VALUES(motherboard_model), monitors=VALUES(monitors), printer_model=VALUES(printer_model), printer_port=VALUES(printer_port), printer_sn=VALUES(printer_sn), office_version=VALUES(office_version), ping_ms=VALUES(ping_ms), ping_loss_pct=VALUES(ping_loss_pct), alerta_ram_baja=VALUES(alerta_ram_baja), alerta_sin_impresora=VALUES(alerta_sin_impresora), alerta_impresora_red=VALUES(alerta_impresora_red), alerta_disco=VALUES(alerta_disco), alerta_uptime=VALUES(alerta_uptime), alerta_nombre_duplicado=VALUES(alerta_nombre_duplicado), is_active=1, full_json_data=VALUES(full_json_data)
    """
    
    with get_db_connection() as conn:
        conn.execute(sql, (pc_name, fuero_detectado, os_name, processor, ram_gb, ip_address, mac_address, last_user, last_report, ram_detalles, disk_models, disk_speeds_rpm, motherboard_model, monitors, printer_model, printer_port, printer_sn, office_version, ping_ms, ping_loss_pct, alerta_ram_baja, alerta_sin_impresora, alerta_impresora_red, alerta_disco, alerta_uptime, alerta_nombre_duplicado, full_json))
        
        # Sincronización Total: El servidor es un reflejo del script de la PC
        # 1. Limpiamos todas las asignaciones previas para este equipo
        conn.execute("DELETE FROM pc_network_printers WHERE pc_name = %s", (pc_name,))
        
        # 2. Re-vinculamos únicamente si el script detecta una impresora que está en el catálogo
        if (alerta_impresora_red == 1 or printer_sn != 'N/A') and (printer_port != 'N/A' or printer_sn != 'N/A'):
            clean_ip = None
            if printer_port != 'N/A':
                # Intentar extraer IP de: "10.15.0.1 (Port)" o "\\10.15.0.1\Printer"
                if printer_port.startswith('\\\\'):
                    parts = printer_port.split('\\')
                    if len(parts) >= 3:
                        maybe_host = parts[2]
                        if '.' in maybe_host: clean_ip = maybe_host
                else:
                    clean_ip = printer_port.split(' ')[0]
            
            # Buscar en el catálogo (Primero por SN, luego por IP)
            known_printer = None
            if printer_sn != 'N/A':
                known_printer = conn.execute("SELECT id FROM network_printers WHERE serial_number = %s", (printer_sn,)).fetchone()
            
            if not known_printer and clean_ip and '.' in clean_ip:
                known_printer = conn.execute("SELECT id FROM network_printers WHERE ip_address = %s", (clean_ip,)).fetchone()
            
            if known_printer:
                printer_id = known_printer['id']
                # 3. Vincular la actual
                conn.execute("INSERT INTO pc_network_printers (pc_name, printer_id) VALUES (%s, %s)", (pc_name, printer_id))
                conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                             (pc_name, 'AUTO_SYNC_PRINTER', 'Catalog', printer_sn if printer_sn != 'N/A' else clean_ip, "SISTEMA", "AUTO_SYNC", request.remote_addr))
        
        elif alerta_sin_impresora == 1:
            # 1. LIMPIEZA DEL CATÁLOGO (Stock de infraestructura)
            if old_printer_sn and old_printer_sn != "N/A":
                # Borrado total si el SN coincide (ya sabemos que esta PC reportó no encontrarla)
                cursor = conn.execute("DELETE FROM network_printers WHERE serial_number = %s", (old_printer_sn,))
                print(f"[DEBUG] Catálogo limpiado. SN: {old_printer_sn}. Filas: {cursor.rowcount}")

            # 2. Limpieza de Asignaciones Internas
            conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                         (pc_name, 'AUTO_CLEAN_PRINTER', 'Assigned', 'None', "SISTEMA", "AUTO_SYNC", request.remote_addr))
                
            # 3. LIMPIEZA EN CASCADA (Misión: Clientes huérfanos)
            host_pattern = f"%\\\\\\\\{pc_name.upper()}\\\\%"
            clients = conn.execute("SELECT pc_name FROM pcs WHERE UPPER(printer_port) LIKE %s", (host_pattern,)).fetchall()
            if clients:
                for c in clients:
                    client_name = c["pc_name"]
                    conn.execute("DELETE FROM pc_network_printers WHERE pc_name = %s", (client_name,))
                    conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                                 (client_name, 'CASCADE_UNASSIGN', 'Host Offline', pc_name, "SISTEMA", "CASCADE_ACTION", request.remote_addr))

        # --- PROPAGACIÓN EN CASCADA (SI SOY HOST) ---
        # Si esta PC tiene un serial de impresora USB/Local válido, buscar clientes que impriman aquí
        if printer_sn and printer_sn != "N/A" and printer_sn != "" and printer_sn != "Desconocido":
            # Patrones de puerto que buscaría un cliente: \\MiHost\ o \\MiHost.dominio\ o \\MiIP\
            patterns = []
            if pc_name:
                # Nombre NetBIOS
                patterns.append(f"%\\\\\\\\{pc_name.upper()}\\\\%")
                # Posible prefijo de FQDN (ej: \\EQINT... )
                patterns.append(f"%\\\\\\\\{pc_name.upper()}.%")
                
            if ip_address and ip_address != "N/A":
                patterns.append(f"%\\\\\\\\{ip_address}\\\\%")
            
            total_cascada = 0
            for pat in patterns:
                updated = conn.execute(
                    """
                    UPDATE pcs SET printer_sn = %s 
                    WHERE (printer_sn IS NULL OR printer_sn = 'N/A' OR printer_sn = '' OR printer_sn = 'Desconocido')
                    AND UPPER(printer_port) LIKE %s
                    """,
                    (printer_sn, pat)
                )
                total_cascada += updated.rowcount
            
            if total_cascada > 0:
                print(f"[CASCADA] Se propagó serial {printer_sn} a {total_cascada} cliente(s) del host {pc_name}")
            
        # --- PROCESAR IMPRESORAS MULTIPLES (Printers_Extra) ---
        printers_extra = data.get("Printers_Extra", [])
        if printers_extra:
            # Limpiamos todo el buffer de esta PC
            conn.execute("DELETE FROM pc_detected_printers WHERE pc_name = %s", (pc_name,))
            for p in printers_extra:
                pm_extra = p.get("Model", "N/A")
                pp_extra = p.get("Port", "N/A")
                psn_extra = clean_hex_string(p.get("SN", "N/A"))
                
                # Auto-filtrado de impresoras virtuales (PDF, XPS, OneNote, Fax)
                pm_upper = pm_extra.upper()
                is_virtual_extra = ("PDF" in pm_upper) or ("XPS" in pm_upper) or ("ONENOTE" in pm_upper) or ("FAX" in pm_upper) or ("SEND TO" in pm_upper) or ("MICROSOFT" in pm_upper and "DOCUMENT" in pm_upper)
                
                # Insertar en la nueva tabla de impresoras secundarias
                # Las virtuales se insertan como ignoradas automáticamente
                conn.execute(
                    """
                    INSERT INTO pc_detected_printers (pc_name, printer_model, printer_port, printer_sn, is_ignored)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (pc_name, pm_extra, pp_extra, psn_extra, 1 if is_virtual_extra else 0)
                )

        conn.commit()


    print(f"Inventario guardado / actualizado: {pc_name}")
    return pc_name


@bp_api.route("/submit_inventory", methods=["POST"])
@limiter.limit("60 per minute")
def receive_inventory():
    api_token = os.environ.get("API_TOKEN", "super-secret-token")
    auth_header = request.headers.get("Authorization", "")
    token_query = request.args.get("api_key", "")
    
    if auth_header != f"Bearer {api_token}" and token_query != api_token:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
        
    try:
        raw_data = request.get_data()
        try:
            try: data = json.loads(raw_data.decode("utf-8"))
            except Exception: data = json.loads(raw_data.decode("utf-16"))
        except Exception as e:
            raise ValueError(f"JSON inválido o error de codificación: {e}")
            
        process_inventory_data(data)
        return jsonify({"status": "success"}), 200
    except ValueError as ve:
        return jsonify({"status": "error", "message": str(ve)}), 400
    except Exception as exc:
        print(f"Error procesando inventario: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 500

@bp_api.route("/upload_manual", methods=["POST"])
def upload_manual_inventory():
    if 'file' not in request.files: return redirect(url_for('dashboard.dashboard'))
    file = request.files['file']
    if file.filename == '': return redirect(url_for('dashboard.dashboard'))
    if not file.filename.lower().endswith('.json'):
        from flask import flash
        flash("Solo se admiten archivos .json", "error")
        return redirect(url_for('dashboard.dashboard'))
        
    if file:
        try:
            content = file.read()
            if len(content) > 2 * 1024 * 1024:
                from flask import flash
                flash("Archivo demasiado grande (max 2MB)", "error")
                return redirect(url_for('dashboard.dashboard'))
            try: data = json.loads(content.decode("utf-8"))
            except: data = json.loads(content.decode("utf-16"))
            pc_name = process_inventory_data(data)
            print(f"Manual upload success for {pc_name}")
        except Exception as e: print(f"Error en carga manual: {e}")
        return redirect(url_for('dashboard.dashboard'))

@bp_api.route("/health", methods=["GET"])
@limiter.limit("60 per minute")
def health():
    try:
        with get_db_connection() as conn:
            conn.execute("SELECT 1")
        return {"status": "ok", "db_ok": True}, 200
    except Exception:
        return {"status": "error", "db_ok": False}, 500

@bp_api.route("/api/security/<string:pc_name>")
def api_security(pc_name):
    """Devuelve las conexiones de red activas (snapshot) desde el JSON completo."""
    try:
        with get_db_connection() as conn:
            row = conn.execute("SELECT full_json_data FROM pcs WHERE pc_name = %s", (pc_name,)).fetchone()
            if not row or not row["full_json_data"]:
                return jsonify({"status": "error", "message": "PC no encontrada o sin datos"}), 404
            
            data = json.loads(row["full_json_data"])
            conns = data.get("Conexiones", [])
            sec_extra = data.get("Seguridad_Extra", {"Antivirus": "Descargando...", "Startup": []})
            return jsonify({"status": "success", "data": conns, "seguridad_extra": sec_extra})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_api.route("/api/health/<string:pc_name>")
def api_health(pc_name):
    """Devuelve el diagnóstico unificado del equipo desde el JSON completo."""
    try:
        with get_db_connection() as conn:
            row = conn.execute("SELECT full_json_data FROM pcs WHERE pc_name = %s", (pc_name,)).fetchone()
            if not row or not row["full_json_data"]:
                return jsonify({"status": "error", "message": "PC no encontrada o sin datos"}), 404
            
            data = json.loads(row["full_json_data"])
            health = data.get("Salud", {})
            sistema = data.get("Sistema", {})
            conns = data.get("Conexiones", [])
            sec_extra = data.get("Seguridad_Extra", {"Antivirus": "Descargando...", "Startup": []})
            return jsonify({
                "status": "success", 
                "data": health,
                "conexiones": conns,
                "seguridad_extra": sec_extra,
                "extra": {
                    "office": sistema.get("Office", "N/A"),
                    "os": sistema.get("OsName", "N/A")
                }
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
@bp_api.route("/api/pc_printer/<string:pc_ref>")
def api_pc_printer(pc_ref):
    """Devuelve el serial de la impresora de una PC dada (por nombre o IP)."""
    try:
        pc_ref = pc_ref.upper()
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT printer_sn, printer_model, printer_port FROM pcs WHERE pc_name = %s OR ip_address = %s LIMIT 1", 
                (pc_ref, pc_ref)
            ).fetchone()
            if not row:
                return jsonify({"status": "error", "message": "PC no encontrada"}), 404
            
            return jsonify({
                "status": "success", 
                "printer_sn": row["printer_sn"] or "N/A",
                "printer_model": row["printer_model"] or "N/A",
                "printer_port": row["printer_port"] or "N/A"
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_api.route("/api/detected_printers")
def api_detected_printers():
    """Devuelve la lista de impresoras detectadas (locales) y registradas. Opcionalmente filtra por pc_name."""
    pc_filter = request.args.get('pc_name', '').strip()
    try:
        with get_db_connection() as conn:
            # 1. Impresoras registradas en Infraestructura
            net_printers = conn.execute("SELECT * FROM network_printers ORDER BY brand_model").fetchall()
            
            # 2. Impresoras detectadas en PCs — con filtro opcional por PC
            base_query = """
                SELECT 
                    dp.pc_name, 
                    dp.printer_model, 
                    dp.printer_sn, 
                    dp.printer_port, 
                    pcs.last_report, 
                    pcs.fuero,
                    dp.id AS detect_id,
                    pcs.printer_model AS primary_printer_model,
                    pcs.printer_port AS primary_printer_port,
                    pcs.printer_sn AS primary_printer_sn
                FROM pc_detected_printers dp
                INNER JOIN pcs ON pcs.pc_name = dp.pc_name
                WHERE pcs.is_active = 1
                  AND dp.is_ignored = 0
                  AND (dp.printer_model IS NOT NULL AND dp.printer_model != '' AND dp.printer_model != 'N/A' AND UPPER(dp.printer_model) NOT LIKE '%%SIN IMPRESORA%%')
                  AND (dp.printer_port IS NULL OR dp.printer_port NOT LIKE '\\\\\\\\%%') 
            """
            if pc_filter:
                base_query += " AND dp.pc_name = %s ORDER BY dp.pc_name"
                detected_rows = conn.execute(base_query, (pc_filter,)).fetchall()
            else:
                base_query += " ORDER BY dp.pc_name"
                detected_rows = conn.execute(base_query).fetchall()

            main_query = """
                SELECT
                    pcs.pc_name,
                    pcs.printer_model,
                    pcs.printer_sn,
                    pcs.printer_port,
                    pcs.last_report,
                    pcs.fuero,
                    NULL AS detect_id
                FROM pcs
                WHERE pcs.is_active = 1
                  AND (pcs.printer_model IS NOT NULL AND pcs.printer_model != '' AND pcs.printer_model != 'N/A' AND UPPER(pcs.printer_model) NOT LIKE '%%SIN IMPRESORA%%')
            """
            if pc_filter:
                main_query += " AND pcs.pc_name = %s ORDER BY pcs.pc_name"
                main_rows = conn.execute(main_query, (pc_filter,)).fetchall()
            else:
                main_query += " ORDER BY pcs.pc_name"
                main_rows = conn.execute(main_query).fetchall()

            assigned_rows = conn.execute("""
                SELECT pnp.pc_name, np.serial_number, np.ip_address, np.brand_model
                FROM pc_network_printers pnp
                JOIN network_printers np ON np.id = pnp.printer_id
            """).fetchall()

            catalog_serials = {
                (p["serial_number"] or "").strip().upper()
                for p in net_printers
                if p.get("serial_number") and str(p["serial_number"]).strip().upper() != "N/A"
            }
            catalog_ports = {
                _normalize_printer_endpoint(p.get("ip_address"))
                for p in net_printers
                if _normalize_printer_endpoint(p.get("ip_address"))
            }

            assigned_by_pc = {}
            for row in assigned_rows:
                pc_name = row["pc_name"]
                assigned_by_pc.setdefault(pc_name, {"serials": set(), "ports": set(), "keys": set()})
                serial = (row.get("serial_number") or "").strip().upper()
                port = _normalize_printer_endpoint(row.get("ip_address"))
                key = _build_printer_match_key(row.get("brand_model"), row.get("ip_address"))
                if serial and serial != "N/A":
                    assigned_by_pc[pc_name]["serials"].add(serial)
                if port:
                    assigned_by_pc[pc_name]["ports"].add(port)
                if key:
                    assigned_by_pc[pc_name]["keys"].add(key)

            filtered_detected = []
            seen_detected_keys = set()
            for row in list(main_rows) + list(detected_rows):
                row_dict = dict(row)
                detect_serial = (row_dict.get("printer_sn") or "").strip().upper()
                detect_port = _normalize_printer_endpoint(row_dict.get("printer_port"))
                detect_key = _build_printer_match_key(row_dict.get("printer_model"), row_dict.get("printer_port"))
                pc_name = row_dict["pc_name"]

                if detect_serial and detect_serial != "N/A" and detect_serial in catalog_serials:
                    continue
                if detect_port and detect_port in catalog_ports:
                    continue

                assigned = assigned_by_pc.get(pc_name, {"serials": set(), "ports": set(), "keys": set()})
                if detect_serial and detect_serial != "N/A" and detect_serial in assigned["serials"]:
                    continue
                if detect_port and detect_port in assigned["ports"]:
                    continue
                if detect_key and detect_key in assigned["keys"]:
                    continue

                dedupe_key = (pc_name, detect_serial or "", detect_key or "", detect_port or "")
                if dedupe_key in seen_detected_keys:
                    continue
                seen_detected_keys.add(dedupe_key)

                filtered_detected.append({
                    "pc_name": row_dict["pc_name"],
                    "printer_model": row_dict["printer_model"],
                    "printer_sn": row_dict["printer_sn"],
                    "printer_port": row_dict["printer_port"],
                    "last_report": row_dict["last_report"],
                    "fuero": row_dict["fuero"],
                    "detect_id": row_dict["detect_id"],
                })
            
            return jsonify({
                "status": "success",
                "network_printers": [dict(p) for p in net_printers],
                "detected_printers": filtered_detected
            })
    except Exception as e:
        print(f"Error en api_detected_printers: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_api.route("/api/ignore_detected_printer/<int:detect_id>", methods=["POST"])
def ignore_detected_printer(detect_id):
    try:
        with get_db_connection() as conn:
            conn.execute("UPDATE pc_detected_printers SET is_ignored = 1 WHERE id = %s", (detect_id,))
            return jsonify({"status": "success", "message": "Impresora ignorada correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

from flask import current_app
from werkzeug.utils import secure_filename
import uuid
from utils.auth import current_technician_identity

@bp_api.route("/api/racks", methods=["GET"])
def api_get_racks():
    try:
        with get_db_connection() as conn:
            racks = conn.execute("SELECT * FROM racks ORDER BY nombre").fetchall()
        return jsonify({"status": "success", "data": [dict(r) for r in racks]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_api.route("/api/racks/status", methods=["GET"])
@limiter.limit("30 per minute")
def api_get_racks_status():
    try:
        with get_db_connection() as conn:
            racks = conn.execute("SELECT * FROM racks ORDER BY nombre").fetchall()
            status_data = []
            for rack in racks:
                last_audit = conn.execute(
                    "SELECT * FROM rack_audits WHERE rack_id = %s ORDER BY timestamp DESC LIMIT 1", 
                    (rack["id"],)
                ).fetchone()
                
                status_color = "green"
                if last_audit:
                    temp = float(last_audit.get("temperatura_celsius_float") or 0)
                    if not last_audit.get("estado_luces_bool") or not last_audit.get("limpieza_ok_bool") or not last_audit.get("iluminacion_ok_bool", True) or temp > 24.0:
                        status_color = "red"
                
                status_data.append({
                    "rack": dict(rack),
                    "last_audit": dict(last_audit) if last_audit else None,
                    "status_color": status_color
                })
        return jsonify({"status": "success", "data": status_data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_api.route("/api/racks/audit", methods=["POST"])
def api_post_rack_audit():
    try:
        rack_id = request.form.get("rack_id")
        estado_luces = 1 if request.form.get("estado_luces") == "on" else 0
        limpieza_ok = 1 if request.form.get("limpieza_ok") == "on" else 0
        iluminacion_ok = 1 if request.form.get("iluminacion_ok") == "on" else 0
        
        try:
            temperatura = float(request.form.get("temperatura") or 0)
        except ValueError:
            return jsonify({"status": "error", "message": "Temperatura inválida."}), 400
            
        observaciones = request.form.get("observaciones", "").strip()
        
        if (estado_luces == 0 or limpieza_ok == 0 or iluminacion_ok == 0 or temperatura > 24.0) and not observaciones:
            return jsonify({"status": "error", "message": "Las observaciones son obligatorias si hay fallas o temperatura alta."}), 400

        foto_file = request.files.get("foto")
        ruta_foto = ""
        
        if foto_file and foto_file.filename != "":
            filename = secure_filename(foto_file.filename)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
            unique_filename = f"rack_{rack_id}_{uuid.uuid4().hex[:8]}.{ext}"
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
            foto_file.save(upload_path)
            ruta_foto = unique_filename
            
        tecnico = current_technician_identity()
        
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO rack_audits (rack_id, estado_luces_bool, limpieza_ok_bool, iluminacion_ok_bool, temperatura_celsius_float, observaciones_text, ruta_foto_text, tecnico)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (rack_id, estado_luces, limpieza_ok, iluminacion_ok, temperatura, observaciones, ruta_foto, tecnico)
            )
            
            # --- TAREA GLOBAL AGRUPADA (Flujo Transparente) ---
            try:
                import datetime
                
                # 1. Obtener nombre del rack para el registro
                rack_row = conn.execute("SELECT nombre FROM racks WHERE id = %s", (rack_id,)).fetchone()
                rack_name = rack_row["nombre"] if rack_row else f"ID {rack_id}"
                
                # 2. Buscar o crear la Tarea Diaria
                today_str = datetime.datetime.now().strftime("%Y-%m-%d")
                task_desc = f"Auditoría de Racks - {today_str}"
                
                existing_task = conn.execute(
                    "SELECT id FROM tasks WHERE descripcion = %s AND assigned_to = %s LIMIT 1",
                    (task_desc, tecnico)
                ).fetchone()
                
                if existing_task:
                    task_id = existing_task["id"]
                    # Actualizar fecha de completado
                    conn.execute("UPDATE tasks SET completed_at = NOW() WHERE id = %s", (task_id,))
                else:
                    # Crear nueva tarea en estado Hecha
                    cursor = conn.execute(
                        """
                        INSERT INTO tasks (descripcion, solicitante, categoria, tipo_actividad, estado, assigned_to, pc_name, completed_by, completed_at, created_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        """,
                        (task_desc, 'Sistema', 'Mantenimiento', 'tarea', 'Hecha', tecnico, 'Infraestructura', tecnico)
                    )
                    task_id = cursor.lastrowid
                
                # 3. Registrar la acción (el rack revisado)
                str_luces = "OK" if estado_luces else "Falla"
                str_limpieza = "OK" if limpieza_ok else "Falla"
                accion_texto = f"Revisó Rack '{rack_name}'. Luces: {str_luces}, Limpieza: {str_limpieza}, Temp: {temperatura}°C"
                if observaciones:
                    accion_texto += f" | Obs: {observaciones}"
                    
                conn.execute(
                    "INSERT INTO task_actions (task_id, user_name, action_text) VALUES (%s, %s, %s)",
                    (task_id, tecnico, accion_texto)
                )
            except Exception as e:
                print(f"Error registrando la tarea agrupada de rack: {e}")
                
            conn.commit()
            
        return jsonify({"status": "success", "message": "Auditoría guardada exitosamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- SWITCHES API ---

@bp_api.route("/api/switches", methods=["GET"])
def api_get_switches():
    try:
        with get_db_connection() as conn:
            switches = conn.execute("SELECT * FROM switches ORDER BY nombre").fetchall()
        return jsonify({"status": "success", "data": [dict(s) for s in switches]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_api.route("/api/switches", methods=["POST"])
def api_post_switch():
    try:
        data = request.get_json() if request.is_json else request.form
        nombre = data.get("nombre", "").strip()
        marca = data.get("marca", "").strip()
        modelo = data.get("modelo", "").strip()
        edificio = data.get("edificio", "").strip()
        lugar = data.get("lugar", "").strip()
        
        try:
            puertos_totales = int(data.get("puertos_totales") or 0)
            puertos_poe = int(data.get("puertos_poe") or 0)
        except ValueError:
            return jsonify({"status": "error", "message": "Los puertos deben ser numéricos."}), 400

        if not nombre:
            return jsonify({"status": "error", "message": "El nombre es obligatorio."}), 400

        import uuid
        codigo_qr = f"SW-{uuid.uuid4().hex[:8].upper()}"

        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO switches (codigo_qr, nombre, marca, modelo, edificio, lugar, puertos_totales, puertos_poe)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (codigo_qr, nombre, marca, modelo, edificio, lugar, puertos_totales, puertos_poe)
            )
            conn.commit()
        return jsonify({"status": "success", "message": "Switch creado exitosamente.", "codigo_qr": codigo_qr})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_api.route("/api/switches/<int:switch_id>", methods=["DELETE"])
def api_delete_switch(switch_id):
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM switches WHERE id = %s", (switch_id,))
            conn.commit()
        return jsonify({"status": "success", "message": "Switch eliminado exitosamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_api.route("/api/switches/status", methods=["GET"])
def api_get_switches_status():
    try:
        with get_db_connection() as conn:
            switches = conn.execute("SELECT * FROM switches ORDER BY nombre").fetchall()
            status_data = []
            for sw in switches:
                last_audit = conn.execute(
                    "SELECT * FROM switch_audits WHERE switch_id = %s ORDER BY timestamp DESC LIMIT 1",
                    (sw["id"],)
                ).fetchone()
                
                status_color = "green"
                if last_audit:
                    if last_audit["estado_general"] != "Online" or last_audit["puertos_fallados"] > 0:
                        status_color = "red"

                status_data.append({
                    "switch": dict(sw),
                    "last_audit": dict(last_audit) if last_audit else None,
                    "status_color": status_color
                })

        return jsonify({"status": "success", "data": status_data})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_api.route("/api/switches/audit", methods=["POST"])
def api_post_switch_audit():
    try:
        from utils.auth import current_technician_identity
        switch_id = request.form.get("switch_id")
        estado_general = request.form.get("estado_general", "Online")
        observaciones = request.form.get("observaciones", "").strip()
        
        try:
            puertos_libres = int(request.form.get("puertos_libres") or 0)
            puertos_ocupados = int(request.form.get("puertos_ocupados") or 0)
            puertos_fallados = int(request.form.get("puertos_fallados") or 0)
        except ValueError:
            return jsonify({"status": "error", "message": "Valores de puertos inválidos."}), 400
            
        if (estado_general != "Online" or puertos_fallados > 0) and not observaciones:
            return jsonify({"status": "error", "message": "Las observaciones son obligatorias si hay fallas."}), 400

        tecnico = current_technician_identity()
        
        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO switch_audits (switch_id, estado_general, puertos_libres, puertos_ocupados, puertos_fallados, observaciones_text, tecnico)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (switch_id, estado_general, puertos_libres, puertos_ocupados, puertos_fallados, observaciones, tecnico)
            )
            conn.commit()
            
        return jsonify({"status": "success", "message": "Auditoría de switch guardada exitosamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- ADMIN NOTIFICATIONS API ---

@bp_api.route("/api/notifications/unread", methods=["GET"])
def api_get_unread_notifications():
    try:
        with get_db_connection() as conn:
            # Fetch unread notifications
            notifications = conn.execute(
                "SELECT id, title, body, url, created_at FROM app_notifications WHERE read_at IS NULL ORDER BY created_at DESC LIMIT 50"
            ).fetchall()
            
            # Format datetime for JSON
            result = []
            for n in notifications:
                nd = dict(n)
                if nd["created_at"]:
                    nd["created_at"] = nd["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                result.append(nd)
                
            return jsonify({"status": "success", "data": result, "count": len(result)})
    except Exception as e:
        print(f"Error fetching notifications: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_api.route("/api/notifications/<int:notif_id>/mark_read", methods=["POST"])
def api_mark_notification_read(notif_id):
    try:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE app_notifications SET read_at = NOW() WHERE id = %s",
                (notif_id,)
            )
            conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_api.route("/api/admin/sent_messages", methods=["GET"])
def api_admin_sent_messages():
    try:
        from utils.auth import is_authenticated, current_user, is_superuser, current_username
        if not is_authenticated() or (current_user().get('role') != 'administrador' and not is_superuser()):
            return jsonify({"status": "error", "message": "No autorizado"}), 401

        sender = current_username()

        with get_db_connection() as conn:
            # Traer historial de mensajes/recordatorios enviados por este admin
            messages = conn.execute(
                """
                SELECT id, title, body, technician_name, created_at, scheduled_for, read_at
                FROM tech_messages 
                WHERE sender = %s
                ORDER BY created_at DESC 
                LIMIT 100
                """,
                (sender,)
            ).fetchall()
            
            result = []
            for m in messages:
                md = dict(m)
                if md["created_at"]:
                    md["created_at"] = md["created_at"].strftime("%Y-%m-%d %H:%M:%S")
                if md["scheduled_for"]:
                    md["scheduled_for"] = md["scheduled_for"].strftime("%Y-%m-%d %H:%M:%S")
                if md["read_at"]:
                    md["read_at"] = md["read_at"].strftime("%Y-%m-%d %H:%M:%S")
                result.append(md)
                
            return jsonify({"status": "success", "data": result})
    except Exception as e:
        print(f"Error fetching admin sent messages: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

