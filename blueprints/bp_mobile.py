from flask import Blueprint, jsonify, request, render_template
import datetime
from database.db_core import get_db_connection
from services.ai_assistant import predict_category
# from voice_processor import process_voice_command # Ensure it handles import cleanly if missing

bp_mobile = Blueprint('mobile', __name__)

@bp_mobile.route("/mobile")
def mobile_view():
    return render_template("mobile.html")

@bp_mobile.route("/mobile/scanner")
def mobile_scanner_view():
    return render_template("mobile_scanner.html")

@bp_mobile.route("/api/mobile/data")
def api_mobile_data():
    try:
        with get_db_connection() as conn:
            techs = [dict(r) for r in conn.execute("SELECT * FROM technicians ORDER BY name").fetchall()]
            unassigned = [dict(r) for r in conn.execute("SELECT * FROM tasks WHERE (pc_name IS NULL OR pc_name = '') AND estado != 'Hecha' ORDER BY created_at DESC").fetchall()]
            all_active = [dict(r) for r in conn.execute("SELECT t.*, p.fuero as pc_fuero FROM tasks t LEFT JOIN pcs p ON t.pc_name = p.pc_name WHERE t.estado != 'Hecha' ORDER BY t.created_at DESC").fetchall()]
            pcs_query = conn.execute("SELECT pc_name, last_user, fuero FROM pcs WHERE is_active='True' ORDER BY pc_name").fetchall()
            pcs = [{"name": r["pc_name"], "user": r["last_user"] or "Desconocido", "area": r["fuero"] or "Desconocido"} for r in pcs_query]

        return jsonify({"technicians": techs, "unassigned": unassigned, "active_tasks": all_active, "pcs": pcs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp_mobile.route("/api/mobile/create_task", methods=["POST"])
def api_mobile_create_task():
    try:
        data = request.json
        descripcion = data.get("descripcion")
        pc_name = data.get("pc_name")
        technician = data.get("technician")
        solicitante_input = data.get("solicitante", "").strip()
        is_done = data.get("is_done", False)
        es_infraestructura = data.get("es_infraestructura", False)
        tecnico_ejecutor = data.get("tecnico", "")

        if not descripcion or not technician: return jsonify({"status": "error", "message": "Faltan datos"}), 400
        if es_infraestructura and not pc_name: pc_name = "Infraestructura"

        categoria = predict_category(descripcion)
        estado = "Hecha" if is_done else "Pendiente"
        created_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        completed_at = created_at if is_done else None
        
        if is_done and tecnico_ejecutor: completed_by = tecnico_ejecutor
        elif is_done: completed_by = technician
        else: completed_by = None
        
        solicitante = solicitante_input if solicitante_input else "No Especificado (Móvil)"
        assigned_to = technician

        # MySQL exige NULL (no string vacío) para no violar la FK de pc_name
        if not pc_name:
            pc_name = None

        with get_db_connection() as conn:
             cursor = conn.execute(
                "INSERT INTO tasks (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to)
            )
             new_id = cursor.lastrowid
             conn.commit()

        return jsonify({"status": "success", "id": new_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_mobile.route("/api/mobile/update_task", methods=["POST"])
def api_mobile_update_task():
    try:
        data = request.json
        task_id = data.get("id")
        action = data.get("action")
        technician = data.get("technician")
        pc_name = data.get("pc_name")

        if not task_id or not action or not technician: return jsonify({"status": "error", "message": "Datos incompletos"}), 400

        with get_db_connection() as conn:
            if action == "claim":
                conn.execute("UPDATE tasks SET assigned_to=%s WHERE id=%s", (technician, task_id))
            elif action == "complete":
                 sql = "UPDATE tasks SET estado='Hecha', completed_by=%s, completed_at=NOW()"
                 params = [technician]
                 if pc_name:
                     sql += ", pc_name=%s"
                     params.append(pc_name)
                 sql += " WHERE id=%s"
                 params.append(task_id)
                 conn.execute(sql, params)
            conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_mobile.route("/api/mobile/parse_voice", methods=["POST"])
def api_mobile_parse_voice():
    try:
        data = request.json
        text = data.get("text", "")
        if not text: return jsonify({"status": "error", "message": "Texto vacío"}), 400
        
        try:
            import voice_processor
            result = voice_processor.process_voice_command(text)
            return jsonify({"status": "success", "data": result})
        except Exception as e:
            print(f"Error in api_mobile_parse_voice: {e}")
            return jsonify({"status": "success", "data": {"descripcion": text, "solicitante": "", "error_voice": str(e)}})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
