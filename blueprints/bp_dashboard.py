from flask import Blueprint, render_template, request, redirect, url_for, abort, send_file, flash
import os
from datetime import datetime as dt
from database.db_core import get_db_connection
import socket
from utils.constants import FUERO_MAPPING, detect_fuero
import datetime
from datetime import datetime as dt
from io import BytesIO
from openpyxl import Workbook
from utils.constants import FUERO_MAPPING, FUERO_COLORS
from utils.auth import current_username, delete_app_user, list_app_users, list_technician_users, superuser_required, upsert_app_user

bp_dashboard = Blueprint('dashboard', __name__)

@bp_dashboard.route("/cementerio")
def view_cementerio():
    return redirect(url_for("dashboard.dashboard", estado="False"))

@bp_dashboard.route("/graficos")
def view_graphics():
    """Nueva pÃ¡gina dedicada a KPIs y GrÃ¡ficos."""
    try:
        with get_db_connection() as conn:
            kpi_total_activas = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND UPPER(pc_name) NOT LIKE 'PC-GENERICA%%' AND UPPER(pc_name) NOT LIKE 'PC GENERICA%%' AND UPPER(pc_name) NOT LIKE 'INFRAESTRUCTURA%%'").fetchone()["c"]
            kpi_total_graveyard = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'False'").fetchone()["c"]
            kpi_alerta_ram = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND alerta_ram_baja = 1 AND UPPER(pc_name) NOT LIKE 'PC-GENERICA%%' AND UPPER(pc_name) NOT LIKE 'PC GENERICA%%' AND UPPER(pc_name) NOT LIKE 'INFRAESTRUCTURA%%'").fetchone()["c"]
            kpi_sin_impresora = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND alerta_sin_impresora = 1 AND UPPER(pc_name) NOT LIKE 'PC-GENERICA%%' AND UPPER(pc_name) NOT LIKE 'PC GENERICA%%' AND UPPER(pc_name) NOT LIKE 'INFRAESTRUCTURA%%'").fetchone()["c"]
            kpi_impresora_red = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND alerta_impresora_red = 1 AND UPPER(pc_name) NOT LIKE 'PC-GENERICA%%' AND UPPER(pc_name) NOT LIKE 'PC GENERICA%%' AND UPPER(pc_name) NOT LIKE 'INFRAESTRUCTURA%%'").fetchone()["c"]
            kpi_win7 = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND os_name LIKE %s AND UPPER(pc_name) NOT LIKE 'PC%%GENERICA%%' AND UPPER(pc_name) NOT LIKE 'INFRAESTRUCTURA%%'", ("%Windows 7%",)).fetchone()["c"]
            kpi_win10 = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND os_name LIKE %s AND UPPER(pc_name) NOT LIKE 'PC%%GENERICA%%' AND UPPER(pc_name) NOT LIKE 'INFRAESTRUCTURA%%'", ("%Windows 10%",)).fetchone()["c"]
            kpi_win11 = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND os_name LIKE %s AND UPPER(pc_name) NOT LIKE 'PC%%GENERICA%%' AND UPPER(pc_name) NOT LIKE 'INFRAESTRUCTURA%%'", ("%Windows 11%",)).fetchone()["c"]
            kpi_tareas_hoy = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado = 'Hecha' AND DATE(completed_at) = CURDATE()").fetchone()["c"]
            kpi_tareas_pendientes_count = conn.execute("SELECT COUNT(DISTINCT pc_name) as c FROM tasks WHERE estado != 'Hecha' AND pc_name IS NOT NULL AND pc_name != ''").fetchone()["c"]
            kpi_tareas_pendientes_total = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado != 'Hecha'").fetchone()["c"]

            rows_cats = conn.execute("SELECT categoria, COUNT(*) as c FROM tasks GROUP BY categoria").fetchall()
            cat_labels = []
            cat_values = []
            for r in rows_cats:
                cat_name = r["categoria"] if r["categoria"] else "Sin CategorÃ­a"
                if cat_name == "General": continue
                cat_labels.append(cat_name)
                cat_values.append(r["c"])
            
    except Exception as e:
        print(f"Error en graficos: {e}")
        kpi_total_activas = kpi_total_graveyard = kpi_alerta_ram = kpi_sin_impresora = kpi_impresora_red = 0
        kpi_win7 = kpi_win10 = kpi_tareas_hoy = kpi_tareas_pendientes_count = kpi_tareas_pendientes_total = 0
        cat_labels = []
        cat_values = []

    return render_template(
        "graficos.html",
        kpi_total_activas=kpi_total_activas,
        kpi_total_graveyard=kpi_total_graveyard,
        kpi_alerta_ram=kpi_alerta_ram,
        kpi_sin_impresora=kpi_sin_impresora,
        kpi_impresora_red=kpi_impresora_red,
        kpi_win7=kpi_win7,
        kpi_win10=kpi_win10,
        kpi_win11=kpi_win11,
        kpi_tareas_hoy=kpi_tareas_hoy,
        kpi_tareas_pendientes_count=kpi_tareas_pendientes_count,
        kpi_tareas_pendientes_total=kpi_tareas_pendientes_total,
        cat_labels=cat_labels,
        cat_values=cat_values,
        hostname=socket.gethostname()
    )

