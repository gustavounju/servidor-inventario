from database.db_core import get_db_connection
from utils.auth import list_technician_users
import re


def _infer_disk_kind(model, speed_text):
    model_text = (model or "").strip()
    speed_value = (speed_text or "").strip()
    combined = f"{model_text} {speed_value}".upper()

    rpm_match = re.search(r"(\d+)\s*RPM", combined)
    if rpm_match:
        rpm = int(rpm_match.group(1))
        if rpm > 0:
            return f"HDD {rpm} RPM"

    if any(token in combined for token in ("SSD", "NVME", "M.2", "SOLID")):
        return "SSD"

    if re.search(r"\b(SN[VMP]?\w*|SU\d+|EVO|KINGSTON|ADATA)\b", combined) and "HITACHI" not in combined:
        return "SSD"

    if any(token in combined for token in ("HITACHI", "WD ", "WESTERN DIGITAL", "SEAGATE", "TOSHIBA", "HUA7")):
        return "HDD"

    if "FIXED HARD DISK" in combined or "HDD" in combined:
        return "HDD"

    return "Tipo no detectado"


def _build_disk_summary_lines(disk_models, disk_speeds):
    models = [part.strip() for part in (disk_models or "").split("|") if part.strip()]
    speed_parts = [part.strip() for part in (disk_speeds or "").split("|") if part.strip()]
    speed_map = {}

    for part in speed_parts:
        if ":" in part:
            model_name, kind = part.split(":", 1)
            speed_map[model_name.strip().upper()] = kind.strip()

    lines = []
    for model_entry in models:
        model_name = model_entry.split(" (")[0].strip()
        kind = speed_map.get(model_name.upper(), "")
        if not kind or kind.upper() in ("RPM", "0 RPM", "N/A"):
            kind = _infer_disk_kind(model_entry, kind)
        lines.append(f"{model_entry} - {kind}")

    return lines

def _parse_hardware_components(pc):
    """
    Formatea y estructura los componentes internos (Motherboard, RAM, Discos, CPU) 
    extrayendo marcas, modelos y números de serie físicos.
    """
    mb_raw = pc.get("motherboard_model") or "N/A"
    ram_raw = pc.get("ram_detalles") or "N/A"
    disk_raw = pc.get("disk_models") or "N/A"
    proc_raw = pc.get("processor") or "N/A"

    # Motherboard
    mb_info = {"model": mb_raw, "serial": "N/A"}
    if " (SN: " in mb_raw:
        parts = mb_raw.split(" (SN: ")
        mb_info["model"] = parts[0].strip()
        mb_info["serial"] = parts[1].replace(")", "").strip()

    # RAM Modules
    ram_list = []
    if ram_raw and ram_raw != "N/A":
        for module in ram_raw.split("|"):
            mod_str = module.strip()
            if not mod_str: continue
            sn = "N/A"
            if " (SN: " in mod_str:
                m_parts = mod_str.split(" (SN: ")
                spec = m_parts[0].strip()
                sn = m_parts[1].replace(")", "").strip()
            else:
                spec = mod_str
            ram_list.append({"spec": spec, "serial": sn})

    # Disks
    disk_list = []
    if disk_raw and disk_raw != "N/A":
        for disk in disk_raw.split("|"):
            d_str = disk.strip()
            if not d_str: continue
            sn = "N/A"
            if " [SN: " in d_str:
                d_parts = d_str.split(" [SN: ")
                model = d_parts[0].strip()
                sn = d_parts[1].replace("]", "").strip()
            else:
                model = d_str
            disk_list.append({"model": model, "serial": sn})

    # Monitors
    mon_raw = pc.get("monitors") or "N/A"
    mon_list = []
    if mon_raw and mon_raw != "N/A":
        for mon in mon_raw.split("|"):
            m_str = mon.strip()
            if not m_str: continue
            sn = "N/A"
            if " (SN: " in m_str:
                m_parts = m_str.split(" (SN: ")
                model = m_parts[0].strip()
                sn = m_parts[1].replace(")", "").strip()
            else:
                model = m_str
            mon_list.append({"model": model, "serial": sn})

    # Keyboard & Mouse (from full_json_data or pc dict if present)
    full_json = {}
    if pc.get("full_json_data"):
        try:
            import json
            full_json = json.loads(pc["full_json_data"])
        except Exception: pass
    
    keyboard_model = full_json.get("Keyboard_Model") or "Teclado USB Estándar"
    if not keyboard_model or keyboard_model in ("N/A", "None", ""):
        keyboard_model = "Teclado USB Estándar"

    mouse_model = full_json.get("Mouse_Model") or "Mouse Óptico USB Estándar"
    if not mouse_model or mouse_model in ("N/A", "None", ""):
        mouse_model = "Mouse Óptico USB Estándar"

    # Printer
    printer_info = {
        "model": pc.get("printer_model") or "N/A",
        "port": pc.get("printer_port") or "N/A",
        "serial": pc.get("printer_sn") or "N/A"
    }

    return {
        "motherboard": mb_info,
        "ram_modules": ram_list,
        "disks": disk_list,
        "monitors": mon_list,
        "keyboard": keyboard_model,
        "mouse": mouse_model,
        "printer": printer_info,
        "processor": proc_raw
    }


