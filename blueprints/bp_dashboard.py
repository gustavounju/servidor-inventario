from flask import Blueprint, render_template, request, redirect, url_for, abort, send_file
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

bp_dashboard = Blueprint('dashboard', __name__)

@bp_dashboard.route("/cementerio")
def view_cementerio():
    return redirect(url_for("dashboard.dashboard", estado="False"))

@bp_dashboard.route("/graficos")
def view_graphics():
    """Nueva página dedicada a KPIs y Gráficos."""
    try:
        with get_db_connection() as conn:
            kpi_total_activas = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND pc_name NOT IN ('PC Generica', 'Infraestructura')").fetchone()["c"]
            kpi_total_graveyard = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'False'").fetchone()["c"]
            kpi_alerta_ram = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND alerta_ram_baja = 1 AND pc_name != 'PC Generica'").fetchone()["c"]
            kpi_sin_impresora = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND alerta_sin_impresora = 1 AND pc_name != 'PC Generica'").fetchone()["c"]
            kpi_impresora_red = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND alerta_impresora_red = 1 AND pc_name != 'PC Generica'").fetchone()["c"]
            kpi_win7 = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND os_name LIKE %s", ("%Windows 7%",)).fetchone()["c"]
            kpi_win10 = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND (os_name LIKE %s OR os_name LIKE %s)", ("%Windows 10%", "%Windows 11%")).fetchone()["c"]
            kpi_tareas_hoy = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado = 'Hecha' AND DATE(completed_at) = CURDATE()").fetchone()["c"]
            kpi_tareas_pendientes_count = conn.execute("SELECT COUNT(DISTINCT pc_name) as c FROM tasks WHERE estado != 'Hecha' AND pc_name IS NOT NULL AND pc_name != ''").fetchone()["c"]
            kpi_tareas_pendientes_total = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado != 'Hecha'").fetchone()["c"]

            rows_cats = conn.execute("SELECT categoria, COUNT(*) as c FROM tasks GROUP BY categoria").fetchall()
            cat_labels = []
            cat_values = []
            for r in rows_cats:
                cat_name = r["categoria"] if r["categoria"] else "Sin Categoría"
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
        kpi_tareas_hoy=kpi_tareas_hoy,
        kpi_tareas_pendientes_count=kpi_tareas_pendientes_count,
        kpi_tareas_pendientes_total=kpi_tareas_pendientes_total,
        cat_labels=cat_labels,
        cat_values=cat_values,
        hostname=socket.gethostname(),
        fueros=FUERO_MAPPING
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
                filter_sql += " AND p.pc_name LIKE %s"
                filter_params.append(f"%{q}%")
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
                filter_sql += " AND (p.os_name LIKE %s OR p.os_name LIKE %s)"
                filter_params.extend(["%Windows 10%", "%Windows 11%"])
            
            if filter_tasks == "true":
                filter_sql += " AND (SELECT COUNT(*) FROM tasks t WHERE t.pc_name = p.pc_name AND t.estado != 'Hecha') > 0"

            # Ejecutar conteo
            count_sql = "SELECT COUNT(*) as c FROM pcs p WHERE 1=1" + filter_sql
            total_rows = conn.execute(count_sql, filter_params).fetchone()["c"]

            unassigned_tasks = conn.execute("SELECT * FROM tasks WHERE (pc_name IS NULL OR pc_name = '') AND estado != 'Hecha' ORDER BY created_at DESC").fetchall()
            unassigned_count = len(unassigned_tasks)
            technicians_list = [dict(r) for r in conn.execute("SELECT * FROM technicians ORDER BY name").fetchall()]

            base_sql = """
                SELECT p.*, u.real_name as ad_real_name,
                    (SELECT COUNT(*) FROM tasks t WHERE t.pc_name = p.pc_name AND t.estado != 'Hecha') AS tareas_pendientes
                FROM pcs p
                LEFT JOIN ad_users u ON LOWER(SUBSTRING_INDEX(p.last_user, '\\\\', -1)) = u.username
                WHERE 1=1
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
                    WHEN p.pc_name = 'PC Generica' THEN 0 
                    WHEN p.pc_name = 'Infraestructura' THEN 1 
                    ELSE 2 
                END, {sort_col_sql} {sort_dir_sql} LIMIT %s OFFSET %s
            """
            params_base = filter_params + [per_page, offset]
            pcs_data = [dict(row) for row in conn.execute(base_sql, params_base).fetchall()]

            kpi_total_activas = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND pc_name NOT IN ('PC Generica', 'Infraestructura')").fetchone()["c"]
            kpi_total_graveyard = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'False'").fetchone()["c"]
            kpi_alerta_ram = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND alerta_ram_baja = 1 AND pc_name != 'PC Generica'").fetchone()["c"]
            kpi_sin_impresora = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND alerta_sin_impresora = 1 AND pc_name != 'PC Generica'").fetchone()["c"]
            kpi_impresora_red = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND alerta_impresora_red = 1 AND pc_name != 'PC Generica'").fetchone()["c"]
            kpi_win7 = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND os_name LIKE %s", ("%Windows 7%",)).fetchone()["c"]
            kpi_win10 = conn.execute("SELECT COUNT(*) as c FROM pcs WHERE is_active = 'True' AND (os_name LIKE %s OR os_name LIKE %s)", ("%Windows 10%", "%Windows 11%")).fetchone()["c"]
            kpi_tareas_hoy = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado = 'Hecha' AND DATE(completed_at) = CURDATE()").fetchone()["c"]
            kpi_tareas_pendientes_total = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado != 'Hecha'").fetchone()["c"]

            all_pcs_dropdown = [dict(row) for row in conn.execute(
                """SELECT pc_name, fuero, last_user FROM pcs WHERE is_active = 'True' 
                ORDER BY CASE WHEN pc_name = 'PC Generica' THEN 0 WHEN pc_name = 'Infraestructura' THEN 1 ELSE 2 END, pc_name ASC"""
            ).fetchall()]
            
    except Exception as exc:
        print(f"Error cargando dashboard: {exc}")
        pcs_data = technicians_list = unassigned_tasks = all_pcs_dropdown = []
        total_rows = kpi_total_activas = kpi_total_graveyard = kpi_alerta_ram = kpi_sin_impresora = 0
        kpi_impresora_red = kpi_win7 = kpi_win10 = kpi_tareas_hoy = kpi_tareas_pendientes_total = unassigned_count = 0

    total_pages = (total_rows + per_page - 1) // per_page if per_page > 0 else 1

    return render_template(
        "index.html",
        pcs=pcs_data,
        server_url=request.host_url,
        unassigned_tasks=unassigned_tasks,
        unassigned_count=unassigned_count,
        technicians=technicians_list,
        kpi_tareas_hoy=kpi_tareas_hoy,
        kpi_tareas_pendientes_total=kpi_tareas_pendientes_total,
        all_pcs=all_pcs_dropdown,
        fueros=FUERO_MAPPING,
        kpi_total_activas=kpi_total_activas,
        kpi_total_graveyard=kpi_total_graveyard,
        kpi_alerta_ram=kpi_alerta_ram,
        kpi_sin_impresora=kpi_sin_impresora,
        kpi_impresora_red=kpi_impresora_red,
        kpi_win7=kpi_win7,
        kpi_win10=kpi_win10,
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
        filter_tasks=filter_tasks
    )