@bp_dashboard.route("/", methods=["GET"])
def dashboard():
    """Lista todas las PCs (activas y en cementerio) + KPIs + filtros + paginado."""
    pcs_data = []
    kpi_tareas_hoy = 0
    kpi_tareas_pendientes_total = 0

    q = request.args.get("q", "").strip()
    estado = request.args.get("estado", "True").strip()
    alerta = request.args.get("alerta", "").strip()
    os_param = request.args.get("os", "").strip()
    filter_tasks = request.args.get("filter_tasks", "").strip()
    sort_by = request.args.get("sort_by", "pc_name").strip()
    order = request.args.get("order", "asc").strip()

    try: page = int(request.args.get("page", 1))
    except ValueError: page = 1
    
    try: per_page = int(request.args.get("per_page", 25))
    except ValueError: per_page = 25
        
    offset = (page - 1) * per_page
    total_rows = 0

    try:
        with get_db_connection() as conn:
            # Construir filtros comunes
            filter_sql = ""
            filter_params = []
            if q:
                filter_sql += " AND (p.pc_name LIKE %s OR p.last_user LIKE %s OR p.ip_address LIKE %s OR p.fuero LIKE %s OR p.os_name LIKE %s OR u.real_name LIKE %s)"
                filter_params.extend([f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%"])
            
            if estado in ("True", "False"):
                filter_sql += " AND p.is_active = %s"
                filter_params.append(estado)
            if alerta == "ram":
                filter_sql += " AND p.alerta_ram_baja = 1"
            elif alerta == "sinimp":
                filter_sql += " AND p.alerta_sin_impresora = 1"
            elif alerta == "red":
                filter_sql += " AND p.alerta_impresora_red = 1"
            
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
                filter_sql += " AND (SELECT COUNT(*) FROM tasks t WHERE t.pc_name = p.pc_name AND t.estado != 'Hecha') > 0"

            # Ejecutar conteo
            count_sql = """
                SELECT COUNT(*) as c 
                FROM pcs p 
                LEFT JOIN ad_users u ON (
                    LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = u.username OR 
                    LOWER(p.last_user) = LOWER(u.real_name)
                )
                WHERE 1=1 
                AND UPPER(p.pc_name) NOT LIKE 'PC%%GENERICA%%' 
                AND UPPER(p.pc_name) NOT LIKE 'INFRAESTRUCTURA%%'
            """ + filter_sql
            total_rows = conn.execute(count_sql, filter_params).fetchone()["c"]

            unassigned_tasks = conn.execute("SELECT * FROM tasks WHERE (pc_name IS NULL OR pc_name = '') AND estado != 'Hecha' ORDER BY created_at DESC").fetchall()
            unassigned_count = len(unassigned_tasks)
            technicians_list = list_technician_users()

            base_sql = """
                SELECT p.*, u.real_name as ad_real_name, u.phone as ad_phone,
                    (SELECT COUNT(*) FROM tasks t WHERE t.pc_name = p.pc_name AND (t.estado != 'Hecha' OR UPPER(p.pc_name) LIKE 'PC%%GENERICA%%')) AS tareas_pendientes,
                    (
                        SELECT CONCAT(np.ip_address, ' - ', np.brand_model) 
                        FROM pc_network_printers pnp 
                        JOIN network_printers np ON pnp.printer_id = np.id 
                        WHERE pnp.pc_name = p.pc_name 
                        LIMIT 1
                    ) as assigned_network_printer,
                    (
                        SELECT np.id 
                        FROM pc_network_printers pnp 
                        JOIN network_printers np ON pnp.printer_id = np.id 
                        WHERE pnp.pc_name = p.pc_name 
                        LIMIT 1
                    ) as assigned_network_printer_id
                FROM pcs p
                LEFT JOIN ad_users u ON (
                    LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = u.username OR 
                    LOWER(p.last_user) = LOWER(u.real_name)
                )
                WHERE 1=1 
                AND UPPER(p.pc_name) NOT LIKE 'PC%%GENERICA%%' 
                AND UPPER(p.pc_name) NOT LIKE 'INFRAESTRUCTURA%%'
            """ + filter_sql
            
            allowed_sort_cols = {
                "pc_name": "p.pc_name", "last_user": "p.last_user", "fuero": "p.fuero",
                "motherboard_model": "p.motherboard_model", "os_name": "p.os_name",
                "processor": "p.processor", "ram_gb": "p.ram_gb", "ram_detalles": "p.ram_detalles",
                "disk_models": "p.disk_models", "printer_model": "p.printer_model",
                "monitors": "p.monitors", "ip_address": "p.ip_address"
            }
            sort_col_sql = allowed_sort_cols.get(sort_by, "p.pc_name")
            sort_dir_sql = "DESC" if order == "desc" else "ASC"
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

            # Fetch auxiliary PCs separately so they always appear as cards even with pagination/filters
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
            # Contador de Impresoras (LÃ³gica Refinada: Red Ãšnicas + Locales por PC)
            # Primero: Cantidad de impresoras en el catÃ¡logo de Red
            count_network_catalog = conn.execute("SELECT COUNT(*) as c FROM network_printers").fetchone()["c"]
            
            # Segundo: PCs activas con impresora local (excluyendo las que sabemos que son de red por puerto UNC o alerta o que ya estÃ¡n en el catÃ¡logo)
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

            all_pcs_dropdown = [dict(row) for row in conn.execute(
                """SELECT pc_name, fuero, last_user FROM pcs WHERE is_active = 'True' 
                ORDER BY CASE WHEN UPPER(pc_name) LIKE 'PC%%GENERICA%%' THEN 0 WHEN UPPER(pc_name) LIKE 'INFRAESTRUCTURA%%' THEN 1 ELSE 2 END, pc_name ASC"""
            ).fetchall()]
            
            # --- STATUS ULTIMO BACKUP ---
            last_backup_info = "Sin backups"
            backup_dir = "/opt/inventario/backups"
            if os.path.exists(backup_dir):
                try:
                    backups = [f for f in os.listdir(backup_dir) if f.endswith('.sql.gz')]
                    if backups:
                        latest_backup = max(backups, key=lambda x: os.path.getmtime(os.path.join(backup_dir, x)))
                        mtime = os.path.getmtime(os.path.join(backup_dir, latest_backup))
                        last_backup_info = dt.fromtimestamp(mtime).strftime('%d/%m/%y %H:%M')
                except Exception:
                    pass
            # ----------------------------
            
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
            # Usuarios AD que se registraron pero aún no fueron aprobados
            pending_users_list = [u for u in app_users_list if not u.get("is_active")]
            
            # --- DICCIONARIO DE PUERTOS PARA HOST OFFLINE ---
            pc_ports_query = conn.execute("SELECT pc_name, printer_port FROM pcs WHERE is_active = 'True'").fetchall()
            pc_ports = {row["pc_name"].upper(): (row["printer_port"] or "") for row in pc_ports_query}
            # ------------------------------------------------
            
            # --- TECNICOS ACTIVOS MOVILES ---
            techs_actives_query = conn.execute("SELECT name FROM technicians WHERE last_mobile_activity >= NOW() - INTERVAL 5 MINUTE").fetchall()
            active_mobile_techs = [row["name"] for row in techs_actives_query]
            # ------------------------------------------------

    except Exception as exc:
        print(f"Error cargando dashboard: {exc}")
        pc_ports = {}
        pending_users_list = []
        pcs_data = auxiliary_pcs = technicians_list = unassigned_tasks = all_pcs_dropdown = ad_users_list = app_users_list = active_mobile_techs = []
        total_rows = kpi_total_activas = kpi_total_graveyard = kpi_alerta_ram = kpi_sin_impresora = 0
        kpi_impresora_red = kpi_total_impresoras = kpi_win7 = kpi_win10 = kpi_win11 = kpi_tareas_hoy = kpi_tareas_pendientes_total = unassigned_count = 0
        last_backup_info = "Error leyendo"

    total_pages = (total_rows + per_page - 1) // per_page if per_page > 0 else 1

    return render_template(
        "index.html",
        pcs=pcs_data,
        auxiliary_pcs=auxiliary_pcs,
        pc_ports=pc_ports,
        server_url=request.host_url,
        unassigned_tasks=unassigned_tasks,
        unassigned_count=unassigned_count,
        kpi_total_impresoras=kpi_total_impresoras,
        technicians=technicians_list,
        active_mobile_techs=active_mobile_techs,
        ad_users_list=ad_users_list,
        app_users_list=app_users_list,
        kpi_tareas_hoy=kpi_tareas_hoy,
        kpi_tareas_pendientes_total=kpi_tareas_pendientes_total,
        all_pcs=all_pcs_dropdown,
        kpi_total_activas=kpi_total_activas,
        kpi_total_graveyard=kpi_total_graveyard,
        kpi_alerta_ram=kpi_alerta_ram,
        kpi_sin_impresora=kpi_sin_impresora,
        kpi_impresora_red=kpi_impresora_red,
        kpi_win7=kpi_win7,
        kpi_win10=kpi_win10,
        kpi_win11=kpi_win11,
        q=q,
        estado=estado,
        alerta=alerta,
        page=page,
        total_pages=total_pages,
        fuero_colors=FUERO_COLORS,
        per_page=per_page,
        sort_by=sort_by,
        order=order,
        os_param=os_param,
        filter_tasks=filter_tasks,
        last_backup_info=last_backup_info,
        pending_users_list=pending_users_list
    )

@bp_dashboard.route("/export", methods=["GET", "POST"])
def export_inventory():
    """GET: muestra formulario. POST: genera Excel con campos seleccionados."""
    if request.method == "GET":
        return render_template("export_inventory.html")
    
    campos_seleccionados = request.form.getlist("campos")
    if not campos_seleccionados:
        # Añadimos fuero y printer_model por defecto si no hay selección
        campos_seleccionados = ["pc_name", "last_user", "fuero", "os_name", "processor", "ram_gb", "ip_address", "printer_model"]
    
    with get_db_connection() as conn:
        # Mejoramos la consulta para traer info de red e impresoras compartidas
        sql = """
            SELECT p.*,
                (SELECT GROUP_CONCAT(CONCAT(np.brand_model, ' (', np.ip_address, ')') SEPARATOR ' | ') 
                 FROM pc_network_printers pnp 
                 JOIN network_printers np ON pnp.printer_id = np.id 
                 WHERE pnp.pc_name = p.pc_name) as net_printers_info,
                (SELECT COUNT(*) FROM pcs p2 WHERE p2.is_active = 'True' AND p2.printer_port LIKE CONCAT('%\\\\\\\\', p.pc_name, '%')) as clients_count
            FROM pcs p 
            WHERE p.is_active = 'True' 
            ORDER BY p.fuero ASC, p.pc_name ASC
        """
        rows = conn.execute(sql).fetchall()
    if not rows: return "Sin datos", 404
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Inventario"
    
    # Mapeo para cabeceras amigables
    headers_map = {
        "pc_name": "Nombre PC", "last_user": "Último Usuario", "fuero": "Fuero / Área",
        "os_name": "Sistema Operativo", "processor": "Procesador", "ram_gb": "RAM (GB)",
        "ip_address": "Dirección IP", "printer_model": "Impresora", "motherboard_model": "Motherboard",
        "monitors": "Monitores", "disk_models": "Discos", "last_report": "Última Sincro"
    }
    
    ws.append([headers_map.get(c, c) for c in campos_seleccionados])
    
    for row in rows:
        # Lógica para campo Impresora enriquecido
        printer_str = row["printer_model"] or "-"
        port = row["printer_port"] or ""
        
        if port.startswith("\\\\"):
            # Es una impresora compartida desde otro host
            host = port.split("\\")[2] if len(port.split("\\")) > 2 else "Red"
            printer_str = f"COMPARTIDA desde {host} ({printer_str})"
        elif row["net_printers_info"]:
            # Es una impresora de red del catálogo
            printer_str = f"RED: {row['net_printers_info']}"
        
        # Si esta PC comparte a otros
        if row["clients_count"] > 0:
            printer_str = f"Local y COMPARTIDA (Hosting a {row['clients_count']} PCs) - {printer_str}"
        elif printer_str != "-" and not printer_str.startswith(("COMPARTIDA", "RED:")):
            printer_str = f"Local: {printer_str}"

        # Creamos la fila mapeando campos
        fila = []
        for campo in campos_seleccionados:
            if campo == "printer_model":
                fila.append(printer_str)
            else:
                fila.append(row[campo])
        ws.append(fila)
    
    # --- AUTO-AJUSTE DE COLUMNAS ---
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except: pass
        ws.column_dimensions[column].width = max_length + 2
    # -------------------------------

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"Inventario_Completo_{dt.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
    )

@bp_dashboard.route("/export_inventory_pdf", methods=["POST"])
def export_inventory_pdf():
    from services.reporting import PDFReport, format_date_es
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT p.pc_name, p.last_user, p.fuero, p.os_name, p.printer_model, p.printer_port, p.processor, p.ram_gb, p.ip_address,
                   (SELECT GROUP_CONCAT(np.brand_model) FROM pc_network_printers pnp JOIN network_printers np ON pnp.printer_id = np.id WHERE pnp.pc_name = p.pc_name) as net_printers,
                   (SELECT COUNT(*) FROM pcs p2 WHERE p2.is_active = 'True' AND p2.printer_port LIKE CONCAT('%\\\\\\\\', p.pc_name, '%')) as is_sharing_host
            FROM pcs p 
            WHERE p.is_active = 'True' 
              AND UPPER(p.pc_name) NOT IN ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA') 
            ORDER BY p.fuero ASC, p.pc_name ASC
        """).fetchall()
    
    pdf = PDFReport(title="Inventario Físico - Inventario GOLD", orientation='L')
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Generado el: {format_date_es(datetime.datetime.now())}", 0, 1, 'C')
    pdf.ln(2)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Total Equipos Activos: {len(rows)}", 0, 1, 'C')
    pdf.ln(4)
    
    # Headers optimizados (A4 Landscape = 277 total útil)
    headers = ["Nombre PC", "Usuario", "Fuero/Área", "OS", "Impresora", "Procesador", "RAM", "IP Address"]
    # [PC:31, User:28, Fuero:44, OS:28, Prn:38, CPU:64, RAM:14, IP:30] = 277
    widths = [31, 28, 44, 28, 38, 64, 14, 30]
    
    pdf.set_font("Arial", "B", 8)
    pdf.set_fill_color(30, 41, 59) # Slate 800
    pdf.set_text_color(255)
    
    for i, h in enumerate(headers):
        pdf.cell(widths[i], 8, h, 1, 0, 'C', fill=True)
    pdf.ln()
    
    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(0)
    
    def draw_multiline_row(pdf, cols, widths, row_height=6):
        # 1. Calcular altura necesaria (buscando el campo con más líneas)
        max_lines = 1
        split_cols = []
        for i, text in enumerate(cols):
            lines = pdf.multi_cell(widths[i], row_height, str(text), split_only=True)
            max_lines = max(max_lines, len(lines))
            split_cols.append(lines)
        
        h_row = max_lines * row_height
        
        # 2. Salto de página preventivo
        if (pdf.get_y() + h_row) > 190: 
            pdf.add_page()
            # Redibujar cabecera
            pdf.set_font("Arial", "B", 8)
            pdf.set_fill_color(30, 41, 59)
            pdf.set_text_color(255)
            for i, h in enumerate(headers): pdf.cell(widths[i], 8, h, 1, 0, 'C', fill=True)
            pdf.ln()
            pdf.set_font("Arial", "", 8)
            pdf.set_text_color(0)

        # 3. Dibujar las celdas de la fila
        x_start, y_start = pdf.get_x(), pdf.get_y()
        for i, lines in enumerate(split_cols):
            curr_x = x_start + sum(widths[:i])
            pdf.set_xy(curr_x, y_start)
            # Dibujar borde de la celda
            pdf.rect(curr_x, y_start, widths[i], h_row)
            cell_text = "\n".join(lines)
            pdf.multi_cell(widths[i], row_height, cell_text, 0, 'L')
        
        pdf.set_xy(x_start, y_start + h_row)

    for row in rows:
        # Limpieza de datos
        raw_user = row["last_user"] or "N/A"
        user = raw_user.split("\\")[-1] if "\\" in raw_user else raw_user
        
        os_str = (row["os_name"] or "N/A").replace("Microsoft ", "")
        
        # --- Lógica de Impresora Detallada ---
        printer = row["printer_model"] or "-"
        port = row["printer_port"] or ""
        
        if port.startswith("\\\\"):
            # Caso: Impresora en red compartida por otra PC
            host_srv = port.split("\\")[2] if len(port.split("\\")) > 2 else "Server"
            printer = f"Compartida (desde {host_srv})"
        elif row["net_printers"]:
            # Caso: Impresora de red directa (Catálogo)
            printer = f"Red ({row['net_printers']})"
        elif printer.upper() in ("N/A", "SIN IMPRESORA", "NONE", "-"):
            printer = "-"
        else:
            # Es local, ver si la comparte
            if row["is_sharing_host"] > 0:
                printer = f"Local y Compartida (Hosting a {row['is_sharing_host']} PCs) - {printer}"
            else:
                printer = f"Local ({printer})"
        # -------------------------------------
        
        data_to_draw = [
            str(row["pc_name"]),
            str(user),
            str(row["fuero"] or "N/A"),
            str(os_str),
            str(printer),
            str(row["processor"] or "N/A"),
            f'{row["ram_gb"]}G',
            str(row["ip_address"])
        ]
        
        draw_multiline_row(pdf, data_to_draw, widths)

    output = BytesIO()
    pdf_bytes = pdf.output()
    output.write(pdf_bytes)
    output.seek(0)
    
    return send_file(
        output,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"Inventario_Fisico_{dt.now().strftime('%Y%m%d')}.pdf",
    )

@bp_dashboard.route("/download_db")
def download_db():
    return "Backup de BD no disponible en modo MySQL. Use mysqldump desde el servidor.", 503

@bp_dashboard.route("/decommission/<string:pc_name>", methods=["POST"])
def decommission_pc(pc_name):
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE pcs SET is_active = 'False' WHERE pc_name = %s", (pc_name,)
        )
        conn.commit()
    return redirect(url_for("dashboard.dashboard"))

@bp_dashboard.route("/reactivate/<pc_name>", methods=["POST"])
def reactivate_pc(pc_name):
    """Reactivar una PC (sacarla del cementerio)."""
    try:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE pcs SET is_active = 'True' WHERE pc_name = %s",
                (pc_name,),
            )
            conn.commit()
    except Exception as exc:
        print(f"Error reactivating PC {pc_name}: {exc}")

    return redirect(url_for("dashboard.dashboard"))

@bp_dashboard.route("/refresh_fueros", methods=["POST"])
def refresh_fueros():
    """Recalcula el fuero para todas las PCs basÃ¡ndose en el nombre."""
    try:
        with get_db_connection() as conn:
            pcs = conn.execute("SELECT pc_name FROM pcs").fetchall()
            count = 0
            for pc in pcs:
                name = pc["pc_name"]
                nuevo_fuero = detect_fuero(name)
                conn.execute(
                    "UPDATE pcs SET fuero = %s WHERE pc_name = %s",
                    (nuevo_fuero, name)
                )
                count += 1
            conn.commit()
        print(f"Fueros actualizados para {count} PCs.")
    except Exception as exc:
        print(f"Error refreshing fueros: {exc}")

    return redirect(url_for("dashboard.dashboard"))

@bp_dashboard.route("/delete_permanent/<string:pc_name>", methods=["POST"])
def delete_permanent_pc(pc_name):
    """Borrado definitivo de una PC y sus tareas asociadas."""
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM tasks WHERE pc_name = %s", (pc_name,))
            conn.execute("DELETE FROM pcs WHERE pc_name = %s", (pc_name,))
            conn.execute(
                "INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (pc_name, 'PERMANENT_DELETE', 'Active/Inactive', 'DELETED', current_username(), "BORRADO_PERMANENTE", request.remote_addr)
            )
            conn.commit()
    except Exception as exc:
        print(f"Error deleting PC {pc_name}: {exc}")

    return redirect(url_for("dashboard.dashboard"))



@bp_dashboard.route("/pc/<pc_name>")
def pc_detail(pc_name):
    with get_db_connection() as conn:
        pc = conn.execute("""
            SELECT p.*, u.real_name as ad_real_name 
            FROM pcs p 
            LEFT JOIN ad_users u ON LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = u.username 
            WHERE p.pc_name = %s
        """, (pc_name,)).fetchone()
        tareas = conn.execute("SELECT id, pc_name, created_at, descripcion, estado, solicitante, assigned_to FROM tasks WHERE pc_name = %s ORDER BY created_at DESC", (pc_name,)).fetchall()
        technicians = list_technician_users()
        ad_users_list = [dict(row) for row in conn.execute(
            """
            SELECT username, real_name, phone, fuero
            FROM ad_users
            UNION
            SELECT DISTINCT LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) as username,
                            last_user as real_name,
                            NULL as phone,
                            NULL as fuero
            FROM pcs
            WHERE last_user IS NOT NULL AND last_user != ''
              AND LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) NOT IN (SELECT username FROM ad_users)
            ORDER BY real_name
            """
        ).fetchall()]
        audit_logs = conn.execute("SELECT * FROM audit_logs WHERE pc_name = %s ORDER BY changed_at DESC", (pc_name,)).fetchall()
        all_pcs = conn.execute("SELECT pc_name, fuero, last_user FROM pcs WHERE is_active='True' ORDER BY pc_name").fetchall()
        
        # Buscar Data de la UPS asignada
        pc_ups_list = conn.execute('''
            SELECT u.*, b.serial_number as battery_code 
            FROM ups_inventory u
            LEFT JOIN components b ON u.assigned_battery_id = b.id
            WHERE u.assigned_pc = %s
        ''', (pc_name,)).fetchall()
        
        sharing_pc_data = None
        if pc and pc["printer_port"] and pc["printer_port"].startswith("\\\\"):
            # Extraer el nombre de la PC desde una ruta UNC (ej: \\SISTEMAS-105\HP Deskjet)
            parts = pc["printer_port"].split("\\")
            if len(parts) >= 3:
                potential_host = parts[2].upper()
                sharing_pc_data = conn.execute(
                    "SELECT pc_name, is_active, printer_port, printer_sn, printer_model FROM pcs WHERE UPPER(pc_name) = %s OR ip_address = %s LIMIT 1", 
                    (potential_host, potential_host)
                ).fetchone()
        
        # PCs que usan a esta PC como host de impresora (cascada)
        clients_using_this_printer = []
        if pc and pc["pc_name"] and (pc["pc_name"].upper() not in ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA')):
            # Patrones para buscar clientes
            pat_name = f"%\\\\\\\\{pc['pc_name'].upper()}\\\\%"
            pat_ip = f"%\\\\\\\\{pc['ip_address']}\\\\%" if pc['ip_address'] and pc['ip_address'] != 'N/A' else None
            
            query = "SELECT pc_name FROM pcs WHERE is_active='True' AND UPPER(printer_port) LIKE %s"
            params = [pat_name]
            if pat_ip:
                query += " OR UPPER(printer_port) LIKE %s"
                params.append(pat_ip)
            
            clients_using_this_printer = conn.execute(query, tuple(params)).fetchall()
        
        # UPS Disponibles en caso de querer asignarle una (UPS sin asignar)
        available_ups = conn.execute("SELECT id, code, model FROM ups_inventory WHERE assigned_pc IS NULL").fetchall()
        
        # Buscar componentes asignados a la PC (y sus hijos)
        pc_components = conn.execute('''
            SELECT id, serial_number, component_type, brand_model, status, assigned_to_component_id 
            FROM components 
            WHERE assigned_pc = %s
            ORDER BY assigned_to_component_id ASC, component_type
        ''', (pc_name,)).fetchall()
        
        # Componentes en Stock disponibles para asignar
        available_components = conn.execute('''
            SELECT id, serial_number, component_type, brand_model 
            FROM components 
            WHERE status = 'Stock' AND component_type NOT LIKE 'Bat%'
        ''').fetchall()
        
        # Baterias disponibles para asignar a la UPS de esta PC
        baterias_disponibles = conn.execute("SELECT id, serial_number as code, brand_model FROM components WHERE component_type LIKE 'Bat%' AND status = 'Stock'").fetchall()

        # Impresoras de red asignadas a esta PC
        assigned_network_printers = conn.execute('''
            SELECT np.id, np.ip_address, np.brand_model, np.serial_number 
            FROM network_printers np
            JOIN pc_network_printers pnp ON np.id = pnp.printer_id
            WHERE pnp.pc_name = %s
        ''', (pc_name,)).fetchall()
        
        # Impresoras de red disponibles para asignar (todas)
        available_network_printers = conn.execute("SELECT id, ip_address, brand_model FROM network_printers ORDER BY ip_address").fetchall()

    if pc is None: abort(404)
    return render_template("pc_detail.html", pc=pc, tareas=tareas, technicians=technicians, ad_users_list=ad_users_list, audit_logs=audit_logs, all_pcs=all_pcs, fuero_colors=FUERO_COLORS, pc_ups_list=pc_ups_list, available_ups=available_ups, pc_components=pc_components, available_components=available_components, baterias_disponibles=baterias_disponibles, sharing_pc=sharing_pc_data, clients_using_this_printer=clients_using_this_printer, assigned_network_printers=assigned_network_printers, available_network_printers=available_network_printers)

@bp_dashboard.route("/pc/<pc_name>/update_infrastructure", methods=["POST"])
def update_pc_infrastructure(pc_name):
    """Actualiza los datos de infraestructura de una PC."""
    building = request.form.get("building", "").strip()
    floor = request.form.get("floor", "").strip()
    switch_name = request.form.get("switch_name", "").strip()
    switch_port = request.form.get("switch_port", "").strip()
    pachera_name = request.form.get("pachera_name", "").strip()
    pachera_port = request.form.get("pachera_port", "").strip()
    
    try:
        with get_db_connection() as conn:
            old_pc = conn.execute("SELECT * FROM pcs WHERE pc_name = %s", (pc_name,)).fetchone()
            conn.execute(
                """UPDATE pcs SET building = %s, floor = %s, switch_name = %s, switch_port = %s, pachera_name = %s, pachera_port = %s WHERE pc_name = %s""",
                (building, floor, switch_name, switch_port, pachera_name, pachera_port, pc_name)
            )
            if old_pc:
                changes = [
                    ("building", old_pc["building"], building), ("floor", old_pc["floor"], floor),
                    ("switch_name", old_pc["switch_name"], switch_name), ("switch_port", old_pc["switch_port"], switch_port),
                    ("pachera_name", old_pc["pachera_name"], pachera_name), ("pachera_port", old_pc["pachera_port"], pachera_port)
                ]
                for field, old, new in changes:
                    old_str = str(old) if old is not None else ""
                    new_str = str(new) if new is not None else ""
                    if old_str != new_str:
                        conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                                     (pc_name, field, old_str, new_str, current_username(), "EDICION_INFRAESTRUCTURA", request.remote_addr))
            conn.commit()
        return redirect(url_for("dashboard.pc_detail", pc_name=pc_name))
    except Exception as e:
        return f"Error actualizando infraestructura: {e}", 500

@bp_dashboard.route("/actividad")
def global_activity():
    """Muestra el historial global de actividad de todas las PCs e Infraestructura."""
    with get_db_connection() as conn:
        # Traer los Ãºltimos 1000 registros para no sobrecargar
        logs = conn.execute("""
            SELECT id, pc_name, field, old_value, new_value, user_name, action_type, ip_address, changed_at 
            FROM audit_logs 
            ORDER BY changed_at DESC 
            LIMIT 1000
        """).fetchall()
    return render_template("activity_logs.html", logs=logs)

@bp_dashboard.route("/admin/users/debug")
@superuser_required
def debug_users():
    from database.db_core import get_db_connection
    from flask import jsonify
    with get_db_connection() as conn:
        app_users = conn.execute("SELECT username, display_name FROM app_users").fetchall()
        ad_users = conn.execute("SELECT username, real_name, fuero FROM ad_users").fetchall()
    return jsonify({
        "app_users": [dict(r) for r in app_users],
        "ad_users": [dict(r) for r in ad_users]
    })


@bp_dashboard.route("/update_user_phone", methods=["POST"])
@superuser_required
def update_user_phone():
    """Actualiza el telÃ©fono de un usuario desde el modal."""
    username = request.form.get("username", "").strip().lower()
    old_username = request.form.get("old_username", "").strip().lower()
    realname = request.form.get("realname", "").strip()
    phone = request.form.get("phone", "").strip()
    fuero = request.form.get("fuero", "").strip()

    if username:
        try:
            with get_db_connection() as conn:
                # Si el usuario cambiÃ³ de nombre (rename), borramos el registro anterior
                if old_username and old_username != username:
                    conn.execute("DELETE FROM ad_users WHERE username = %s", (old_username,))

                conn.execute("""
                    INSERT INTO ad_users (username, real_name, phone, fuero)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        phone = VALUES(phone),
                        real_name = VALUES(real_name),
                        fuero = VALUES(fuero)
                """, (username, realname, phone, fuero))
        except Exception as e:
            print(f"Error updating user ad data: {e}")
    return redirect(url_for("dashboard.dashboard", manage_users=1))


@bp_dashboard.route("/admin/users/create", methods=["POST"])
@superuser_required
def create_app_user():
    is_edit_mode = request.form.get("is_edit_mode") == "1"
    username = request.form.get("username", "").strip().lower()
    display_name = request.form.get("display_name", "").strip() or username
    password = request.form.get("password", "")
    is_superuser_flag = request.form.get("is_superuser") == "on"
    is_active = request.form.get("is_active") == "on"
    must_change_password = request.form.get("must_change_password") == "on"
    role = request.form.get("role", "tecnico").strip().lower()
    technician_name = request.form.get("technician_name", "").strip()
    phone = request.form.get("phone", "").strip()
    permissions = {
        "dashboard": request.form.get("perm_dashboard") == "on",
        "mobile": request.form.get("perm_mobile") == "on",
        "infrastructure": request.form.get("perm_infrastructure") == "on",
        "reports": request.form.get("perm_reports") == "on",
    }

    from utils.auth import _fetch_auth_user
    existing_user = _fetch_auth_user(username)

    # REGLA 1: No permitir crear un usuario que ya existe si no estamos en modo edición
    if not is_edit_mode and existing_user:
        flash(f"Error: El usuario '{username}' ya existe. Si desea modificarlo, use el botón 'Editar' en la lista.", "error")
        return redirect(url_for("dashboard.dashboard", manage_users=1))
    
    # REGLA 2: Si estamos en modo edición y algunos campos vienen vacíos (como en quickPromote), preservamos los actuales
    if is_edit_mode and existing_user:
        if not display_name or display_name == username:
            display_name = existing_user["display_name"] or display_name
        if not technician_name:
            technician_name = existing_user["technician_name"]
        if not phone:
            phone = existing_user["phone"]

    # REGLA 3: Password obligatoria para nuevos usuarios
    if not is_edit_mode and not password:
        flash("Error: La contraseña es obligatoria para nuevos usuarios.", "error")
        return redirect(url_for("dashboard.dashboard", manage_users=1))

    try:
        upsert_app_user(
            username=username,
            password=password,
            display_name=display_name,
            is_superuser_flag=is_superuser_flag,
            is_active=is_active or is_superuser_flag,
            must_change_password=must_change_password,
            role=role,
            technician_name=technician_name,
            permissions=permissions,
            phone=phone,
        )
        msg = f"Usuario '{username}' actualizado." if is_edit_mode else f"Usuario '{username}' creado correctamente."
        flash(msg, "success")
    except Exception as exc:
        flash(f"Error al procesar usuario: {exc}", "error")

    return redirect(url_for("dashboard.dashboard", manage_users=1))


@bp_dashboard.route("/admin/users/reset_password", methods=["POST"])
@superuser_required
def reset_app_user_password():
    username = request.form.get("username", "").strip().lower()
    new_password = request.form.get("password", "")
    if not username or not new_password:
        flash("Usuario y nueva clave son obligatorios.", "error")
    else:
        try:
            from utils.auth import update_app_user_password
            update_app_user_password(username, new_password)
            flash(f"Clave de '{username}' actualizada correctamente.", "success")
        except Exception as exc:
            flash(f"Error al restablecer clave: {exc}", "error")
    return redirect(url_for("dashboard.dashboard", manage_users=1))


@bp_dashboard.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@superuser_required
def remove_app_user(user_id):
    try:
        delete_app_user(user_id, acting_username=current_username())
        flash("Usuario del sistema eliminado.", "success")
    except Exception as exc:
        flash(f"No se pudo eliminar el usuario: {exc}", "error")
    return redirect(url_for("dashboard.dashboard", manage_users=1))



@bp_dashboard.route("/fueros")
def view_fueros():
    """Vista para consultar usuarios, impresoras y PCs por fuero, y encontrar elementos huérfanos."""
    fuero_param = request.args.get("fuero", "").strip()
    
    with get_db_connection() as conn:
        fueros_rows = conn.execute("SELECT DISTINCT fuero FROM pcs WHERE fuero IS NOT NULL AND fuero != '' AND fuero != 'Desconocido' ORDER BY fuero").fetchall()
        fueros_list = [row['fuero'] for row in fueros_rows]

        # Conteos por fuero físicos (Patrimonio real del sector)
        pc_counts_rows = conn.execute("""
            SELECT fuero, COUNT(*) as cnt
            FROM pcs
            WHERE is_active = 'True'
              AND fuero IS NOT NULL AND fuero != '' AND fuero != 'Desconocido'
              AND UPPER(pc_name) NOT IN ('PC GENERICA','INFRAESTRUCTURA','PC-GENERICA')
            GROUP BY fuero
        """).fetchall()

        # Contar Usuarios por Fuero (AD + Distintos en PCs)
        user_counts_rows = conn.execute("""
            SELECT f.fuero, COUNT(DISTINCT u.username) as cnt
            FROM (SELECT DISTINCT fuero FROM pcs WHERE fuero IS NOT NULL AND fuero != '') f
            JOIN (
                SELECT username, fuero FROM ad_users
                UNION
                SELECT LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) as username, fuero 
                FROM pcs 
                WHERE is_active = 'True' AND last_user IS NOT NULL AND last_user != ''
            ) u ON u.fuero = f.fuero
            GROUP BY f.fuero
        """).fetchall()

        # Contar Impresoras de Red físicas del Fuero
        net_printer_counts = conn.execute("""
            SELECT fuero, COUNT(*) as cnt
            FROM network_printers
            WHERE fuero IS NOT NULL AND fuero != '' AND fuero != 'Desconocido'
            GROUP BY fuero
        """).fetchall()

        # Contar Impresoras Locales físicas del Fuero (Excluyendo las que ya están en el catálogo de Red)
        local_printer_counts = conn.execute("""
            SELECT fuero, COUNT(*) as cnt
            FROM pcs
            WHERE is_active = 'True'
              AND (printer_model IS NOT NULL AND printer_model != '' AND printer_model != 'N/A' AND UPPER(printer_model) NOT LIKE '%%SIN IMPRESORA%%')
              AND (printer_port IS NULL OR printer_port NOT LIKE '\\\\\\\\%%')
              AND fuero IS NOT NULL AND fuero != '' AND fuero != 'Desconocido'
              AND pc_name NOT IN (SELECT pc_name FROM pc_network_printers)
            GROUP BY fuero
        """).fetchall()

        fuero_stats = {}
        for row in pc_counts_rows:
            fuero_stats.setdefault(row['fuero'], {'pcs': 0, 'printers': 0, 'users': 0})['pcs'] = row['cnt']
        for row in user_counts_rows:
            fuero_stats.setdefault(row['fuero'], {'pcs': 0, 'printers': 0, 'users': 0})['users'] = row['cnt']
        for row in net_printer_counts:
            fuero_stats.setdefault(row['fuero'], {'pcs': 0, 'printers': 0, 'users': 0})['printers'] += row['cnt']
        for row in local_printer_counts:
            fuero_stats.setdefault(row['fuero'], {'pcs': 0, 'printers': 0, 'users': 0})['printers'] += row['cnt']

        pcs = []
        users = []
        printers = []

        
        if fuero_param:
            pcs = conn.execute("SELECT pc_name, last_user, ip_address, os_name, printer_model, printer_port FROM pcs WHERE is_active = 'True' AND UPPER(pc_name) NOT IN ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA') AND fuero = %s ORDER BY pc_name", (fuero_param,)).fetchall()
            users = conn.execute("""
                SELECT username, real_name, phone 
                FROM ad_users 
                WHERE fuero = %s 
                UNION
                SELECT DISTINCT 
                    LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) as username, 
                    last_user as real_name, 
                    NULL as phone
                FROM pcs 
                WHERE is_active = 'True' 
                  AND pc_name NOT IN ('PC Generica', 'Infraestructura') 
                  AND fuero = %s 
                  AND last_user IS NOT NULL 
                  AND last_user != '' 
                  AND LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) NOT IN (SELECT username FROM ad_users)
                ORDER BY real_name
            """, (fuero_param, fuero_param)).fetchall()
            printers_raw = conn.execute("""
                SELECT DISTINCT np.id, np.ip_address, np.serial_number, np.brand_model, np.fuero as physical_fuero 
                FROM network_printers np
                LEFT JOIN pc_network_printers pnp ON np.id = pnp.printer_id
                LEFT JOIN pcs p ON pnp.pc_name = p.pc_name
                WHERE np.fuero = %s OR p.fuero = %s 
                ORDER BY np.ip_address
            """, (fuero_param, fuero_param)).fetchall()
        else:
            # Buscar elementos sin fuero (huerfanos)
            pcs = conn.execute("SELECT pc_name, last_user, ip_address, os_name, printer_model, printer_port FROM pcs WHERE is_active = 'True' AND UPPER(pc_name) NOT IN ('PC GENERICA', 'INFRAESTRUCTURA', 'PC-GENERICA') AND (fuero IS NULL OR fuero = '' OR fuero = 'Desconocido') ORDER BY pc_name").fetchall()
            users = conn.execute("""
                SELECT username, real_name, phone 
                FROM ad_users 
                WHERE (fuero IS NULL OR fuero = '' OR fuero = 'Desconocido') 
                UNION
                SELECT DISTINCT 
                    LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) as username, 
                    last_user as real_name, 
                    NULL as phone
                FROM pcs 
                WHERE is_active = 'True' 
                  AND pc_name NOT IN ('PC Generica', 'Infraestructura') 
                  AND (fuero IS NULL OR fuero = '' OR fuero = 'Desconocido') 
                  AND last_user IS NOT NULL 
                  AND last_user != '' 
                  AND LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) NOT IN (SELECT username FROM ad_users)
                ORDER BY real_name
            """).fetchall()
            printers_raw = conn.execute("""
                SELECT DISTINCT np.id, np.ip_address, np.serial_number, np.brand_model, np.fuero as physical_fuero 
                FROM network_printers np
                LEFT JOIN pc_network_printers pnp ON np.id = pnp.printer_id
                LEFT JOIN pcs p ON pnp.pc_name = p.pc_name
                WHERE (np.fuero IS NULL OR np.fuero = '' OR np.fuero = 'Desconocido') 
                   OR (p.fuero IS NULL OR p.fuero = '' OR p.fuero = 'Desconocido')
                ORDER BY np.ip_address
            """).fetchall()

        # Agregar asignaciones (PCs cliente) a cada impresora
        for p_row in printers_raw:
            p_dict = dict(p_row)
            assigned_pcs = conn.execute("""
                SELECT p.pc_name, p.last_user, u.real_name 
                FROM pc_network_printers pnp
                JOIN pcs p ON pnp.pc_name = p.pc_name
                LEFT JOIN ad_users u ON LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = u.username
                WHERE pnp.printer_id = %s
            """, (p_dict['id'],)).fetchall()
            p_dict['assignments'] = [dict(a) for a in assigned_pcs]
            printers.append(p_dict)

    # ── Respuesta JSON (para el modal de topología) ──────────────
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.args.get('json'):
        from flask import jsonify
        return jsonify({
            'fuero_param': fuero_param,
            'users':    [dict(u) for u in users],
            'pcs':      [dict(p) for p in pcs],
            'printers': printers,
        })

    return render_template(
        "fueros.html",
        fueros_list=fueros_list,
        fuero_param=fuero_param,
        fuero_stats=fuero_stats,
        pcs=pcs,
        users=users,
        printers=printers,
        fuero_colors=FUERO_COLORS
    )

