from flask import Blueprint, request, jsonify, redirect, url_for
import json
import datetime
import os

from database.db_core import get_db_connection
from utils.constants import detect_fuero

bp_api = Blueprint('api', __name__)

def process_inventory_data(data):
    from utils.constants import detect_fuero, clean_hex_string
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

    red = data.get("Red", [])
    ip_address = red[0].get("IPAddress") if red else "N/A"

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
            parts = printer_port.split("\\")
            if len(parts) >= 3:
                host_ref = parts[2].upper()
                with get_db_connection() as conn:
                    if host_ref:
                        # Buscamos la PC host por nombre (LIKE para manejar FQDN) o por IP
                        host_info = conn.execute(
                            "SELECT printer_sn, printer_model, pc_name FROM pcs WHERE (UPPER(pc_name) LIKE %s OR ip_address = %s) AND printer_sn IS NOT NULL AND printer_sn != 'N/A' AND printer_sn != '' LIMIT 1", 
                            (f"{host_ref.upper()}%", host_ref)
                        ).fetchone()
                        
                        if host_info and host_info['printer_sn'] and host_info['printer_sn'] != 'N/A':
                            printer_sn = host_info['printer_sn']
                            # Si el cliente no reportó modelo, heredamos el del host
                            if not printer_model or printer_model == "N/A":
                                printer_model = host_info['printer_model']
                            debug_logs.append(f"Herencia: Serial {printer_sn} heredado del host {host_info['pc_name']}")
                        else:
                            debug_logs.append(f"Herencia: No se encontró serial válido en el host {host_ref}")
        except Exception as e:
            debug_logs.append(f"Error en herencia: {e}")
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

        if alerta_impresora_red == 1:
            alerta_sin_impresora = 1

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
    fuero_detectado = detect_fuero(pc_name)

    # Initial states for new calculations
    alerta_nombre_duplicado = 0
    reactivado = False
    
    with get_db_connection() as conn:
        current_pc = conn.execute("SELECT * FROM pcs WHERE pc_name = %s", (pc_name,)).fetchone()
        if current_pc:
            # Check for reactivation from Cementerio
            if str(current_pc.get("is_active", "True")) == "False":
                reactivado = True
                conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, %s, %s, %s)", 
                             (pc_name, "Estado de PC", "Cementerio (Baja)", "Reactivado (Activo)"))

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
                "ram_gb": str(ram_gb), "disk_models": str(disk_models), "processor": str(processor), "os_name": str(os_name), "ip_address": str(ip_address)
            }
            for field, old_val in fields_to_check.items():
                new_val = new_values_map.get(field, "N/A")
                if old_val.strip() != new_val.strip():
                    conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, %s, %s, %s)", (pc_name, field, old_val, new_val))


    # --- OBTENER VALORES ANTIGUOS PARA LIMPIEZA ---
    old_printer_sn = "N/A"
    with get_db_connection() as conn:
        old_pc = conn.execute("SELECT printer_sn FROM pcs WHERE pc_name = %s", (pc_name,)).fetchone()
        if old_pc: old_printer_sn = old_pc["printer_sn"] or "N/A"

    sql = """
    INSERT INTO pcs (pc_name, fuero, os_name, processor, ram_gb, ip_address, last_user, last_report, ram_detalles, disk_models, disk_speeds_rpm, motherboard_model, monitors, printer_model, printer_port, printer_sn, ping_ms, ping_loss_pct, alerta_ram_baja, alerta_sin_impresora, alerta_impresora_red, alerta_disco, alerta_uptime, alerta_nombre_duplicado, is_active, full_json_data)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'True', %s)
    ON DUPLICATE KEY UPDATE
        fuero=VALUES(fuero), os_name=VALUES(os_name), processor=VALUES(processor), ram_gb=VALUES(ram_gb), ip_address=VALUES(ip_address), last_user=VALUES(last_user), last_report=VALUES(last_report), ram_detalles=VALUES(ram_detalles), disk_models=VALUES(disk_models), disk_speeds_rpm=VALUES(disk_speeds_rpm), motherboard_model=VALUES(motherboard_model), monitors=VALUES(monitors), printer_model=VALUES(printer_model), printer_port=VALUES(printer_port), printer_sn=VALUES(printer_sn), ping_ms=VALUES(ping_ms), ping_loss_pct=VALUES(ping_loss_pct), alerta_ram_baja=VALUES(alerta_ram_baja), alerta_sin_impresora=VALUES(alerta_sin_impresora), alerta_impresora_red=VALUES(alerta_impresora_red), alerta_disco=VALUES(alerta_disco), alerta_uptime=VALUES(alerta_uptime), alerta_nombre_duplicado=VALUES(alerta_nombre_duplicado), is_active='True', full_json_data=VALUES(full_json_data)
    """
    
    with get_db_connection() as conn:
        conn.execute(sql, (pc_name, fuero_detectado, os_name, processor, ram_gb, ip_address, last_user, last_report, ram_detalles, disk_models, disk_speeds_rpm, motherboard_model, monitors, printer_model, printer_port, printer_sn, ping_ms, ping_loss_pct, alerta_ram_baja, alerta_sin_impresora, alerta_impresora_red, alerta_disco, alerta_uptime, alerta_nombre_duplicado, full_json))
        
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
                conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, 'AUTO_SYNC_PRINTER', 'Catalog', %s)", (pc_name, printer_sn if printer_sn != 'N/A' else clean_ip))
        
        elif alerta_sin_impresora == 1:
            with get_db_connection() as conn:
                # 1. LIMPIEZA DEL CATÁLOGO (Stock de infraestructura)
                if old_printer_sn and old_printer_sn != "N/A":
                    # Borrado total si el SN coincide (ya sabemos que esta PC reportó no encontrarla)
                    cursor = conn.execute("DELETE FROM network_printers WHERE serial_number = %s", (old_printer_sn,))
                    print(f"[DEBUG] Catálogo limpiado. SN: {old_printer_sn}. Filas: {cursor.rowcount}")

                # 2. Limpieza de Asignaciones Internas
                conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, 'AUTO_CLEAN_PRINTER', 'Assigned', 'None')", (pc_name,))
                
                # 3. LIMPIEZA EN CASCADA (Misión: Clientes huérfanos)
                host_pattern = f"%\\\\\\\\{pc_name.upper()}\\\\%"
                clients = conn.execute("SELECT pc_name FROM pcs WHERE UPPER(printer_port) LIKE %s", (host_pattern,)).fetchall()
                if clients:
                    for c in clients:
                        client_name = c["pc_name"]
                        conn.execute("DELETE FROM pc_network_printers WHERE pc_name = %s", (client_name,))
                        conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, 'CASCADE_UNASSIGN', 'Host Offline', %s)", (client_name, pc_name))
                
                conn.commit()

        # --- PROPAGACIÓN EN CASCADA (SI SOY HOST) ---
        # Si esta PC tiene un serial de impresora USB/Local válido, buscar clientes que impriman aquí
        if printer_sn and printer_sn != "N/A" and printer_sn != "" and printer_sn != "Desconocido":
            # Patrones de puerto que buscaría un cliente: \\MiIP\ o \\MiNombre\
            # Usamos doble backslash para el LIKE de SQL
            patterns = []
            if ip_address and ip_address != "N/A":
                patterns.append(f"%\\\\\\\\{ip_address}\\\\%")
            if pc_name:
                patterns.append(f"%\\\\\\\\{pc_name.upper()}\\\\%")
            
            for pat in patterns:
                updated = conn.execute(
                    """
                    UPDATE pcs SET printer_sn = %s 
                    WHERE (printer_sn IS NULL OR printer_sn = 'N/A' OR printer_sn = '' OR printer_sn = 'Desconocido')
                    AND UPPER(printer_port) LIKE %s
                    """,
                    (printer_sn, pat)
                )
                if updated.rowcount > 0:
                    debug_logs.append(f"Cascada: Se actualizó serial {printer_sn} a {updated.rowcount} cliente(s) para el patrón {pat}")
            
        conn.commit()


    print(f"Inventario guardado / actualizado: {pc_name}")
    return pc_name


