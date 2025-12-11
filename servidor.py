from flask import Flask, request, jsonify, render_template, redirect, url_for, Response, send_file
import json
import os
import sqlite3
import datetime
import csv
import io
from openpyxl import Workbook
from datetime import datetime as dt
from io import BytesIO
import socket

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

DB_FILE = "inventario.db"
LOG_FOLDER = "logs"

# ----------------- Utilidades DB -----------------

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crea tabla pcs y tabla tasks con todas las columnas necesarias."""
    print(f"Inicializando base de datos en '{DB_FILE}'...")
    with get_db_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS pcs (
                pc_name TEXT PRIMARY KEY,
                os_name TEXT,
                processor TEXT,
                ram_gb REAL,
                ip_address TEXT,
                last_user TEXT,
                last_report TEXT,
                ram_detalles TEXT,
                disk_models TEXT,
                disk_speeds_rpm TEXT,
                motherboard_model TEXT,
                monitors TEXT,
                printer_model TEXT,
                printer_port TEXT,
                ping_ms TEXT,
                ping_loss_pct TEXT,
                alerta_ram_baja INTEGER DEFAULT 0,
                alerta_sin_impresora INTEGER DEFAULT 0,
                alerta_impresora_red INTEGER DEFAULT 0,
                is_active TEXT DEFAULT 'True',
                full_json_data TEXT
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pc_name TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now', '-3 hours')),
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'Pendiente',
                FOREIGN KEY (pc_name) REFERENCES pcs(pc_name)
            )
            """
        )

        conn.commit()
    print("Base de datos lista y estructura verificada.")



# ----------------- Healthcheck -----------------

@app.route("/health", methods=["GET"])
def health():
    try:
        conn = sqlite3.connect(DB_FILE)
        conn.execute("SELECT 1")
        conn.close()
        return {"status": "ok", "db_ok": True}, 200
    except Exception:
        return {"status": "error", "db_ok": False}, 500


# Crear carpeta de logs
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)