def get_pc_detail_context(pc_name):
    """Obtiene todo el contexto necesario para renderizar pc_detail.html."""
    with get_db_connection() as conn:
        pc = conn.execute("""
            SELECT p.*, COALESCE(u.real_name, au.display_name) as ad_real_name 
            FROM pcs p 
            LEFT JOIN ad_users u ON LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = u.username 
            LEFT JOIN app_users au ON LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = au.username
            WHERE p.pc_name = %s
        """, (pc_name,)).fetchone()
        
        if not pc:
            return None

        tareas = [dict(row) for row in conn.execute("""
            SELECT id, pc_name, created_at, descripcion, estado, solicitante, assigned_to, completed_by
            FROM tasks WHERE pc_name = %s ORDER BY created_at DESC
        """, (pc_name,)).fetchall()]
        
        # Attach AD matches if this is a generic PC
        if 'generica' in pc_name.lower():
            from blueprints.bp_tasks import _attach_task_user_matches
            tareas = _attach_task_user_matches(tareas, conn)
        
        technicians = list_technician_users()
        
        ad_users_list = [dict(row) for row in conn.execute("""
            SELECT username, real_name, phone, fuero FROM ad_users
            UNION
            SELECT DISTINCT LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) as username, last_user as real_name, NULL as phone, NULL as fuero
            FROM pcs WHERE last_user IS NOT NULL AND last_user != ''
              AND LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) NOT IN (SELECT username FROM ad_users)
            ORDER BY real_name
        """).fetchall()]
        
        audit_logs = conn.execute("SELECT * FROM audit_logs WHERE pc_name = %s ORDER BY changed_at DESC", (pc_name,)).fetchall()
        
        all_pcs = conn.execute("""
            SELECT p.pc_name, p.fuero, p.last_user, a.real_name 
            FROM pcs p 
            LEFT JOIN ad_users a ON LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = a.username 
            WHERE p.is_active=1 
            ORDER BY p.pc_name
        """).fetchall()
        
        pc_ups_list = conn.execute('''
            SELECT u.*, b.serial_number as battery_code FROM ups_inventory u
            LEFT JOIN components b ON u.assigned_battery_id = b.id
            WHERE u.assigned_pc = %s
        ''', (pc_name,)).fetchall()
        
        # Compartición de impresoras
        sharing_pc_data = None
        if pc["printer_port"] and pc["printer_port"].startswith("\\\\"):
            parts = pc["printer_port"].split("\\")
            if len(parts) >= 3:
                potential_host = parts[2].upper()
                sharing_pc_data = conn.execute(
                    "SELECT pc_name, is_active, printer_port, printer_sn, printer_model FROM pcs WHERE pc_name = %s OR ip_address = %s LIMIT 1", 
                    (potential_host, potential_host)
                ).fetchone()
        
        clients_using_this_printer = []
        if pc["pc_name"] and (pc["pc_name"].upper() not in ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA')):
            pat_name = f"%\\\\\\\\{pc['pc_name'].upper()}\\\\%"
            pat_ip = f"%\\\\\\\\{pc['ip_address']}\\\\%" if pc['ip_address'] and pc['ip_address'] != 'N/A' else None
            query = "SELECT pc_name FROM pcs WHERE is_active=1 AND UPPER(printer_port) LIKE %s"
            params = [pat_name]
            if pat_ip:
                query += " OR UPPER(printer_port) LIKE %s"; params.append(pat_ip)
            clients_using_this_printer = conn.execute(query, tuple(params)).fetchall()
        
        available_ups = conn.execute("SELECT id, code, model FROM ups_inventory WHERE assigned_pc IS NULL").fetchall()
        pc_components = conn.execute('''
            SELECT id, serial_number, component_type, brand_model, status, assigned_to_component_id, oc_number, invoice_number, supplier, assigned_user, assigned_fuero 
            FROM components WHERE assigned_pc = %s ORDER BY assigned_to_component_id ASC, component_type
        ''', (pc_name,)).fetchall()
        
        comp_dicts = [dict(c) for c in pc_components]
        oc_list = sorted(list({c["oc_number"].strip() for c in comp_dicts if c.get("oc_number") and c["oc_number"].strip()}))
        invoice_list = sorted(list({c["invoice_number"].strip() for c in comp_dicts if c.get("invoice_number") and c["invoice_number"].strip()}))

        available_components = conn.execute('''
            SELECT id, serial_number, component_type, brand_model FROM components 
            WHERE status = 'Stock' AND component_type NOT LIKE 'Bat%'
        ''').fetchall()
        
        baterias_disponibles = conn.execute("SELECT id, serial_number as code, brand_model FROM components WHERE component_type LIKE 'Bat%' AND status = 'Stock'").fetchall()
        
        assigned_network_printers = conn.execute('''
            SELECT np.id, np.ip_address, np.brand_model, np.serial_number FROM network_printers np
            JOIN pc_network_printers pnp ON np.id = pnp.printer_id WHERE pnp.pc_name = %s
        ''', (pc_name,)).fetchall()

        detected_printers = conn.execute('''
            SELECT id, printer_model, printer_port, printer_sn
            FROM pc_detected_printers
            WHERE pc_name = %s
              AND is_ignored = 0
              AND printer_model IS NOT NULL
              AND printer_model != ''
              AND printer_model != 'N/A'
              AND UPPER(printer_model) NOT LIKE '%%SIN IMPRESORA%%'
            ORDER BY updated_at DESC
        ''', (pc_name,)).fetchall()
        
        available_network_printers = conn.execute("SELECT id, ip_address, brand_model FROM network_printers ORDER BY ip_address").fetchall()

        disk_summary_lines = _build_disk_summary_lines(pc.get("disk_models"), pc.get("disk_speeds_rpm"))
        hardware_components = _parse_hardware_components(pc)

        preferred_printer_serial = pc.get("printer_sn")
        preferred_printer_serial_source = "pc"
        if (not preferred_printer_serial or preferred_printer_serial == "N/A") and assigned_network_printers:
            first_assigned = assigned_network_printers[0]
            if first_assigned.get("serial_number") and first_assigned["serial_number"] != "N/A":
                preferred_printer_serial = first_assigned["serial_number"]
                preferred_printer_serial_source = "assigned_network_printer"

        return {
            "pc": pc, "tareas": tareas, "technicians": technicians, "ad_users_list": ad_users_list,
            "audit_logs": audit_logs, "all_pcs": all_pcs, "pc_ups_list": pc_ups_list,
            "available_ups": available_ups, "pc_components": pc_components,
            "available_components": available_components, "baterias_disponibles": baterias_disponibles,
            "sharing_pc": sharing_pc_data, "clients_using_this_printer": clients_using_this_printer,
            "assigned_network_printers": assigned_network_printers,
            "detected_printers": detected_printers,
            "available_network_printers": available_network_printers,
            "disk_summary_lines": disk_summary_lines,
            "hardware_components": hardware_components,
            "preferred_printer_serial": preferred_printer_serial,
            "preferred_printer_serial_source": preferred_printer_serial_source,
            "oc_list": oc_list,
            "invoice_list": invoice_list
        }
