from flask import Blueprint, abort, jsonify, request, render_template
import datetime
import os
import logging
from database.db_core import get_db_connection
from services.ai_assistant import predict_category
from services.push_notifications import notify_all_technicians
from utils.auth import current_technician_identity, current_user, list_technician_users
from blueprints.bp_tasks import _attach_task_actions_bulk
# from voice_processor import process_voice_command # Ensure it handles import cleanly if missing

bp_mobile = Blueprint('mobile', __name__)

@bp_mobile.route("/mobile")
def mobile_view():
    from flask import redirect, url_for
    return redirect(url_for("tecnicos.tecnicos_view"))

@bp_mobile.route("/mobile/scanner")
def mobile_scanner_view():
    if current_user().get("role") == "operador":
        abort(403)
    return render_template("mobile_scanner.html")

def _json_serializable(data):
    """Auxiliar para convertir objetos no serializables (como datetime) a string."""
    if isinstance(data, list):
        return [_json_serializable(i) for i in data]
    if isinstance(data, dict):
        return {k: _json_serializable(v) for k, v in data.items()}
    if isinstance(data, (datetime.datetime, datetime.date)):
        return data.strftime("%Y-%m-%d %H:%M:%S")
    return data

@bp_mobile.route("/api/mobile/data")
def api_mobile_data():
    try:
        with get_db_connection() as conn:
            techs = list_technician_users()
            unassigned = [dict(r) for r in conn.execute("SELECT * FROM tasks WHERE (pc_name IS NULL OR pc_name = '') AND estado != 'Hecha' ORDER BY created_at DESC").fetchall()]
            unassigned = _attach_task_actions_bulk(unassigned, conn)
            all_active = [dict(r) for r in conn.execute("""
                SELECT t.*, p.fuero as pc_fuero 
                FROM tasks t 
                LEFT JOIN pcs p ON t.pc_name = p.pc_name 
                WHERE t.estado != 'Hecha' 
                ORDER BY 
                    CASE WHEN t.tipo_actividad = 'incidente' THEN 0 WHEN t.tipo_actividad = 'riesgo' THEN 1 ELSE 2 END,
                    t.prioridad DESC, 
                    t.created_at DESC
            """).fetchall()]
            all_active = _attach_task_actions_bulk(all_active, conn)
            
            # Registrar última actividad móvil (ping de 30seg)
            tech_identity = current_technician_identity()
            if tech_identity:
                conn.execute("UPDATE technicians SET last_mobile_activity = NOW() WHERE name = %s", (tech_identity,))
                conn.commit()
            
            # Tareas hechas por el técnico actual para el historial (últimas 50)
            my_history = [dict(r) for r in conn.execute(
                "SELECT t.*, p.fuero as pc_fuero FROM tasks t LEFT JOIN pcs p ON t.pc_name = p.pc_name WHERE t.estado = 'Hecha' AND t.completed_by = %s ORDER BY t.completed_at DESC LIMIT 50",
                (tech_identity,)
            ).fetchall()]
            my_history = _attach_task_actions_bulk(my_history, conn)
            
            # Total histórico de tareas tomadas/resueltas por este técnico
            my_historical_total = 0
            if tech_identity:
                row = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE (estado = 'Hecha' AND completed_by = %s) OR (estado != 'Hecha' AND assigned_to = %s)", (tech_identity, tech_identity)).fetchone()
                if row:
                    my_historical_total = row["c"]

            pcs_query = conn.execute("SELECT pc_name, last_user, fuero FROM pcs WHERE is_active=1 ORDER BY pc_name").fetchall()
            requesters = [dict(r) for r in conn.execute(
                """
                SELECT username, real_name, phone
                FROM ad_users
                UNION
                SELECT DISTINCT LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) as username, 
                                last_user as real_name, 
                                NULL as phone 
                FROM pcs 
                WHERE last_user IS NOT NULL AND last_user != '' 
                  AND LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) NOT IN (SELECT username FROM ad_users)
                ORDER BY real_name
                """
            ).fetchall()]
            pcs = [{"name": r["pc_name"], "user": r["last_user"] or "Desconocido", "area": r["fuero"] or "Desconocido"} for r in pcs_query]

            # Estadísticas globales para el contador del móvil
            global_tomadas = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado != 'Hecha' AND assigned_to IS NOT NULL AND assigned_to != ''").fetchone()["c"]
            global_libres = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado != 'Hecha' AND (assigned_to IS NULL OR assigned_to = '')").fetchone()["c"]
            global_hechas = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado = 'Hecha' AND DATE(completed_at) = CURDATE()").fetchone()["c"]
            global_stats = {
                "tomadas": global_tomadas,
                "libres": global_libres,
                "hechas_hoy": global_hechas
            }

        payload = {
            "technicians": techs, 
            "unassigned": unassigned, 
            "active_tasks": all_active, 
            "my_history": my_history,
            "my_historical_total": my_historical_total,
            "pcs": pcs, 
            "requesters": requesters,
            "global_stats": global_stats
        }
        return jsonify(_json_serializable(payload))
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@bp_mobile.route("/api/mobile/notifications")
def api_mobile_notifications():
    try:
        with get_db_connection() as conn:
            # Traer las últimas 50 notificaciones
            rows = [dict(r) for r in conn.execute("SELECT * FROM app_notifications ORDER BY created_at DESC LIMIT 50").fetchall()]
            return jsonify(_json_serializable(rows))
    except Exception as e:
        logging.error(f"Error api_mobile_notifications: {e}")
        return jsonify({"error": str(e)}), 500