# ----------------- Rutas Web -----------------
@app.route("/", methods=["GET"])
def dashboard():
    """Lista todas las PCs (activas y en cementerio) + KPIs + filtros + paginado."""
    pcs_data = []
    kpi_total_activas = 0
    kpi_total_graveyard = 0
    kpi_alerta_ram = 0
    kpi_sin_impresora = 0
    kpi_impresora_red = 0
    kpi_win7 = 0
    kpi_win10 = 0

    # Filtros
    q = request.args.get("q", "").strip()
    estado = request.args.get("estado", "").strip()
    alerta = request.args.get("alerta", "").strip()

    # Paginación
    try:
        page = int(request.args.get("page", 1))
    except ValueError:
        page = 1
    per_page = 25
    offset = (page - 1) * per_page

    total_rows = 0

    try:
        with get_db_connection() as conn:
            # Primero contamos cuántas filas habría con los filtros
            count_sql = "SELECT COUNT(*) as c FROM pcs p WHERE 1=1"
            params = []

            if q:
                count_sql += " AND p.pc_name LIKE ?"
                params.append(f"%{q}%")

            if estado in ("True", "False"):
                count_sql += " AND p.is_active = ?"
                params.append(estado)

            if alerta == "ram":
                count_sql += " AND p.alerta_ram_baja = 1"
            elif alerta == "sinimp":
                count_sql += " AND p.alerta_sin_impresora = 1"
            elif alerta == "red":
                count_sql += " AND p.alerta_impresora_red = 1"

            total_rows = conn.execute(count_sql, params).fetchone()["c"]

            # Ahora traemos solo la página actual
            base_sql = """
                SELECT
                    p.*,
                    (
                        SELECT COUNT(*)
                        FROM tasks t
                        WHERE t.pc_name = p.pc_name
                          AND t.estado != 'Hecha'
                    ) AS tareas_pendientes
                FROM pcs p
                WHERE 1=1
            """

            if q:
                base_sql += " AND p.pc_name LIKE ?"
            if estado in ("True", "False"):
                base_sql += " AND p.is_active = ?"
            if alerta == "ram":
                base_sql += " AND p.alerta_ram_baja = 1"
            elif alerta == "sinimp":
                base_sql += " AND p.alerta_sin_impresora = 1"
            elif alerta == "red":
                base_sql += " AND p.alerta_impresora_red = 1"

            base_sql += " ORDER BY p.last_report DESC LIMIT ? OFFSET ?"
            params_with_limit = params + [per_page, offset]

            rows = conn.execute(base_sql, params_with_limit).fetchall()

            for row in rows:
                pc = dict(row)

                # KPIs sobre el conjunto filtrado de la página (si quieres sobre todo, habría que usar otra consulta)
                if pc.get("is_active") == "True":
                    kpi_total_activas += 1
                else:
                    kpi_total_graveyard += 1

                if pc.get("alerta_ram_baja"):
                    kpi_alerta_ram += 1
                if pc.get("alerta_sin_impresora"):
                    kpi_sin_impresora += 1
                if pc.get("alerta_impresora_red"):
                    kpi_impresora_red += 1

                os_name = pc.get("os_name") or ""
                if "Windows 7" in os_name:
                    kpi_win7 += 1
                elif "Windows 10" in os_name or "Windows 11" in os_name:
                    kpi_win10 += 1

                pcs_data.append(pc)

    except Exception as exc:
        print(f"Error cargando dashboard: {exc}")

    # Calcular total de páginas
    total_pages = (total_rows // per_page) + (1 if total_rows % per_page else 0)

    server_url = request.url_root.strip("/")  # ej: "http://192.168.1.8:5000"

    return render_template(
        "index.html",
        pcs=pcs_data,
        kpi_total_activas=kpi_total_activas,
        kpi_total_graveyard=kpi_total_graveyard,
        kpi_alerta_ping=0,
        kpi_alerta_ram=kpi_alerta_ram,
        kpi_sin_impresora=kpi_sin_impresora,
        kpi_impresora_red=kpi_impresora_red,
        kpi_win7=kpi_win7,
        kpi_win10=kpi_win10,
        page=page,
        total_pages=total_pages,
        total_rows=total_rows,
        per_page=per_page,
        server_url=server_url,      # <- agregar esta línea
        hostname=socket.gethostname(),
    )




# --------- Exportar a CSV ---------

@app.route("/export", methods=["GET", "POST"])
def export_inventory():
    """GET: muestra formulario. POST: genera Excel con campos seleccionados."""
    
    if request.method == "GET":
        # Mostrar formulario para elegir campos
        return render_template("export_inventory.html")
    
    # POST: generar Excel
    campos_seleccionados = request.form.getlist("campos")
    
    if not campos_seleccionados:
        # Si no eligió nada, incluir los básicos
        campos_seleccionados = ["pc_name", "os_name", "processor", "ram_gb", "ip_address"]
    
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM pcs ORDER BY last_report DESC").fetchall()
    
    if not rows:
        return "Sin datos", 404
    
    # Crear workbook
    wb = Workbook()
    ws = wb.active
    ws.title = "Inventario"
    
    # Encabezados (solo los campos seleccionados)
    ws.append(campos_seleccionados)
    
    # Filas (solo los campos seleccionados)
    for row in rows:
        fila = [row[campo] for campo in campos_seleccionados]
        ws.append(fila)
    
    # Generar archivo en memoria
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"Inventario_{dt.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
    )



# --------- Detalle + Tareas ---------

@app.route("/pc/<pc_name>")
def pc_detail(pc_name):
    with get_db_connection() as conn:
        pc = conn.execute(
            "SELECT * FROM pcs WHERE pc_name = ?",
            (pc_name,),
        ).fetchone()

        tareas = conn.execute(
            """
            SELECT id, pc_name, created_at, descripcion, estado
            FROM tasks
            WHERE pc_name = ?
            ORDER BY created_at DESC
            """,
            (pc_name,),
        ).fetchall()

    if pc is None:
        abort(404)

    return render_template("pc_detail.html", pc=pc, tareas=tareas)


@app.route("/pc/<pc_name>/tasks", methods=["POST"])
def add_task(pc_name):
    descripcion = request.form.get("descripcion", "").strip()
    if not descripcion:
        return redirect(url_for("pc_detail", pc_name=pc_name))

    with get_db_connection() as conn:
        conn.execute(
            "INSERT INTO tasks (pc_name, descripcion) VALUES (?, ?)",
            (pc_name, descripcion),
        )
        conn.commit()

    return redirect(url_for("pc_detail", pc_name=pc_name))


@app.route("/tasks/<int:task_id>/done", methods=["POST"])
def mark_task_done(task_id):
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT pc_name FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

        if row:
            conn.execute(
                "UPDATE tasks SET estado = 'Hecha' WHERE id = ?",
                (task_id,),
            )
            conn.commit()
            pc_name = row["pc_name"]
        else:
            pc_name = ""

    if not pc_name:
        return redirect(url_for("dashboard"))

    return redirect(url_for("pc_detail", pc_name=pc_name))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT pc_name FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()

        if row:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            conn.commit()
            pc_name = row["pc_name"]
        else:
            pc_name = ""

    if not pc_name:
        return redirect(url_for("dashboard"))

    return redirect(url_for("pc_detail", pc_name=pc_name))


