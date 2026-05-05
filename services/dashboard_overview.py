import os
import re
from datetime import datetime as dt

from database.db_core import get_db_connection
from utils.auth import list_app_users, list_technician_users

from services.dashboard_contract import (
    normalize_alerta,
    sanitize_sort_column,
    sanitize_sort_direction,
)


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
    return token.rstrip("\\/")


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


def _split_fuero_path(fuero):
    text = re.sub(r"\s+", " ", (fuero or "").strip())
    if not text or text.lower() == "desconocido":
        return ["Sin fuero asignado"]

    compact_code = text.upper().replace(" ", "")
    jcc_match = re.match(r"^JCC(\d+)SEC(\d{1,2})(?:\d{4,})?$", compact_code)
    if jcc_match:
        return [
            f"Juzgado Civil y Comercial N°{int(jcc_match.group(1))}",
            f"Secretaria {int(jcc_match.group(2))}",
        ]

    ccyc_match = re.match(r"^CCYCS([IVXLCDM]+)(\d{1,2})(?:\d{4,})?$", compact_code)
    if ccyc_match:
        return [
            "Cámara Civil y Comercial",
            f"Sala {ccyc_match.group(1)}",
            f"Vocalia {int(ccyc_match.group(2))}",
        ]

    tts_match = re.match(r"^TTS([IVXLCDM]+)VOC(\d{1,2})(?:\d{4,})?$", compact_code)
    if tts_match:
        return [
            "Tribunal de Trabajo",
            f"Sala {tts_match.group(1)}",
            f"Vocalia {int(tts_match.group(2))}",
        ]

    if "-" in text:
        parts = [_normalize_fuero_part(part.strip()) for part in text.split("-") if part.strip()]
        if parts:
            return parts

    marker_pattern = re.compile(
        r"\b(sala|secretar(?:i|í)a|vocal(?:i|í)a)\s+([A-Za-z0-9IVXLCDM]+)\b",
        re.IGNORECASE,
    )
    matches = list(marker_pattern.finditer(text))
    if not matches:
        return [text]

    root = text[:matches[0].start()].strip(" -")
    root = _normalize_fuero_part(root)
    parts = [root] if root else []
    for match in matches:
        label = match.group(1).lower()
        number = match.group(2).strip()
        if label.startswith("sala"):
            parts.append(f"Sala {number}")
        elif label.startswith("secretar"):
            parts.append(f"Secretaria {number}")
        else:
            parts.append(f"Vocalia {number}")

    return parts or [text]


def _normalize_fuero_part(part):
    text = re.sub(r"\s+", " ", (part or "").strip())
    if not text:
        return text

    lowered = text.lower()

    jcc_match = re.match(r"^juzgado civil y comercial n(?:Â?[°º]|o)\s*(\d+)$", text, re.IGNORECASE)
    if jcc_match:
        return f"Juzgado Civil y Comercial N°{int(jcc_match.group(1))}"

    if re.match(r"^c[áa]mara civil y comercial$", lowered, re.IGNORECASE):
        return "Cámara Civil y Comercial"

    sala_match = re.match(r"^sala\s+([a-z0-9ivxlcdm]+)$", text, re.IGNORECASE)
    if sala_match:
        return f"Sala {sala_match.group(1).upper()}"

    sec_match = re.match(r"^secretar(?:i|í)a\s+(\d+)$", text, re.IGNORECASE)
    if sec_match:
        return f"Secretaria {int(sec_match.group(1))}"

    voc_match = re.match(r"^vocal(?:i|í)a\s+(\d+)$", text, re.IGNORECASE)
    if voc_match:
        return f"Vocalia {int(voc_match.group(1))}"

    return text


def _node_to_view(name, node):
    children = [
        _node_to_view(child_name, child_node)
        for child_name, child_node in sorted(node["children"].items(), key=lambda item: item[0].lower())
    ]
    pcs = sorted(node["pcs"], key=lambda pc: (pc.get("pc_name") or "").lower())
    return {
        "name": name,
        "count": node["count"],
        "uncataloged_printers": node["uncataloged_printers"],
        "children": children,
        "pcs": pcs,
    }


