import sys

filepath = 'blueprints/bp_tasks.py'
with open(filepath, 'rb') as f:
    content = f.read()

# Try to decode with various encodings
for enc in ['utf-8', 'latin-1', 'cp1252']:
    try:
        text = content.decode(enc)
        print(f"Decoded with {enc}")
        break
    except:
        continue
else:
    print("Could not decode file")
    sys.exit(1)

# Perform replacements
old_visor = """@bp_tasks.route("/visor")
def visor():
    \"\"\"Vista de 'visor' para mostrar trabajos del día y anteriores.\"\"\"
    try:
        with get_db_connection() as conn:
            # Técnicos para filtros si fuera necesario
            technicians = conn.execute("SELECT * FROM technicians ORDER BY name ASC").fetchall()
            
            # Obtener fecha actual
            hoy = dt.now().strftime("%Y-%m-%d")
            
            # Tareas de hoy (cualquier estado)
            tareas_hoy = conn.execute(\"\"\"
                SELECT t.*, p.last_user 
                FROM tasks t 
                LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                WHERE DATE(t.created_at) = CURDATE() OR (t.estado = 'Hecha' AND DATE(t.completed_at) = CURDATE())
                ORDER BY t.created_at DESC
            \"\"\").fetchall()
            
            # Tareas de días anteriores (últimos 7 días)
            tareas_anteriores = conn.execute(\"\"\"
                SELECT t.*, p.last_user 
                FROM tasks t 
                LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                WHERE DATE(t.created_at) < CURDATE() 
                AND DATE(t.created_at) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                ORDER BY t.created_at DESC
                LIMIT 50
            \"\"\").fetchall()

            return render_template("visor_tareas.html", 
                                   tareas_hoy=[_decorate_visor_task(t) for t in tareas_hoy], 
                                   tareas_anteriores=[_decorate_visor_task(t) for t in tareas_anteriores],
                                   technicians=technicians,
                                   hoy=hoy)\n    except Exception as e:
        print(f"Error en visor: {e}")
        return f"Error cargando el visor: {e}", 500"""

new_visor = """@bp_tasks.route("/visor")
def visor():
    \"\"\"Vista de 'visor' para mostrar trabajos con filtros.\"\"\"
    try:
        fecha_filtro = request.args.get("fecha", dt.now().strftime("%Y-%m-%d"))
        pc_filtro = request.args.get("pc", "").strip()
        tech_filtro = request.args.get("technician", "").strip()
        is_filtered = any([request.args.get("fecha"), pc_filtro, tech_filtro])

        with get_db_connection() as conn:
            technicians = conn.execute("SELECT * FROM technicians ORDER BY name ASC").fetchall()
            
            if is_filtered:
                base_sql = "SELECT t.*, p.last_user FROM tasks t LEFT JOIN pcs p ON t.pc_name = p.pc_name WHERE 1=1"
                params = []
                if request.args.get("fecha"):
                    base_sql += " AND (DATE(t.created_at) = %s OR (t.estado = 'Hecha' AND DATE(t.completed_at) = %s))"
                    params.extend([fecha_filtro, fecha_filtro])
                if pc_filtro:
                    base_sql += " AND t.pc_name LIKE %s"
                    params.append(f"%{pc_filtro}%")
                if tech_filtro:
                    base_sql += " AND (t.assigned_to = %s OR t.completed_by = %s)"
                    params.extend([tech_filtro, tech_filtro])
                
                base_sql += " ORDER BY t.created_at DESC LIMIT 200"
                tareas = conn.execute(base_sql, params).fetchall()
                
                return render_template("visor_tareas.html", 
                                       tareas_hoy=[_decorate_visor_task(t) for t in tareas], 
                                       tareas_anteriores=[],
                                       technicians=technicians,
                                       hoy=fecha_filtro,
                                       pc_filtro=pc_filtro,
                                       tech_filtro=tech_filtro,
                                       is_filtered=True)
            else:
                tareas_hoy = conn.execute(\"\"\"
                    SELECT t.*, p.last_user FROM tasks t 
                    LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                    WHERE DATE(t.created_at) = CURDATE() OR (t.estado = 'Hecha' AND DATE(t.completed_at) = CURDATE())
                    ORDER BY t.created_at DESC
                \"\"\").fetchall()
                tareas_anteriores = conn.execute(\"\"\"
                    SELECT t.*, p.last_user FROM tasks t 
                    LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                    WHERE DATE(t.created_at) < CURDATE() AND DATE(t.created_at) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                    ORDER BY t.created_at DESC LIMIT 50
                \"\"\").fetchall()
                return render_template("visor_tareas.html", 
                                       tareas_hoy=[_decorate_visor_task(t) for t in tareas_hoy], 
                                       tareas_anteriores=[_decorate_visor_task(t) for t in tareas_anteriores],
                                       technicians=technicians,
                                       hoy=fecha_filtro,
                                       is_filtered=False)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"Error cargando el visor: {e}", 500"""

