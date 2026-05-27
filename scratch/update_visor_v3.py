import sys

filepath = 'blueprints/bp_tasks.py'
with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the start of visor()
start_line = -1
for i, line in enumerate(lines):
    if '/visor' in line and '@bp_tasks.route' in line:
        start_line = i
        break

if start_line == -1:
    print("Could not find visor route")
    sys.exit(1)

# Keep everything up to start_line
new_lines = lines[:start_line]

# Add new visor and api_visor_data
new_code = """@bp_tasks.route("/visor")
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
        return f"Error cargando el visor: {e}", 500

@bp_tasks.route("/api/visor/data")
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
        return jsonify({"status": "error", "message": str(e)}), 500
"""

with open(filepath, 'w', encoding='utf-8', newline='\n') as f:
    f.writelines(new_lines)
    f.write(new_code)
print("File rewritten from visor route onwards")
