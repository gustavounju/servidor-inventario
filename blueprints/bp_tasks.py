from flask import Blueprint, request, jsonify, redirect, url_for, render_template, send_file
import datetime
from datetime import datetime as dt
from io import BytesIO
from openpyxl import Workbook
import sqlite3

from database.db_core import get_db_connection
from services.ai_assistant import predict_category
from services.reporting import PDFReport, format_datetime_es, format_date_es

bp_tasks = Blueprint('tasks', __name__)

@bp_tasks.route("/pc/migrate_tasks", methods=["POST"])
def migrate_generic_tasks():
    target_pc = request.form.get("target_pc")
    task_id = request.form.get("migration_task_id")
    if not target_pc: return redirect(url_for("dashboard.pc_detail", pc_name="PC Generica"))
    
    with get_db_connection() as conn:
        if task_id:
            conn.execute("UPDATE tasks SET pc_name = ? WHERE id = ? AND pc_name = 'PC Generica'", (target_pc, task_id))
            audit_msg = f"Se importó la tarea #{task_id} de PC Generica"
        else:
            conn.execute("UPDATE tasks SET pc_name = ? WHERE pc_name = 'PC Generica'", (target_pc,))
            audit_msg = "Se importaron TODAS las tareas de PC Generica"
        
        conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (?, ?, ?, ?)", (target_pc, "MIGRACION", "PC Generica", audit_msg))
        conn.commit()
    return redirect(url_for("dashboard.pc_detail", pc_name=target_pc))

@bp_tasks.route("/pc/<pc_name>/tasks", methods=["POST"])
def add_task(pc_name):
    descripcion = request.form.get("descripcion", "").strip()
    solicitante = request.form.get("solicitante", "").strip()
    categoria = request.form.get("categoria", "").strip()
    if not solicitante: solicitante = "No Especificado (Dashboard)"
    if not descripcion: return redirect(url_for("dashboard.pc_detail", pc_name=pc_name))
    if not categoria: categoria = predict_category(descripcion)

    with get_db_connection() as conn:
        conn.execute("INSERT INTO tasks (pc_name, descripcion, solicitante, categoria) VALUES (?, ?, ?, ?)", (pc_name, descripcion, solicitante, categoria))
        conn.commit()
    return redirect(url_for("dashboard.pc_detail", pc_name=pc_name))

@bp_tasks.route("/technicians/add", methods=["POST"])
def add_technician():
    name = request.form.get("name", "").strip()
    if name:
        try:
            with get_db_connection() as conn:
                conn.execute("INSERT INTO technicians (name) VALUES (?)", (name,))
                conn.commit()
        except sqlite3.IntegrityError: pass
    return redirect(url_for("dashboard.dashboard"))

@bp_tasks.route("/technicians/delete/<int:tech_id>", methods=["POST"])
def delete_technician(tech_id):
    with get_db_connection() as conn:
        conn.execute("DELETE FROM technicians WHERE id = ?", (tech_id,))
        conn.commit()
    return redirect(url_for("dashboard.dashboard"))

@bp_tasks.route("/tasks/<int:task_id>/done", methods=["POST"])
def mark_task_done(task_id):
    technician = request.form.get("technician_name", None)
    with get_db_connection() as conn:
        row = conn.execute("SELECT pc_name FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row:
            conn.execute(
                "UPDATE tasks SET estado = 'Hecha', completed_by = ?, completed_at = ? WHERE id = ?",
                (technician, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), task_id)
            )
            conn.commit()
            pc_name = row["pc_name"]
        else: pc_name = ""
    if not pc_name: return redirect(url_for("dashboard.dashboard"))
    return redirect(url_for("dashboard.pc_detail", pc_name=pc_name))