old_api = """@bp_tasks.route("/api/visor/data")
def api_visor_data():
    \"\"\"API para actualización en tiempo real del visor.\"\"\"
    try:
        with get_db_connection() as conn:
            # Tareas de hoy
            tareas_hoy_rows = conn.execute(\"\"\"
                SELECT t.*, p.last_user 
                FROM tasks t 
                LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                WHERE DATE(t.created_at) = CURDATE() OR (t.estado = 'Hecha' AND DATE(t.completed_at) = CURDATE())
                ORDER BY t.created_at DESC
            \"\"\").fetchall()
            
            # Tareas anteriores (pendientes o recientes)
            tareas_anteriores_rows = conn.execute(\"\"\"
                SELECT t.*, p.last_user 
                FROM tasks t 
                LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                WHERE DATE(t.created_at) < CURDATE() 
                AND DATE(t.created_at) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                ORDER BY t.created_at DESC
                LIMIT 50
            \"\"\").fetchall()

            def format_tasks(rows):
                return [_decorate_visor_task(t) for t in rows]
            
            return jsonify({
                "status": "success", 
                "tasks_hoy": format_tasks(tareas_hoy_rows),
                "tasks_anteriores": format_tasks(tareas_anteriores_rows)
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500"""

new_api = """@bp_tasks.route("/api/visor/data")
def api_visor_data():
    \"\"\"API para actualización en tiempo real del visor con soporte de filtros.\"\"\"
    try:
        fecha_filtro = request.args.get("fecha")
        pc_filtro = request.args.get("pc", "").strip()
        tech_filtro = request.args.get("technician", "").strip()
        is_filtered = any([fecha_filtro, pc_filtro, tech_filtro])

        with get_db_connection() as conn:
            if is_filtered:
                base_sql = "SELECT t.*, p.last_user FROM tasks t LEFT JOIN pcs p ON t.pc_name = p.pc_name WHERE 1=1"
                params = []
                if fecha_filtro:
                    base_sql += " AND (DATE(t.created_at) = %s OR (t.estado = 'Hecha' AND DATE(t.completed_at) = %s))"
                    params.extend([fecha_filtro, fecha_filtro])
                if pc_filtro:
                    base_sql += " AND t.pc_name LIKE %s"
                    params.append(f"%{pc_filtro}%")
                if tech_filtro:
                    base_sql += " AND (t.assigned_to = %s OR t.completed_by = %s)"
                    params.extend([tech_filtro, tech_filtro])
                
                base_sql += " ORDER BY t.created_at DESC LIMIT 200"
                rows = conn.execute(base_sql, params).fetchall()
                
                return jsonify({
                    "status": "success", 
                    "tasks_hoy": [_decorate_visor_task(t) for t in rows],
                    "tasks_anteriores": []
                })
            else:
                # Tareas de hoy
                tareas_hoy_rows = conn.execute(\"\"\"
                    SELECT t.*, p.last_user 
                    FROM tasks t 
                    LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                    WHERE DATE(t.created_at) = CURDATE() OR (t.estado = 'Hecha' AND DATE(t.completed_at) = CURDATE())
                    ORDER BY t.created_at DESC
                \"\"\").fetchall()
                
                # Tareas anteriores (pendientes o recientes)
                tareas_anteriores_rows = conn.execute(\"\"\"
                    SELECT t.*, p.last_user 
                    FROM tasks t 
                    LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                    WHERE DATE(t.created_at) < CURDATE() 
                    AND DATE(t.created_at) >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
                    ORDER BY t.created_at DESC
                    LIMIT 50
                \"\"\").fetchall()

                return jsonify({
                    "status": "success", 
                    "tasks_hoy": [_decorate_visor_task(t) for t in tareas_hoy_rows],
                    "tasks_anteriores": [_decorate_visor_task(t) for t in tareas_anteriores_rows]
                })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500"""

# We use a very fuzzy match by replacing non-ascii or problematic parts if needed, 
# but here we try literal replacement first, then if it fails, we can use regex or similar.
# Since the goal is to fix the file, I'll just write it back as UTF-8.

text = text.replace(old_visor, new_visor)
text = text.replace(old_api, new_api)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(text)
print("File updated and saved as UTF-8")
