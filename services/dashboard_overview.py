import os
from datetime import datetime as dt

from database.db_core import get_db_connection
from utils.auth import list_app_users, list_technician_users

from services.dashboard_contract import (
    normalize_alerta,
    sanitize_sort_column,
    sanitize_sort_direction,
)


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
                filter_sql += " AND (p.alerta_ram_baja + p.alerta_sin_impresora + p.alerta_disco + p.alerta_uptime + p.alerta_nombre_duplicado) >= 2"
            elif alerta == "media":
                filter_sql += " AND (p.alerta_ram_baja + p.alerta_sin_impresora + p.alerta_disco + p.alerta_uptime + p.alerta_nombre_duplicado) = 1"
            elif alerta == "ninguna":
                filter_sql += " AND p.alerta_ram_baja = 0 AND p.alerta_sin_impresora = 0 AND p.alerta_disco = 0 AND p.alerta_uptime = 0 AND p.alerta_nombre_duplicado = 0"
            elif alerta == "sin_impresora_inventario":
                filter_sql += " AND (p.printer_model IS NULL OR p.printer_model = '' OR p.printer_model = 'N/A' OR UPPER(p.printer_model) LIKE '%%SIN IMPRESORA%%') AND p.pc_name NOT IN (SELECT pc_name FROM pc_network_printers)"

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
                AND UPPER(p.pc_name) NOT LIKE 'PC%%GENERICA%%'
                AND UPPER(p.pc_name) NOT LIKE 'INFRAESTRUCTURA%%'
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
                    (
                        SELECT COUNT(*)
                        FROM pc_detected_printers dp
                        WHERE dp.pc_name = p.pc_name
                          AND dp.is_ignored = 0
                          AND (dp.printer_model IS NOT NULL AND dp.printer_model != '' AND dp.printer_model != 'N/A' AND UPPER(dp.printer_model) NOT LIKE '%%SIN IMPRESORA%%')
                          AND (dp.printer_port IS NULL OR dp.printer_port NOT LIKE '\\\\\\\\%%')
                          AND (dp.printer_sn IS NULL OR dp.printer_sn = '' OR dp.printer_sn = 'N/A' OR dp.printer_sn NOT IN (SELECT serial_number FROM network_printers WHERE serial_number IS NOT NULL AND serial_number != ''))
                    ) as detected_printers_count
                FROM pcs p
                LEFT JOIN ad_users u ON (
                    LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = u.username OR
                    LOWER(p.last_user) = LOWER(u.real_name)
                )
                LEFT JOIN app_users au ON (
                    LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = au.username
                )
                WHERE 1=1
                AND UPPER(p.pc_name) NOT LIKE 'PC%%GENERICA%%'
                AND UPPER(p.pc_name) NOT LIKE 'INFRAESTRUCTURA%%'
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

            auxiliary_pcs = [dict(row) for row in conn.execute(
                """SELECT p.pc_name, p.last_report,
                    (SELECT COUNT(*) FROM tasks t WHERE t.pc_name = p.pc_name AND (t.estado != 'Hecha' OR UPPER(p.pc_name) LIKE 'PC%%GENERICA%%')) AS tareas_pendientes
                FROM pcs p
                WHERE p.is_active = 'True'
                AND (UPPER(p.pc_name) = 'PC GENERICA' OR UPPER(p.pc_name) = 'INFRAESTRUCTURA')"""
            ).fetchall()]

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
                AND alerta_ram_baja = 0 AND alerta_sin_impresora = 0
                AND alerta_disco = 0 AND alerta_uptime = 0 AND alerta_nombre_duplicado = 0
            """).fetchone()["c"]
            kpi_alerta_media = conn.execute("""
                SELECT COUNT(*) as c FROM pcs
                WHERE is_active = 'True'
                AND UPPER(pc_name) NOT IN ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA')
                AND UPPER(pc_name) NOT LIKE 'PC%%GENERICA%%' AND UPPER(pc_name) NOT LIKE 'INFRAESTRUCTURA%%'
                AND (alerta_ram_baja + alerta_sin_impresora + alerta_disco + alerta_uptime + alerta_nombre_duplicado) = 1
            """).fetchone()["c"]
            kpi_criticas = conn.execute("""
                SELECT COUNT(*) as c FROM pcs
                WHERE is_active = 'True'
                AND UPPER(pc_name) NOT IN ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA')
                AND UPPER(pc_name) NOT LIKE 'PC%%GENERICA%%' AND UPPER(pc_name) NOT LIKE 'INFRAESTRUCTURA%%'
                AND (alerta_ram_baja + alerta_sin_impresora + alerta_disco + alerta_uptime + alerta_nombre_duplicado) >= 2
            """).fetchone()["c"]
            kpi_sin_impresora_inventario = conn.execute("""
                SELECT COUNT(*) as c FROM pcs
                WHERE is_active = 'True'
                AND UPPER(pc_name) NOT IN ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA')
                AND UPPER(pc_name) NOT LIKE 'PC%%GENERICA%%' AND UPPER(pc_name) NOT LIKE 'INFRAESTRUCTURA%%'
                AND (printer_model IS NULL OR printer_model = '' OR printer_model = 'N/A' OR UPPER(printer_model) LIKE '%%SIN IMPRESORA%%')
                AND pc_name NOT IN (SELECT pc_name FROM pc_network_printers)
            """).fetchone()["c"]

            all_pcs_dropdown = [dict(row) for row in conn.execute(
                """SELECT pc_name, fuero, last_user FROM pcs WHERE is_active = 'True'
                ORDER BY CASE WHEN UPPER(pc_name) LIKE 'PC%%GENERICA%%' THEN 0 WHEN UPPER(pc_name) LIKE 'INFRAESTRUCTURA%%' THEN 1 ELSE 2 END, pc_name ASC"""
            ).fetchall()]

            backup_dir = "/opt/inventario/backups"
            if os.path.exists(backup_dir):
                try:
                    backups = [f for f in os.listdir(backup_dir) if f.endswith('.sql.gz')]
                    if backups:
                        latest_backup = max(backups, key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)))
                        mtime = os.path.getmtime(os.path.join(backup_dir, latest_backup))
                        last_backup_info = dt.fromtimestamp(mtime).strftime("%d/%m/%y %H:%M")
                except Exception:
                    pass

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