@bp_dashboard.route("/export", methods=["GET", "POST"])
def export_inventory():
    """GET: muestra formulario. POST: genera Excel con campos seleccionados."""
    if request.method == "GET":
        return render_template("export_inventory.html")
    
    campos_seleccionados = request.form.getlist("campos")
    if not campos_seleccionados:
        campos_seleccionados = ["pc_name", "os_name", "processor", "ram_gb", "ip_address"]
    
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM pcs ORDER BY last_report DESC").fetchall()
    if not rows: return "Sin datos", 404
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Inventario"
    ws.append(campos_seleccionados)
    
    for row in rows:
        fila = [row[campo] for campo in campos_seleccionados]
        ws.append(fila)
    
    output = BytesIO()
    wb.save(output)
    
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"Inventario_{dt.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
    )

@bp_dashboard.route("/export_inventory_pdf", methods=["POST"])
def export_inventory_pdf():
    # Ignoramos selección dinámica para PDF, usamos columnas fijas "Pro"
    # Columnas: PC Name, Last User, OS Name, Processor, RAM, IP
    from services.reporting import PDFReport, format_date_es
    with get_db_connection() as conn:
        rows = conn.execute("SELECT pc_name, last_user, os_name, processor, ram_gb, ip_address FROM pcs WHERE pc_name != 'PC Generica' ORDER BY last_report DESC").fetchall()
    
    pdf = PDFReport(title="Inventario General - Inventario GOLD", orientation='L')
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # Fecha de reporte
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, f"Fecha de emisión: {format_date_es(datetime.datetime.now())}", 0, 1, 'C')
    pdf.ln(5)
    
    # Titulo (Conteo)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, f"Total Equipos Inventariados: {len(rows)}", 0, 1, 'C')
    pdf.ln(5)
    
    # Headers
    # Landscape A4 ~ 297mm ancho. Margen 10+10=20. Util: 277.
    # PC(40), User(40), OS(50), CPU(70), RAM(20), IP(35) -> Total 255
    headers = ["Nombre PC", "Usuario", "Sistema Operativo", "Procesador", "RAM", "IP Address"]
    w = [40, 40, 50, 70, 20, 35]
    
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(13, 110, 253)
    pdf.set_text_color(255)
    
    for i, h in enumerate(headers):
        pdf.cell(w[i], 8, h, 1, 0, 'C', fill=True)
    pdf.ln()
    
    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(0)
    
    for row in rows:
        # User clean
        raw_user = row["last_user"] or "N/A"
        if "\\" in raw_user: user = raw_user.split("\\")[-1]
        else: user = raw_user
        
        # CPU truncate
        cpu = row["processor"] or "N/A"
        if len(cpu) > 40: cpu = cpu[:37] + "..."
        
        pdf.cell(w[0], 7, str(row["pc_name"]), 1)
        pdf.cell(w[1], 7, str(user)[:20], 1)
        pdf.cell(w[2], 7, str(row["os_name"]), 1)
        pdf.cell(w[3], 7, cpu, 1)
        pdf.cell(w[4], 7, f'{row["ram_gb"]} GB', 1, 0, 'C')
        pdf.cell(w[5], 7, str(row["ip_address"]), 1, 1, 'C')

    output = BytesIO()
    pdf_bytes = pdf.output()
    output.write(pdf_bytes)
    output.seek(0)
    
    return send_file(
        output,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"Inventario_Reporte_{dt.now().strftime('%Y%m%d')}.pdf",
    )