@bp_mobile.route("/api/mobile/create_task", methods=["POST"])
def api_mobile_create_task():
    try:
        data = request.json
        descripcion = data.get("descripcion")
        pc_name = data.get("pc_name")
        technician = current_technician_identity()
        solicitante_input = data.get("solicitante", "").strip()
        is_done = data.get("is_done", False)
        es_infraestructura = data.get("es_infraestructura", False)
        tecnico_ejecutor = technician

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
            pc_name = "PC Generica"

        tipo_actividad = data.get("tipo_actividad", "tarea").lower()
        prioridad = data.get("prioridad", 2)
        impacto_valor = data.get("impacto_valor", 2)
        solucion = data.get("solucion", "").strip()

        with get_db_connection() as conn:
             cursor = conn.execute(
                """INSERT INTO tasks (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to, tipo_actividad, prioridad, impacto_valor, solucion) 
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to, tipo_actividad, prioridad, impacto_valor, solucion)
            )
             new_id = cursor.lastrowid
             conn.commit()

        # Notify other technicians via Web Push
        try:
            notify_all_technicians(
                title="Nueva Tarea",
                body=f"{solicitante}: {descripcion}",
                url="/tecnicos"
            )
        except Exception as e:
            logging.error(f"Error sending push: {e}")

        return jsonify({"status": "success", "id": new_id})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_mobile.route("/api/mobile/update_task", methods=["POST"])
def api_mobile_update_task():
    try:
        data = request.json
        task_id = data.get("id")
        action = data.get("action")
        technician = current_technician_identity()
        pc_name = data.get("pc_name")

        descripcion = data.get("descripcion")
        solucion = data.get("solucion")

        if not task_id or not action or not technician: return jsonify({"status": "error", "message": "Datos incompletos"}), 400

        with get_db_connection() as conn:
            if action == "claim":
                cursor = conn.execute(
                    "UPDATE tasks SET assigned_to=%s WHERE id=%s AND (assigned_to IS NULL OR assigned_to = '')", 
                    (technician, task_id)
                )
                if cursor.rowcount == 0:
                    current_task = conn.execute("SELECT assigned_to FROM tasks WHERE id=%s", (task_id,)).fetchone()
                    if current_task:
                        owner = current_task.get("assigned_to")
                        if owner and owner != technician:
                            return jsonify({"status": "error", "message": f"Muy lento, la tarea acaba de ser tomada por {owner}."}), 409
                        elif owner == technician:
                            return jsonify({"status": "success"})  # Ya la había tomado él mismo
                    return jsonify({"status": "error", "message": "No se pudo tomar la tarea (ya no existe o no está libre)."}), 404
            elif action == "complete":
                 sql = "UPDATE tasks SET estado='Hecha', completed_by=%s, completed_at=NOW(), assigned_to=COALESCE(NULLIF(assigned_to, ''), %s), solucion=%s"
                 params = [technician, technician, (solucion or "").strip()]
                 if pc_name:
                     sql += ", pc_name=%s"
                     params.append(pc_name)
                 if descripcion:
                     sql += ", descripcion=%s"
                     params.append(descripcion)
                 sql += " WHERE id=%s"
                 params.append(task_id)
                 cursor = conn.execute(sql, params)
                 if cursor.rowcount == 0:
                     return jsonify({"status": "error", "message": "No se encontro la tarea para completar."}), 404
            elif action == "edit":
                 sql = "UPDATE tasks SET descripcion=%s, solucion=%s WHERE id=%s"
                 conn.execute(sql, (descripcion, solucion, task_id))
            elif action == "assign_pc":
                 if not pc_name:
                     return jsonify({"status": "error", "message": "Seleccioná una PC válida."}), 400
                 exists = conn.execute("SELECT 1 FROM pcs WHERE pc_name=%s", (pc_name,)).fetchone()
                 if not exists:
                     return jsonify({"status": "error", "message": "La PC seleccionada no existe."}), 404
                 conn.execute("UPDATE tasks SET pc_name=%s WHERE id=%s AND assigned_to=%s", (pc_name, task_id, technician))
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
            logging.error(f"Error in api_mobile_parse_voice: {e}")
            return jsonify({"status": "success", "data": {"descripcion": text, "solicitante": "", "error_voice": str(e)}})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
@bp_mobile.route("/api/mobile/subscribe_push", methods=["POST"])
def api_subscribe_push():
    """Saves an FCM token for a technician device."""
    try:
        data = request.json
        technician = current_technician_identity()
        token = data.get("token", "").strip()
        if not technician or not token:
            return jsonify({"status": "error", "message": "Faltan datos"}), 400

        with get_db_connection() as conn:
            conn.execute(
                """
                INSERT INTO fcm_tokens (technician_name, token)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE token = VALUES(token), updated_at = NOW()
                """,
                (technician, token)
            )
            conn.commit()
        logging.info(f"[FCM] Token registrado para: {technician}")
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_mobile.route("/api/mobile/voice-upload", methods=["POST"])
def voice_upload():
    """Recibe audio, lo guarda temporalmente y usa Gemini para extraer descripcion/solicitante."""
    if 'audio' not in request.files:
        return jsonify({"status": "error", "message": "No audio file"}), 400
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({"status": "error", "message": "Empty filename"}), 400

    upload_dir = "uploads"
    if not os.path.exists(upload_dir): os.makedirs(upload_dir)
    
    # Extraer extensión real (importante para que Gemini lo procese bien)
    ext = audio_file.filename.split('.')[-1] if '.' in audio_file.filename else "mpeg"
    filename = f"voice_{int(datetime.datetime.now().timestamp())}.{ext}"
    temp_path = os.path.join(upload_dir, filename)
    logging.debug(f"Guardando audio recibido como {temp_path}")
    
    try:
        audio_file.save(temp_path)
        from voice_processor import process_voice_command
        # Gemini multimodal: escucha y entiende
        result = process_voice_command(audio_path=temp_path)
        return jsonify({"status": "success", "result": result})
    except Exception as e:
        logging.error(f"Error en voice-upload: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            try: os.remove(temp_path)
            except: pass

