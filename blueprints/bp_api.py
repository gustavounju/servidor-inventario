from flask import Blueprint, request, jsonify, redirect, url_for
import json
import datetime
import os

from database.db_core import get_db_connection
from utils.constants import detect_fuero

bp_api = Blueprint('api', __name__)

def process_inventory_data(data):
    """Lógica central para procesar el JSON de inventario e insertar/actualizar en BD."""
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
    if printer_port and printer_port.upper().startswith("WSD"):
        printer_port = "Red"
        
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

    # Si la impresora está desconectada y es local, tratarla como SIN IMPRESORA
    if esta_desconectada and es_local:
        printer_model = "SIN IMPRESORA"
        printer_port = "N/A"
        data["Printer_Model"] = "SIN IMPRESORA"
        data["Printer_Port"] = "N/A"
        pm = "SIN IMPRESORA"
        pp = "N/A"
        esta_desconectada = False # Reset so it doesn't trigger other disconnect alerts if not wanted, though it's already "SIN IMPRESORA"

    sin_modelo = pm in ("", "N/A", "NINGUNA", "SIN IMPRESORA")
    es_virtual = ("PDF" in pm) or ("XPS" in pm) or ("ONENOTE" in pm)
    es_red = ("IP_" in pp) or ("WSD" in pp) or ("\\" in pp)

    if sin_modelo or es_virtual or esta_desconectada: alerta_sin_impresora = 1
    else: alerta_sin_impresora = 0

    alerta_impresora_red = 1 if (not sin_modelo and not es_virtual and es_red and not es_local) else 0

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

    sql = """
    INSERT INTO pcs (pc_name, fuero, os_name, processor, ram_gb, ip_address, last_user, last_report, ram_detalles, disk_models, disk_speeds_rpm, motherboard_model, monitors, printer_model, printer_port, ping_ms, ping_loss_pct, alerta_ram_baja, alerta_sin_impresora, alerta_impresora_red, alerta_disco, alerta_uptime, is_active, full_json_data)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'True', %s)
    ON DUPLICATE KEY UPDATE
        fuero=VALUES(fuero), os_name=VALUES(os_name), processor=VALUES(processor), ram_gb=VALUES(ram_gb), ip_address=VALUES(ip_address), last_user=VALUES(last_user), last_report=VALUES(last_report), ram_detalles=VALUES(ram_detalles), disk_models=VALUES(disk_models), disk_speeds_rpm=VALUES(disk_speeds_rpm), motherboard_model=VALUES(motherboard_model), monitors=VALUES(monitors), printer_model=VALUES(printer_model), printer_port=VALUES(printer_port), ping_ms=VALUES(ping_ms), ping_loss_pct=VALUES(ping_loss_pct), alerta_ram_baja=VALUES(alerta_ram_baja), alerta_sin_impresora=VALUES(alerta_sin_impresora), alerta_impresora_red=VALUES(alerta_impresora_red), alerta_disco=VALUES(alerta_disco), alerta_uptime=VALUES(alerta_uptime), is_active='True', full_json_data=VALUES(full_json_data)
    """
    
    with get_db_connection() as conn:
        current_pc = conn.execute("SELECT * FROM pcs WHERE pc_name = %s", (pc_name,)).fetchone()
        if current_pc:
            fields_to_check = {
                "ram_gb": str(current_pc["ram_gb"]), "disk_models": str(current_pc["disk_models"]),
                "processor": str(current_pc["processor"]), "os_name": str(current_pc["os_name"]), "ip_address": str(current_pc["ip_address"])
            }
            new_values_map = {
                "ram_gb": str(ram_gb), "disk_models": str(disk_models), "processor": str(processor), "os_name": str(os_name), "ip_address": str(ip_address)
            }
            for field, old_val in fields_to_check.items():
                new_val = new_values_map.get(field, "N/A")
                if old_val.strip() != new_val.strip():
                    conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, %s, %s, %s)", (pc_name, field, old_val, new_val))

        conn.execute(sql, (pc_name, fuero_detectado, os_name, processor, ram_gb, ip_address, last_user, last_report, ram_detalles, disk_models, disk_speeds_rpm, motherboard_model, monitors, printer_model, printer_port, ping_ms, ping_loss_pct, alerta_ram_baja, alerta_sin_impresora, alerta_impresora_red, alerta_disco, alerta_uptime, full_json))
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