@bp_dashboard.route("/download_db")
def download_db():
    return "Backup de BD no disponible en modo MySQL. Use mysqldump desde el servidor.", 503

@bp_dashboard.route("/decommission/<string:pc_name>", methods=["GET"])
def decommission_pc(pc_name):
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE pcs SET is_active = 'False' WHERE pc_name = %s", (pc_name,)
        )
        conn.commit()
    return redirect(url_for("dashboard.dashboard"))

@bp_dashboard.route("/reactivate/<pc_name>")
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

@bp_dashboard.route("/refresh_fueros")
def refresh_fueros():
    """Recalcula el fuero para todas las PCs basándose en el nombre."""
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

@bp_dashboard.route("/delete_permanent/<string:pc_name>")
def delete_permanent_pc(pc_name):
    """Borrado definitivo de una PC y sus tareas asociadas."""
    try:
        with get_db_connection() as conn:
            conn.execute("DELETE FROM tasks WHERE pc_name = %s", (pc_name,))
            conn.execute("DELETE FROM pcs WHERE pc_name = %s", (pc_name,))
            conn.execute(
                "INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, 'PERMANENT_DELETE', 'Active/Inactive', 'DELETED')",
                (pc_name,)
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
        technicians = [dict(row) for row in conn.execute("SELECT * FROM technicians ORDER BY name").fetchall()]
        audit_logs = conn.execute("SELECT * FROM audit_logs WHERE pc_name = %s ORDER BY changed_at DESC", (pc_name,)).fetchall()
        all_pcs = conn.execute("SELECT pc_name, fuero, last_user FROM pcs WHERE is_active='True' ORDER BY pc_name").fetchall()
        
        # Buscar Data de la UPS asignada
        pc_ups = conn.execute('''
            SELECT u.*, b.serial_number as battery_code 
            FROM ups_inventory u
            LEFT JOIN components b ON u.assigned_battery_id = b.id
            WHERE u.assigned_pc = %s
        ''', (pc_name,)).fetchone()
        
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

    if pc is None: abort(404)
    return render_template("pc_detail.html", pc=pc, tareas=tareas, technicians=technicians, audit_logs=audit_logs, all_pcs=all_pcs, fuero_colors=FUERO_COLORS, pc_ups=pc_ups, available_ups=available_ups, pc_components=pc_components, available_components=available_components, baterias_disponibles=baterias_disponibles)

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
                        conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, %s, %s, %s)", (pc_name, field, old_str, new_str))
            conn.commit()
        return redirect(url_for("dashboard.pc_detail", pc_name=pc_name))
    except Exception as e:
        return f"Error actualizando infraestructura: {e}", 500
