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

        tareas = conn.execute("""
            SELECT id, pc_name, created_at, descripcion, estado, solicitante, assigned_to, completed_by
            FROM tasks WHERE pc_name = %s ORDER BY created_at DESC
        """, (pc_name,)).fetchall()
        
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
        
        all_pcs = conn.execute("SELECT pc_name, fuero, last_user FROM pcs WHERE is_active=1 ORDER BY pc_name").fetchall()
        
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
            SELECT id, serial_number, component_type, brand_model, status, assigned_to_component_id 
            FROM components WHERE assigned_pc = %s ORDER BY assigned_to_component_id ASC, component_type
        ''', (pc_name,)).fetchall()
        
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
            "preferred_printer_serial": preferred_printer_serial,
            "preferred_printer_serial_source": preferred_printer_serial_source,
        }