# --------- Reporte tareas a Excel ---------

@app.route("/report/tasks_completed", methods=["GET", "POST"])
def report_tasks_completed():
    # Si viene ?pc=... en la URL, lo usamos como filtro opcional
    pc_name = request.args.get("pc", "").strip()

    if request.method == "GET":
        # Mostrar formulario para elegir fecha (y mostrar si hay filtro de PC)
        return render_template("report_tasks.html", pc_name=pc_name)

    # POST: generar y descargar el Excel
    fecha_filtro = None
    fecha_str = request.form.get("fecha", "").strip()
    if fecha_str:
        fecha_filtro = fecha_str  # formato YYYY-MM-DD

    if not fecha_filtro:
        fecha_filtro = dt.now().strftime("%Y-%m-%d")

    # También permitimos que el formulario mande pc_name oculto
    pc_name_form = request.form.get("pc_name", "").strip()
    if pc_name_form:
        pc_name = pc_name_form

    with get_db_connection() as conn:
        base_sql = """
            SELECT pc_name, descripcion, created_at, estado
            FROM tasks
            WHERE estado = 'Hecha'
              AND DATE(created_at) = ?
        """
        params = [fecha_filtro]

        if pc_name:
            base_sql += " AND pc_name = ?"
            params.append(pc_name)

        base_sql += " ORDER BY created_at DESC"

        tareas = conn.execute(base_sql, params).fetchall()

    wb = Workbook()
    ws = wb.active
    ws.title = "Tareas"

    ws.append(["PC", "Descripción", "Fecha/Hora", "Estado"])

    for t in tareas:
        ws.append([
            t["pc_name"],
            t["descripcion"],
            t["created_at"],
            t["estado"],
        ])

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    nombre_pc_sufijo = f"_{pc_name}" if pc_name else ""
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=f"Tareas_Completadas{nombre_pc_sufijo}_{fecha_filtro}.xlsx",
    )



# --------- Acciones de estado ---------

@app.route("/decommission/<string:pc_name>", methods=["GET"])
def decommission_pc(pc_name):
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE pcs SET is_active = 'False' WHERE pc_name = ?", (pc_name,)
        )
        conn.commit()
    return redirect(url_for("dashboard"))


@app.route("/reactivate/<pc_name>")
def reactivate_pc(pc_name):
    """Reactivar una PC (sacarla del cementerio)."""
    try:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE pcs SET is_active = 'True' WHERE pc_name = ?",
                (pc_name,),
            )
            conn.commit()
    except Exception as exc:
        print(f"Error reactivating PC {pc_name}: {exc}")

    return redirect(url_for("dashboard"))


# ----------------- API: inventario -----------------