@bp_tasks.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    with get_db_connection() as conn:
        row = conn.execute("SELECT pc_name FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            pc_name = row["pc_name"]
        else: pc_name = ""
    if not pc_name: return redirect(url_for("dashboard.dashboard"))
    return redirect(url_for("dashboard.pc_detail", pc_name=pc_name))

@bp_tasks.route("/create_loose_task", methods=["POST"])
def create_loose_task():
    descripcion = request.form.get("descripcion")
    solicitante = request.form.get("solicitante")
    categoria = request.form.get("categoria")
    technician = request.form.get("technician")
    fuero = request.form.get("fuero")

    if not descripcion or not solicitante: return "Faltan datos", 400
    if not categoria: categoria = predict_category(descripcion)
    
    estado = "Pendiente"
    assigned_to = None
    if technician:
        assigned_to = technician
        estado = "Asignada"

    with get_db_connection() as conn:
        conn.execute(
            """INSERT INTO tasks (descripcion, solicitante, estado, created_at, categoria, assigned_to, fuero, pc_name) VALUES (?, ?, ?, datetime('now', 'localtime'), ?, ?, ?, 'PC Generica')""",
            (descripcion, solicitante, estado, categoria, assigned_to, fuero)
        )
        conn.commit()
    return redirect(url_for("dashboard.dashboard"))

@bp_tasks.route("/tasks/assign", methods=["POST"])
def assign_task():
    task_id = request.form.get("task_id")
    pc_name = request.form.get("pc_name", "").strip()
    if task_id and pc_name:
        with get_db_connection() as conn:
            t = conn.execute("SELECT 1 FROM pcs WHERE pc_name = ?", (pc_name,)).fetchone()
            if t:
                conn.execute("UPDATE tasks SET pc_name = ? WHERE id = ?", (pc_name, task_id))
                conn.commit()
    return redirect(url_for("dashboard.dashboard"))

@bp_tasks.route("/api/audit/<pc_name>/add", methods=["POST"])
def add_manual_audit(pc_name):
    campo = request.form.get("campo", "").strip()
    valor_anterior = request.form.get("valor_anterior", "").strip()
    valor_nuevo = request.form.get("valor_nuevo", "").strip()
    if not campo or not valor_nuevo: return jsonify({"status": "error", "message": "Faltan datos"}), 400
    try:
        with get_db_connection() as conn:
            conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (?, ?, ?, ?)", (pc_name, campo, valor_anterior, valor_nuevo))
            conn.commit()
        return redirect(url_for("dashboard.pc_detail", pc_name=pc_name))
    except Exception as e:
        return f"Error agregando historial manual: {e}", 500

@bp_tasks.route("/report/tasks_completed", methods=["GET", "POST"])
def report_tasks_completed():
    pc_name = request.args.get("pc", "").strip()
    if request.method == "GET": return render_template("report_tasks.html", pc_name=pc_name)

    fecha_filtro = request.form.get("fecha", "").strip() or dt.now().strftime("%Y-%m-%d")
    pc_name = request.form.get("pc_name", "").strip() or pc_name

    with get_db_connection() as conn:
        base_sql = "SELECT pc_name, descripcion, solicitante, created_at, estado, completed_by, completed_at FROM tasks WHERE estado = 'Hecha' AND DATE(completed_at) = ?"
        params = [fecha_filtro]
        if pc_name:
            base_sql += " AND pc_name = ?"
            params.append(pc_name)
        base_sql += " ORDER BY completed_at DESC"
        tareas = conn.execute(base_sql, params).fetchall()

    wb = Workbook()
    ws = wb.active
    ws.title = "Tareas"
    ws.append(["PC", "Descripción", "Solicitante", "Fecha Creación", "Estado", "Realizado Por", "Fecha Cierre"])
    for t in tareas: ws.append([t["pc_name"], t["descripcion"], t["solicitante"] or "", t["created_at"], t["estado"], t["completed_by"] or "", t["completed_at"] or ""])

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    nombre_pc_sufijo = f"_{pc_name}" if pc_name else ""
    return send_file(output, mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", as_attachment=True, download_name=f"Tareas_Completadas{nombre_pc_sufijo}_{fecha_filtro}.xlsx")

@bp_tasks.route("/report/tasks_completed_pdf", methods=["POST"])
def report_tasks_completed_pdf():
    fecha_filtro_str = request.form.get("fecha", "").strip() or dt.now().strftime("%Y-%m-%d")
    pc_name = request.form.get("pc_name", "").strip()
    fecha_dt = datetime.datetime.strptime(fecha_filtro_str, "%Y-%m-%d")
    fecha_display = format_date_es(fecha_dt)

    with get_db_connection() as conn:
        base_sql = "SELECT t.pc_name, t.descripcion, t.solicitante, t.created_at, t.estado, t.completed_by, t.completed_at, p.last_user FROM tasks t LEFT JOIN pcs p ON t.pc_name = p.pc_name WHERE t.estado = 'Hecha' AND DATE(t.completed_at) = ?"
        params = [fecha_filtro_str]
        if pc_name:
            base_sql += " AND t.pc_name = ?"
            params.append(pc_name)
        base_sql += " ORDER BY t.completed_at DESC"
        tareas_hechas = conn.execute(base_sql, params).fetchall()

        sql_pendientes = "SELECT t.pc_name, t.descripcion, t.solicitante, t.created_at, t.estado, t.assigned_to, p.last_user FROM tasks t LEFT JOIN pcs p ON t.pc_name = p.pc_name WHERE t.estado != 'Hecha' AND DATE(t.created_at) = ?"
        params_pend = [fecha_filtro_str]
        if pc_name:
            sql_pendientes += " AND t.pc_name = ?"
            params_pend.append(pc_name)
        sql_pendientes += " ORDER BY t.created_at DESC"
        tareas_pendientes = conn.execute(sql_pendientes, params_pend).fetchall()

    pdf = PDFReport(title="Reporte de Tareas - Inventario GOLD")
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Reporte del día: {fecha_display}", 0, 1)
    pdf.ln(2)

    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(25, 135, 84)
    pdf.cell(0, 8, f"Tareas Realizadas ({len(tareas_hechas)})", 0, 1)
    pdf.ln(2)

    headers = ["PC", "Usuario", "Descripción", "Solic.", "Técnico", "Fecha Creada"]
    w = [28, 22, 45, 18, 18, 34]
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(25, 135, 84)
    pdf.set_text_color(255)
    for i, h in enumerate(headers): pdf.cell(w[i], 8, h, 1, 0, 'C', fill=True)
    pdf.ln()

    if not tareas_hechas:
        pdf.set_font("Arial", "I", 9)
        pdf.set_text_color(0)
        pdf.cell(0, 8, "No hay tareas realizadas registradas para hoy.", 1, 1, 'C')
    else:
        pdf.set_font("Arial", "", 8)
        pdf.set_text_color(0)
        for t in tareas_hechas:
            raw_user = t["last_user"] or "N/A"
            user_display = raw_user.split("\\")[-1] if "\\" in raw_user else raw_user
            desc, solicitante, tecnico, created_at, pc_name_dis = t["descripcion"] or "", t["solicitante"] or "", t["completed_by"] or "", t["created_at"] or "", str(t["pc_name"])
            fecha_hora = format_datetime_es(created_at)

            lines_desc = max(1, (len(desc) // 25) + 1)
            lines_solic = max(1, (len(solicitante) // 9) + 1)
            h_row = max(lines_desc, lines_solic) * 5
            
            x_start, y_start = pdf.get_x(), pdf.get_y()
            if (y_start + h_row) > 275:
                pdf.add_page()
                y_start = pdf.get_y()
            
            pdf.set_xy(x_start, y_start)
            pdf.cell(w[0], h_row, pc_name_dis[:16], 1)
            pdf.cell(w[1], h_row, str(user_display)[:13], 1)
            
            x_desc = x_start + w[0] + w[1]
            pdf.set_xy(x_desc, y_start)
            pdf.multi_cell(w[2], 5, desc, 0, 'L')
            
            x_solic = x_desc + w[2]
            pdf.set_xy(x_solic, y_start)
            pdf.multi_cell(w[3], 5, solicitante, 0, 'L')
            
            x_tech = x_solic + w[3]
            pdf.set_xy(x_tech, y_start)
            pdf.cell(w[4], h_row, tecnico[:11], 1)
            
            x_date = x_tech + w[4]
            pdf.set_xy(x_date, y_start)
            pdf.cell(w[5], h_row, fecha_hora, 1, 1, 'C')
            
            pdf.rect(x_desc, y_start, w[2], h_row)
            pdf.rect(x_solic, y_start, w[3], h_row)
            pdf.set_xy(x_start, y_start + h_row)

    pdf.ln(2)

    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(220, 53, 69)
    pdf.cell(0, 8, f"Tareas Pendientes / Generadas Hoy ({len(tareas_pendientes)})", 0, 1)
    pdf.ln(2)

    headers_pend = ["Descripción", "Solic.", "Asignado a", "Fecha Creada"]
    w_pend = [70, 30, 30, 35]
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(220, 53, 69)
    pdf.set_text_color(255)
    for i, h in enumerate(headers_pend): pdf.cell(w_pend[i], 8, h, 1, 0, 'C', fill=True)
    pdf.ln()

    if not tareas_pendientes:
        pdf.set_font("Arial", "I", 9)
        pdf.set_text_color(0)
        pdf.cell(0, 8, "No hay tareas pendientes generadas hoy.", 1, 1, 'C')
    else:
        pdf.set_font("Arial", "", 8)
        pdf.set_text_color(0)
        for t in tareas_pendientes:
            desc, solicitante, assigned, created_at = t["descripcion"] or "", str(t["solicitante"] or ""), str(t["assigned_to"] or "Sin Asignar"), t["created_at"] or ""
            fecha_hora = format_datetime_es(created_at)
            
            lines_desc = max(1, (len(desc) // 35) + 1)
            lines_solic = max(1, (len(solicitante) // 15) + 1)
            h_row = max(lines_desc, lines_solic) * 5
            
            x_start, y_start = pdf.get_x(), pdf.get_y()
            if (y_start + h_row) > 275:
                pdf.add_page()
                y_start = pdf.get_y()
            
            pdf.set_xy(x_start, y_start)
            pdf.multi_cell(w_pend[0], 5, desc, 0, 'L')
            
            x_solic = x_start + w_pend[0]
            pdf.set_xy(x_solic, y_start)
            pdf.multi_cell(w_pend[1], 5, solicitante, 0, 'L')
            
            x_assign = x_solic + w_pend[1]
            pdf.set_xy(x_assign, y_start)
            pdf.cell(w_pend[2], h_row, assigned[:18], 1)
            
            x_date = x_assign + w_pend[2]
            pdf.set_xy(x_date, y_start)
            pdf.cell(w_pend[3], h_row, fecha_hora, 1, 1, 'C')
            
            pdf.rect(x_start, y_start, w_pend[0], h_row)
            pdf.rect(x_solic, y_start, w_pend[1], h_row)
            pdf.set_xy(x_start, y_start + h_row)

    output = BytesIO()
    pdf_bytes = pdf.output()
    output.write(pdf_bytes)
    output.seek(0)
    
    nombre_pc_sufijo = f"_{pc_name}" if pc_name else ""
    return send_file(output, mimetype="application/pdf", as_attachment=True, download_name=f"Reporte_Tareas{nombre_pc_sufijo}_{fecha_filtro_str}.pdf")