def _build_fuero_tree(pcs):
    roots = {}
    for pc in pcs:
        path = _split_fuero_path(pc.get("fuero"))
        current_level = roots
        current_node = None
        for part in path:
            current_node = current_level.setdefault(part, {"count": 0, "uncataloged_printers": 0, "children": {}, "pcs": []})
            current_node["count"] += 1
            current_node["uncataloged_printers"] += int(pc.get("detected_printers_count") or 0)
            current_level = current_node["children"]
        if current_node is not None:
            current_node["pcs"].append(pc)

    return [
        _node_to_view(name, node)
        for name, node in sorted(roots.items(), key=lambda item: item[0].lower())
    ]


def _is_auxiliary_pc(pc):
    name = (pc.get("pc_name") or "").upper()
    return "GENERICA" in name or name.startswith("INFRAESTRUCTURA")


def load_dashboard_overview(*, q, estado, alerta, os_param, filter_tasks, sort_by, order, page, per_page, tipo_actividad=""):
    """Carga el contexto del dashboard para mantener la ruta Flask más delgada."""
    pcs_data = []
    auxiliary_pcs = []
    unassigned_tasks = []
    all_pcs_dropdown = []
    ad_users_list = []
    app_users_list = []
    active_mobile_techs = []
    pending_users_list = []
    technicians_list = []
    pc_ports = {}
    unassigned_count = 0
    fuero_tree = []

    kpi_total_activas = 0
    kpi_total_graveyard = 0
    kpi_alerta_ram = 0
    kpi_sin_impresora = 0
    kpi_impresora_red = 0
    kpi_total_impresoras = 0
    kpi_win7 = 0
    kpi_win10 = 0
    kpi_win11 = 0
    kpi_tareas_hoy = 0
    kpi_tareas_pendientes_total = 0
    kpi_saludables = 0
    kpi_alerta_media = 0
    kpi_criticas = 0
    kpi_sin_impresora_inventario = 0
    kpi_incidentes = 0
    kpi_riesgos = 0
    kpi_tareas = 0
    total_rows = 0
    last_backup_info = "Sin backups"

    alerta = normalize_alerta(alerta)
    offset = (page - 1) * per_page

    try:
        with get_db_connection() as conn:
            filter_sql = ""
            filter_params = []
            if q:
                filter_sql += " AND (p.pc_name LIKE %s OR p.last_user LIKE %s OR p.ip_address LIKE %s OR p.fuero LIKE %s OR p.os_name LIKE %s OR u.real_name LIKE %s OR au.display_name LIKE %s)"
                filter_params.extend([f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"])

            if estado in ("True", "False"):
                filter_sql += " AND p.is_active = %s"
                filter_params.append(estado)
            if alerta == "ram":
                filter_sql += " AND p.alerta_ram_baja = 1"
            elif alerta == "sin_impresora_alerta":
                filter_sql += " AND p.alerta_sin_impresora = 1"
            elif alerta == "red":
                filter_sql += " AND p.alerta_impresora_red = 1"
            elif alerta == "critica":
                filter_sql += " AND (p.alerta_ram_baja + IF(p.alerta_sin_impresora = 1 AND p.pc_name NOT IN (SELECT pc_name FROM pc_network_printers), 1, 0) + p.alerta_disco + p.alerta_uptime + p.alerta_nombre_duplicado) >= 2"
            elif alerta == "media":
                filter_sql += " AND (p.alerta_ram_baja + IF(p.alerta_sin_impresora = 1 AND p.pc_name NOT IN (SELECT pc_name FROM pc_network_printers), 1, 0) + p.alerta_disco + p.alerta_uptime + p.alerta_nombre_duplicado) = 1"
            elif alerta == "ninguna":
                filter_sql += " AND p.alerta_ram_baja = 0 AND IF(p.alerta_sin_impresora = 1 AND p.pc_name NOT IN (SELECT pc_name FROM pc_network_printers), 1, 0) = 0 AND p.alerta_disco = 0 AND p.alerta_uptime = 0 AND p.alerta_nombre_duplicado = 0"
            elif alerta == "sin_impresora_inventario":
                filter_sql += " AND (p.printer_model IS NULL OR p.printer_model = '' OR p.printer_model = 'N/A' OR UPPER(p.printer_model) IN ('NONE', '-') OR UPPER(p.printer_model) LIKE '%%SIN IMPRESORA%%') AND p.pc_name NOT IN (SELECT pc_name FROM pc_network_printers)"

            if os_param == "win7":
                filter_sql += " AND p.os_name LIKE %s"
                filter_params.append("%Windows 7%")
            elif os_param == "win10":
                filter_sql += " AND p.os_name LIKE %s"
                filter_params.append("%Windows 10%")
            elif os_param == "win11":
                filter_sql += " AND p.os_name LIKE %s"
                filter_params.append("%Windows 11%")

            if filter_tasks == "true":
                if tipo_actividad:
                    filter_sql += " AND (SELECT COUNT(*) FROM tasks t WHERE t.pc_name = p.pc_name AND t.estado != 'Hecha' AND t.tipo_actividad = %s) > 0"
                    filter_params.append(tipo_actividad)
                else:
                    filter_sql += " AND (SELECT COUNT(*) FROM tasks t WHERE t.pc_name = p.pc_name AND t.estado != 'Hecha') > 0"

            count_sql = """
                SELECT COUNT(*) as c
                FROM pcs p
                LEFT JOIN ad_users u ON (
                    LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = u.username OR
                    LOWER(p.last_user) = LOWER(u.real_name)
                )
                LEFT JOIN app_users au ON (
                    LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = au.username
                )
                WHERE 1=1
            """ + filter_sql
            total_rows = conn.execute(count_sql, filter_params).fetchone()["c"]

            unassigned_tasks = conn.execute(
                "SELECT * FROM tasks WHERE (pc_name IS NULL OR pc_name = '') AND estado != 'Hecha' ORDER BY created_at DESC"
            ).fetchall()
            unassigned_count = len(unassigned_tasks)
            technicians_list = list_technician_users()

            base_sql = """
                SELECT p.*,
                    COALESCE(u.real_name, au.display_name) as ad_real_name,
                    COALESCE(u.phone, au.phone) as ad_phone,
                    (SELECT COUNT(*) FROM tasks t WHERE t.pc_name = p.pc_name AND (t.estado != 'Hecha' OR UPPER(p.pc_name) LIKE 'PC%%GENERICA%%')) AS tareas_pendientes,
                    (
                        SELECT GROUP_CONCAT(CONCAT(np.ip_address, ' - ', np.brand_model) SEPARATOR ' | ')
                        FROM pc_network_printers pnp
                        JOIN network_printers np ON pnp.printer_id = np.id
                        WHERE pnp.pc_name = p.pc_name
                    ) as assigned_network_printer,
                    (
                        SELECT GROUP_CONCAT(np.id)
                        FROM pc_network_printers pnp
                        JOIN network_printers np ON pnp.printer_id = np.id
                        WHERE pnp.pc_name = p.pc_name
                    ) as assigned_network_printer_id,
                    0 as detected_printers_count
                FROM pcs p
                LEFT JOIN ad_users u ON (
                    LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = u.username OR
                    LOWER(p.last_user) = LOWER(u.real_name)
                )
                LEFT JOIN app_users au ON (
                    LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = au.username
                )
                WHERE 1=1
            """ + filter_sql

            sort_col_sql = sanitize_sort_column(sort_by)
            sort_dir_sql = sanitize_sort_direction(order)
            base_sql += f"""
                ORDER BY
                CASE
                    WHEN UPPER(p.pc_name) LIKE 'PC%%GENERICA%%' THEN 0
                    WHEN UPPER(p.pc_name) LIKE 'PC-GENERICA%%' THEN 0
                    WHEN UPPER(p.pc_name) LIKE 'INFRAESTRUCTURA%%' THEN 1
                    ELSE 2
                END, {sort_col_sql} {sort_dir_sql} LIMIT %s OFFSET %s
            """
            params_base = filter_params + [per_page, offset]
            pcs_data = [dict(row) for row in conn.execute(base_sql, params_base).fetchall()]

            if pcs_data:
                pc_names = [pc["pc_name"] for pc in pcs_data]
                placeholders = ",".join(["%s"] * len(pc_names))
                detected_rows = [dict(row) for row in conn.execute(
                    f"""
                    SELECT id, pc_name, printer_model, printer_port, printer_sn
                    FROM pc_detected_printers
                    WHERE is_ignored = 0
                      AND pc_name IN ({placeholders})
                      AND (printer_model IS NOT NULL AND printer_model != '' AND printer_model != 'N/A' AND UPPER(printer_model) NOT LIKE '%%SIN IMPRESORA%%')
                      AND (printer_port IS NULL OR printer_port NOT LIKE '\\\\\\\\%%')
                    """,
                    pc_names,
                ).fetchall()]

                assigned_rows = [dict(row) for row in conn.execute(
                    f"""
                    SELECT pnp.pc_name, np.serial_number, np.ip_address, np.brand_model
                    FROM pc_network_printers pnp
                    JOIN network_printers np ON pnp.printer_id = np.id
                    WHERE pnp.pc_name IN ({placeholders})
                    """,
                    pc_names,
                ).fetchall()]

                net_printers = [dict(row) for row in conn.execute(
                    "SELECT serial_number, ip_address, brand_model FROM network_printers"
                ).fetchall()]

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

                detected_by_pc = {pc_name: [] for pc_name in pc_names}
                seen_detected = set()
                for row in detected_rows:
                    detect_serial = (row.get("printer_sn") or "").strip().upper()
                    detect_port = _normalize_printer_endpoint(row.get("printer_port"))
                    detect_key = _build_printer_match_key(row.get("printer_model"), row.get("printer_port"))
                    pc_name = row["pc_name"]

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
                    if dedupe_key in seen_detected:
                        continue
                    seen_detected.add(dedupe_key)
                    detected_by_pc.setdefault(pc_name, []).append(row)

                for pc in pcs_data:
                    pc_name = pc["pc_name"]
                    main_model = (pc.get("printer_model") or "").strip()
                    main_serial = (pc.get("printer_sn") or "").strip().upper()
                    main_port = _normalize_printer_endpoint(pc.get("printer_port"))
                    main_key = _build_printer_match_key(pc.get("printer_model"), pc.get("printer_port"))
                    has_main_printer = main_model and main_model != "N/A" and "SIN IMPRESORA" not in main_model.upper()
                    assigned = assigned_by_pc.get(pc_name, {"serials": set(), "ports": set(), "keys": set()})
                    main_is_cataloged = (
                        (main_serial and main_serial != "N/A" and main_serial in catalog_serials)
                        or (main_port and main_port in catalog_ports)
                        or (main_serial and main_serial != "N/A" and main_serial in assigned["serials"])
                        or (main_port and main_port in assigned["ports"])
                        or (main_key and main_key in assigned["keys"])
                    )
                    main_dedupe_key = (pc_name, main_serial or "", main_key or "", main_port or "")
                    if has_main_printer and not main_is_cataloged and main_dedupe_key not in seen_detected:
                        detected_by_pc.setdefault(pc_name, []).append(pc)
                        seen_detected.add(main_dedupe_key)

                    detected_items = detected_by_pc.get(pc_name, [])
                    pc["detected_printers_count"] = len(detected_items)
                    pc["detected_printers_preview"] = [
                        {
                            "model": item.get("printer_model"),
                            "port": item.get("printer_port"),
                            "sn": item.get("printer_sn"),
                            "connection": (
                                "Compartida"
                                if (item.get("printer_port") or "").startswith("\\\\")
                                else "Red/IP"
                                if ("." in (item.get("printer_port") or "") or "WSD" in (item.get("printer_port") or "") or "IP_" in (item.get("printer_port") or ""))
                                else "Local/USB"
                            ),
                        }
                        for item in detected_items
                        if (pc_name, (item.get("printer_sn") or "").strip().upper() or "", _build_printer_match_key(item.get("printer_model"), item.get("printer_port")) or "", _normalize_printer_endpoint(item.get("printer_port")) or "") != main_dedupe_key
                    ]
                    pc["disk_summary_lines"] = _build_disk_summary_lines(
                        pc.get("disk_models"),
                        pc.get("disk_speeds_rpm"),
                    )

                    # Calcular días sin último reporte del script
                    lr = pc.get('last_report')
                    lr_dt = None
                    if lr:
                        if isinstance(lr, str):
                            for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
                                try:
                                    lr_dt = dt.strptime(lr, fmt)
                                    break
                                except ValueError:
                                    pass
                        elif hasattr(lr, 'timetuple'):
                            lr_dt = lr
                    if lr_dt:
                        days_diff = (dt.now() - lr_dt).days
                        pc['dias_sin_reporte'] = days_diff
                        pc['sin_reporte_30d'] = days_diff > 30
                    else:
                        pc['dias_sin_reporte'] = None
                        pc['sin_reporte_30d'] = False

            if estado != "False":
                fuero_tree = _build_fuero_tree([pc for pc in pcs_data if not _is_auxiliary_pc(pc)])

            auxiliary_pcs_raw = conn.execute(
                """SELECT p.pc_name, p.last_report,
                    (SELECT COUNT(*) FROM tasks t WHERE t.pc_name = p.pc_name AND (t.estado != 'Hecha' OR UPPER(p.pc_name) LIKE 'PC%%GENERICA%%' OR UPPER(p.pc_name) LIKE 'INFRAESTRUCTURA%%')) AS tareas_pendientes
                FROM pcs p
                WHERE p.is_active = 'True'
                AND (UPPER(p.pc_name) LIKE 'PC%%GENERICA%%' OR UPPER(p.pc_name) LIKE 'INFRAESTRUCTURA%%')
                ORDER BY CASE WHEN UPPER(p.pc_name) LIKE 'INFRAESTRUCTURA%%' THEN 0 ELSE 1 END, p.pc_name ASC"""
            ).fetchall()
            
            auxiliary_pcs = []
            for row in auxiliary_pcs_raw:
                pc_dict = dict(row)
                pc_dict["tareas"] = [dict(t) for t in conn.execute("SELECT * FROM tasks WHERE pc_name = %s AND (estado != 'Hecha' OR UPPER(pc_name) LIKE 'PC%%GENERICA%%' OR UPPER(pc_name) LIKE 'INFRAESTRUCTURA%%') ORDER BY created_at DESC", (pc_dict["pc_name"],)).fetchall()]
                auxiliary_pcs.append(pc_dict)

            kpi_total_activas = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND UPPER(pc_name) NOT LIKE 'PC-GENERICA%%' AND UPPER(pc_name) NOT LIKE 'PC%%GENERICA%%' AND UPPER(pc_name) NOT LIKE 'INFRAESTRUCTURA%%'").fetchone()["c"]
            kpi_total_graveyard = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'False'").fetchone()["c"]
            kpi_alerta_ram = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND alerta_ram_baja = 1 AND UPPER(pc_name) NOT LIKE 'PC-GENERICA%%' AND UPPER(pc_name) NOT LIKE 'PC%%GENERICA%%' AND UPPER(pc_name) NOT LIKE 'INFRAESTRUCTURA%%'").fetchone()["c"]
            kpi_sin_impresora = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND alerta_sin_impresora = 1 AND UPPER(pc_name) NOT LIKE 'PC-GENERICA%%' AND UPPER(pc_name) NOT LIKE 'PC%%GENERICA%%' AND UPPER(pc_name) NOT LIKE 'INFRAESTRUCTURA%%'").fetchone()["c"]
            kpi_impresora_red = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND alerta_impresora_red = 1 AND UPPER(pc_name) NOT LIKE 'PC-GENERICA%%' AND UPPER(pc_name) NOT LIKE 'PC%%GENERICA%%' AND UPPER(pc_name) NOT LIKE 'INFRAESTRUCTURA%%'").fetchone()["c"]

            count_network_catalog = conn.execute("SELECT COUNT(*) as c FROM network_printers").fetchone()["c"]
            count_local_printers = conn.execute("""
                SELECT COUNT(*) as c
                FROM pcs
                WHERE is_active = 'True'
                AND UPPER(pc_name) NOT IN ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA')
                AND (printer_model IS NOT NULL AND printer_model != '' AND printer_model != 'N/A' AND UPPER(printer_model) NOT LIKE '%SIN IMPRESORA%')
                AND (printer_port IS NULL OR printer_port NOT LIKE '\\\\\\\\%')
                AND alerta_impresora_red = 0
                AND pc_name NOT IN (SELECT pc_name FROM pc_network_printers)
            """).fetchone()["c"]

            kpi_total_impresoras = count_network_catalog + count_local_printers
            kpi_win7 = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND os_name LIKE %s AND UPPER(pc_name) NOT IN ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA')", ("%Windows 7%",)).fetchone()["c"]
            kpi_win10 = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND os_name LIKE %s AND UPPER(pc_name) NOT IN ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA')", ("%Windows 10%",)).fetchone()["c"]
            kpi_win11 = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND os_name LIKE %s AND UPPER(pc_name) NOT IN ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA')", ("%Windows 11%",)).fetchone()["c"]
            kpi_tareas_hoy = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado = 'Hecha' AND DATE(completed_at) = CURDATE()").fetchone()["c"]
            kpi_tareas_pendientes_total = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado != 'Hecha'").fetchone()["c"]
            kpi_incidentes = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado != 'Hecha' AND tipo_actividad = 'incidente'").fetchone()["c"]
            kpi_riesgos = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado != 'Hecha' AND tipo_actividad = 'riesgo'").fetchone()["c"]
            kpi_tareas = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado != 'Hecha' AND tipo_actividad = 'tarea'").fetchone()["c"]

            kpi_saludables = conn.execute("""
                SELECT COUNT(*) as c FROM pcs
                WHERE is_active = 'True'
                AND UPPER(pc_name) NOT IN ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA')
                AND UPPER(pc_name) NOT LIKE 'PC%%GENERICA%%' AND UPPER(pc_name) NOT LIKE 'INFRAESTRUCTURA%%'
                AND alerta_ram_baja = 0 AND IF(alerta_sin_impresora = 1 AND pc_name NOT IN (SELECT pc_name FROM pc_network_printers), 1, 0) = 0
                AND alerta_disco = 0 AND alerta_uptime = 0 AND alerta_nombre_duplicado = 0
            """).fetchone()["c"]
            kpi_alerta_media = conn.execute("""
                SELECT COUNT(*) as c FROM pcs
                WHERE is_active = 'True'
                AND UPPER(pc_name) NOT IN ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA')
                AND UPPER(pc_name) NOT LIKE 'PC%%GENERICA%%' AND UPPER(pc_name) NOT LIKE 'INFRAESTRUCTURA%%'
                AND (alerta_ram_baja + IF(alerta_sin_impresora = 1 AND pc_name NOT IN (SELECT pc_name FROM pc_network_printers), 1, 0) + alerta_disco + alerta_uptime + alerta_nombre_duplicado) = 1
            """).fetchone()["c"]
            kpi_criticas = conn.execute("""
                SELECT COUNT(*) as c FROM pcs
                WHERE is_active = 'True'
                AND UPPER(pc_name) NOT IN ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA')
                AND UPPER(pc_name) NOT LIKE 'PC%%GENERICA%%' AND UPPER(pc_name) NOT LIKE 'INFRAESTRUCTURA%%'
                AND (alerta_ram_baja + IF(alerta_sin_impresora = 1 AND pc_name NOT IN (SELECT pc_name FROM pc_network_printers), 1, 0) + alerta_disco + alerta_uptime + alerta_nombre_duplicado) >= 2
            """).fetchone()["c"]
            kpi_sin_impresora_inventario = conn.execute("""
                SELECT COUNT(*) as c FROM pcs
                WHERE is_active = 'True'
                AND UPPER(pc_name) NOT IN ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA')
                AND UPPER(pc_name) NOT LIKE 'PC%%GENERICA%%' AND UPPER(pc_name) NOT LIKE 'INFRAESTRUCTURA%%'
                AND (printer_model IS NULL OR printer_model = '' OR printer_model = 'N/A' OR UPPER(printer_model) IN ('NONE', '-') OR UPPER(printer_model) LIKE '%%SIN IMPRESORA%%')
                AND pc_name NOT IN (SELECT pc_name FROM pc_network_printers)
            """).fetchone()["c"]

            all_pcs_dropdown = [dict(row) for row in conn.execute(
                """SELECT pc_name, fuero, last_user FROM pcs WHERE is_active = 'True'
                ORDER BY CASE WHEN UPPER(pc_name) LIKE 'PC%%GENERICA%%' THEN 0 WHEN UPPER(pc_name) LIKE 'INFRAESTRUCTURA%%' THEN 1 ELSE 2 END, pc_name ASC"""
            ).fetchall()]

            backup_dir = os.environ.get("BACKUP_DIR", "/opt/inventario/backups")
            if os.path.exists(backup_dir):
                try:
                    backups = [f for f in os.listdir(backup_dir) if f.endswith('.sql.gz')]
                    if backups:
                        latest_backup = max(backups, key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)))
                        mtime = os.path.getmtime(os.path.join(backup_dir, latest_backup))
                        last_backup_info = dt.fromtimestamp(mtime).strftime("%d/%m/%y %H:%M")
                except Exception:
                    pass
            else:
                last_backup_info = "No configurado"

            ad_users_query = """
                SELECT username, real_name, phone, fuero
                FROM ad_users
                UNION
                SELECT DISTINCT
                    LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) as username,
                    last_user as real_name,
                    NULL as phone,
                    NULL as fuero
                FROM pcs
                WHERE last_user IS NOT NULL
                  AND last_user != ''
                  AND LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) NOT IN (SELECT username FROM ad_users)
                ORDER BY real_name
            """
            ad_users_list = [dict(row) for row in conn.execute(ad_users_query).fetchall()]
            app_users_list = list_app_users()
            pending_users_list = [u for u in app_users_list if not u.get("is_active")]

            pc_ports_query = conn.execute("SELECT pc_name, printer_port FROM pcs WHERE is_active = 'True'").fetchall()
            pc_ports = {row["pc_name"].upper(): (row["printer_port"] or "") for row in pc_ports_query}

            techs_actives_query = conn.execute(
                "SELECT name FROM technicians WHERE last_mobile_activity >= NOW() - INTERVAL 5 MINUTE"
            ).fetchall()
            active_mobile_techs = [row["name"] for row in techs_actives_query]

    except Exception as exc:
        print(f"Error cargando dashboard: {exc}")
        last_backup_info = "Error leyendo"

    total_pages = (total_rows + per_page - 1) // per_page if per_page > 0 else 1

    return {
        "pcs": pcs_data,
        "fuero_tree": fuero_tree,
        "auxiliary_pcs": auxiliary_pcs,
        "pc_ports": pc_ports,
        "unassigned_tasks": unassigned_tasks,
        "unassigned_count": unassigned_count,
        "kpi_total_impresoras": kpi_total_impresoras,
        "technicians": technicians_list,
        "active_mobile_techs": active_mobile_techs,
        "ad_users_list": ad_users_list,
        "app_users_list": app_users_list,
        "kpi_tareas_hoy": kpi_tareas_hoy,
        "kpi_tareas_pendientes_total": kpi_tareas_pendientes_total,
        "kpi_incidentes": kpi_incidentes,
        "kpi_riesgos": kpi_riesgos,
        "kpi_tareas": kpi_tareas,
        "all_pcs": all_pcs_dropdown,
        "kpi_total_activas": kpi_total_activas,
        "kpi_total_graveyard": kpi_total_graveyard,
        "kpi_alerta_ram": kpi_alerta_ram,
        "kpi_sin_impresora": kpi_sin_impresora,
        "kpi_impresora_red": kpi_impresora_red,
        "kpi_win7": kpi_win7,
        "kpi_win10": kpi_win10,
        "kpi_win11": kpi_win11,
        "kpi_saludables": kpi_saludables,
        "kpi_alerta_media": kpi_alerta_media,
        "kpi_criticas": kpi_criticas,
        "kpi_sin_impresora_inventario": kpi_sin_impresora_inventario,
        "q": q,
        "estado": estado,
        "alerta": alerta,
        "page": page,
        "total_pages": total_pages,
        "per_page": per_page,
        "sort_by": sort_by,
        "order": order,
        "os_param": os_param,
        "filter_tasks": filter_tasks,
        "last_backup_info": last_backup_info,
        "pending_users_list": pending_users_list,
    }