@bp_api.route("/submit_inventory", methods=["POST"])
def receive_inventory():
    try:
        raw_data = request.get_data()
        try: data = json.loads(raw_data.decode("utf-8"))
        except Exception: data = json.loads(raw_data.decode("utf-16"))
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
    if file:
        try:
            content = file.read()
            try: data = json.loads(content.decode("utf-8"))
            except: data = json.loads(content.decode("utf-16"))
            pc_name = process_inventory_data(data)
            print(f"Manual upload success for {pc_name}")
        except Exception as e: print(f"Error en carga manual: {e}")
        return redirect(url_for('dashboard.dashboard'))

@bp_api.route("/health", methods=["GET"])
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
    """Devuelve los datos de salud (SMART, Uptime, Eventos) desde el JSON completo."""
    try:
        with get_db_connection() as conn:
            row = conn.execute("SELECT full_json_data FROM pcs WHERE pc_name = %s", (pc_name,)).fetchone()
            if not row or not row["full_json_data"]:
                return jsonify({"status": "error", "message": "PC no encontrada o sin datos"}), 404
            
            data = json.loads(row["full_json_data"])
            health = data.get("Salud", {})
            return jsonify({"status": "success", "data": health})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
@bp_api.route("/api/pc_printer/<string:pc_ref>")
def api_pc_printer(pc_ref):
    """Devuelve el serial de la impresora de una PC dada (por nombre o IP)."""
    try:
        pc_ref = pc_ref.upper()
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT printer_sn, printer_model, printer_port FROM pcs WHERE UPPER(pc_name) = %s OR ip_address = %s LIMIT 1", 
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
    """Devuelve la lista de impresoras detectadas (locales) y registradas."""
    try:
        with get_db_connection() as conn:
            # 1. Impresoras registradas en Infraestructura
            net_printers = conn.execute("SELECT * FROM network_printers ORDER BY brand_model").fetchall()
            
            # 2. Impresoras detectadas en PCs (Locales/USB que no están en el catálogo)
            detected = conn.execute("""
                SELECT pc_name, printer_model, printer_sn, printer_port, last_report, fuero
                FROM pcs 
                WHERE is_active = 'True' 
                AND (printer_model IS NOT NULL AND printer_model != '' AND printer_model != 'N/A' AND UPPER(printer_model) NOT LIKE '%%SIN IMPRESORA%%')
                AND (printer_port IS NULL OR printer_port NOT LIKE '\\\\\\\\%%') 
                AND pc_name NOT IN (SELECT pc_name FROM pc_network_printers)
                AND (printer_sn IS NULL OR printer_sn = '' OR printer_sn = 'N/A' OR printer_sn NOT IN (SELECT serial_number FROM network_printers WHERE serial_number IS NOT NULL AND serial_number != ''))
                ORDER BY pc_name
            """).fetchall()
            
            return jsonify({
                "status": "success",
                "network_printers": [dict(p) for p in net_printers],
                "detected_printers": [dict(p) for p in detected]
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