@app.route("/submit_inventory", methods=["POST"])
def receive_inventory():
    """Recibe JSON de inventario y hace upsert en pcs."""
    try:
        raw_data = request.get_data()
        try:
            data = json.loads(raw_data.decode("utf-8"))
        except Exception:
            data = json.loads(raw_data.decode("utf-16"))

        pc_name = data.get("PC_Nombre")
        if not pc_name:
            return jsonify({"status": "error", "message": "Falta PC_Nombre"}), 400

        last_user = data.get("Usuario_Actual", "N/A")
        fecha_raw = data.get("Fecha_Reporte", str(datetime.datetime.now()))
        last_report = fecha_raw["value"] if isinstance(fecha_raw, dict) else str(fecha_raw)

        sistema = data.get("Sistema", {})
        os_name = sistema.get("OsName", "N/A")
        processor = sistema.get("Procesador", "N/A")
        ram_gb = sistema.get("RAM (GB)", 0)

        # Red
        red = data.get("Red", [])
        ip_address = red[0].get("IPAddress") if red else "N/A"

        # Otros detalles
        ram_detalles = data.get("RAM_Detalles", "N/A")
        disk_models = data.get("Disk_Models", "N/A")
        disk_speeds_rpm = data.get("Disk_Speeds_RPM", "N/A")
        motherboard_model = data.get("Motherboard_Model", "N/A")
        printer_model = data.get("Printer_Model", "N/A")
        printer_port = data.get("Printer_Port", "N/A")
        monitors = data.get("Monitors", "N/A")

        # Calidad de conexión (desactivada, dejamos N/A)
        ping_ms = "N/A"
        ping_loss_pct = "N/A"

        # ------------ ALERTAS ------------

        # RAM baja
        try:
            ram_val = float(ram_gb)
        except Exception:
            ram_val = 0.0
        alerta_ram_baja = 1 if ram_val < 8 else 0

        # Impresoras
        pm = (printer_model or "").upper()
        pp = (printer_port or "").upper()

        sin_modelo = pm in ("", "N/A", "NINGUNA")

        # Impresoras virtuales típicas
        es_virtual = ("PDF" in pm) or ("XPS" in pm) or ("ONENOTE" in pm)

        es_red = ("IP_" in pp) or ("WSD" in pp) or ("\\" in pp)
        es_local = pp.startswith("USB") or pp.startswith("LPT")

        # Sin impresora física propia:
        # - sin modelo
        # - o solo impresora virtual (PDF/XPS/etc.)
        if sin_modelo or es_virtual:
            alerta_sin_impresora = 1
        else:
            alerta_sin_impresora = 0

        # Solo impresora en red (física)
        alerta_impresora_red = 1 if (not sin_modelo and not es_virtual and es_red and not es_local) else 0

        # JSON completo
        full_json = json.dumps(data, ensure_ascii=False)

        sql = """
        INSERT INTO pcs (
            pc_name,
            os_name,
            processor,
            ram_gb,
            ip_address,
            last_user,
            last_report,
            ram_detalles,
            disk_models,
            disk_speeds_rpm,
            motherboard_model,
            monitors,
            printer_model,
            printer_port,
            ping_ms,
            ping_loss_pct,
            alerta_ram_baja,
            alerta_sin_impresora,
            alerta_impresora_red,
            is_active,
            full_json_data
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'True', ?)
        ON CONFLICT(pc_name) DO UPDATE SET
            os_name = excluded.os_name,
            processor = excluded.processor,
            ram_gb = excluded.ram_gb,
            ip_address = excluded.ip_address,
            last_user = excluded.last_user,
            last_report = excluded.last_report,
            ram_detalles = excluded.ram_detalles,
            disk_models = excluded.disk_models,
            disk_speeds_rpm = excluded.disk_speeds_rpm,
            motherboard_model = excluded.motherboard_model,
            monitors = excluded.monitors,
            printer_model = excluded.printer_model,
            printer_port = excluded.printer_port,
            ping_ms = excluded.ping_ms,
            ping_loss_pct = excluded.ping_loss_pct,
            alerta_ram_baja = excluded.alerta_ram_baja,
            alerta_sin_impresora = excluded.alerta_sin_impresora,
            alerta_impresora_red = excluded.alerta_impresora_red,
            full_json_data = excluded.full_json_data
        """

        with get_db_connection() as conn:
            conn.execute(
                sql,
                (
                    pc_name,
                    os_name,
                    processor,
                    ram_gb,
                    ip_address,
                    last_user,
                    last_report,
                    ram_detalles,
                    disk_models,
                    disk_speeds_rpm,
                    motherboard_model,
                    monitors,
                    printer_model,
                    printer_port,
                    ping_ms,
                    ping_loss_pct,
                    alerta_ram_baja,
                    alerta_sin_impresora,
                    alerta_impresora_red,
                    full_json,
                ),
            )
            conn.commit()

        print(f"Inventario guardado / actualizado: {pc_name}")
        return jsonify({"status": "success"}), 200

    except Exception as exc:
        print(f"ERROR CRÍTICO EN SERVER: {exc}")
        return jsonify({"status": "error", "message": str(exc)}), 500


# ----------------- API: logs -----------------

@app.route("/submit_log", methods=["POST"])
def receive_log():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"status": "error", "message": "No JSON"}), 400

        pc_name = data.get("PC_Nombre", "Unknown")
        log_content_raw = data.get("Log_Content", "No Content")

        if isinstance(log_content_raw, (dict, list)):
            log_content = json.dumps(log_content_raw, indent=4, ensure_ascii=False)
        else:
            log_content = str(log_content_raw)

        filename = f"LOG_{pc_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filepath = os.path.join(LOG_FOLDER, filename)

        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(log_content)

        print(f"Log de error guardado: {filename}")
        return jsonify({"status": "success"}), 200

    except Exception as exc:
        print(f"Error guardando log: {exc}")
        return jsonify({"status": "error", "details": str(exc)}), 200


# ----------------- Arranque -----------------

if __name__ == "__main__":
    init_db()
    print("Servidor Inventario GOLD iniciado en http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=True)
