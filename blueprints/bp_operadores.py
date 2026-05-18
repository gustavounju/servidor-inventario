from flask import Blueprint, render_template, jsonify, request
from database.db_core import get_db_connection
from utils.auth import is_authenticated, current_user, has_permission, role_label
import datetime
from services.ai_assistant import predict_category
from services.push_notifications import notify_all_technicians

bp_operadores = Blueprint('operadores', __name__)

def _operator_allowed():
    if not is_authenticated():
        return False
    user = current_user()
    return user.get("role") == "operador" or user.get("is_superuser")

def _load_requesters_catalog():
    with get_db_connection() as conn:
        return [dict(row) for row in conn.execute("""
            SELECT
                a.username,
                a.real_name,
                a.phone,
                COALESCE(NULLIF(a.fuero, ''), pc_user.fuero) AS fuero
            FROM ad_users a
            LEFT JOIN (
                SELECT
                    LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) AS username,
                    MAX(NULLIF(fuero, '')) AS fuero
                FROM pcs
                WHERE last_user IS NOT NULL
                  AND last_user != ''
                  AND fuero IS NOT NULL
                  AND fuero != ''
                GROUP BY LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1))
            ) pc_user ON pc_user.username = LOWER(TRIM(a.username))
            UNION
            SELECT DISTINCT
                LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) as username,
                last_user as real_name,
                NULL as phone,
                fuero
            FROM pcs
            WHERE last_user IS NOT NULL
              AND last_user != ''
              AND LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) NOT IN (SELECT username FROM ad_users)
            ORDER BY real_name
        """).fetchall()]

@bp_operadores.route("/operadores")
def operadores_view():
    if not is_authenticated():
        from flask import redirect, url_for
        return redirect(url_for("auth.login"))
    
    # Solo permitimos a operadores o administradores
    user = current_user()
    if not _operator_allowed():
        from flask import redirect, url_for
        return redirect(url_for("dashboard.dashboard"))

    return render_template("operadores.html",
                           user=user,
                           role_label=role_label(),
                           requesters=_load_requesters_catalog())

@bp_operadores.route("/api/operadores/create_task", methods=["POST"])
def api_operadores_create_task():
    if not _operator_allowed():
        return jsonify({"status": "error", "message": "No autorizado"}), 403

    try:
        data = request.get_json(silent=True) or {}
        descripcion = (data.get("descripcion") or "").strip()
        solicitante = (data.get("solicitante") or "").strip()
        fuero = (data.get("fuero") or "").strip()
        is_done = bool(data.get("is_done"))
        solucion = (data.get("solucion") or "").strip()

        if not descripcion or not solicitante:
            return jsonify({"status": "error", "message": "Faltan descripción y solicitante"}), 400

        categoria = predict_category(descripcion)
        user = current_user()
        operator_name = user.get("display_name") or user.get("username") or "Operador"
        estado = "Hecha" if is_done else "Pendiente"
        completed_by = operator_name if is_done else None
        completed_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") if is_done else None

        with get_db_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tasks
                    (descripcion, solicitante, estado, created_at, categoria, assigned_to, fuero, pc_name, tipo_actividad, prioridad, impacto_valor, completed_by, completed_at, solucion)
                VALUES
                    (%s, %s, %s, NOW(), %s, NULL, %s, 'PC Generica', 'tarea', 1, 1, %s, %s, %s)
                """,
                (descripcion, solicitante, estado, categoria, fuero, completed_by, completed_at, solucion),
            )
            task_id = cursor.lastrowid
            conn.commit()

        try:
            notify_all_technicians(
                title="Nueva tarea de operador",
                body=f"{solicitante}: {descripcion}",
                url="/tecnicos"
            )
        except Exception as e:
            print(f"Error notifying operator task: {e}")

        return jsonify({
            "status": "success",
            "id": task_id,
            "created_by": operator_name,
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_operadores.route("/api/operadores/stats")
def api_operadores_stats():
    try:
        with get_db_connection() as conn:
            # Tareas creadas hoy por cualquier medio (ya que los operadores atienden el teléfono)
            tareas_hoy = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE DATE(created_at) = CURDATE()").fetchone()["c"]
            # Tareas pendientes totales
            pendientes = conn.execute("SELECT COUNT(*) as c FROM tasks WHERE estado != 'Hecha'").fetchone()["c"]
            
            return jsonify({
                "status": "success",
                "tareas_hoy": tareas_hoy,
                "pendientes": pendientes
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_operadores.route("/api/operadores/tasks_today")
def api_operadores_tasks_today():
    try:
        with get_db_connection() as conn:
            rows = conn.execute("""
                SELECT t.id, t.pc_name, t.descripcion, t.solicitante, t.estado, t.created_at, t.categoria, t.assigned_to, t.tipo_actividad
                FROM tasks t
                WHERE DATE(t.created_at) = CURDATE()
                ORDER BY t.created_at DESC
            """).fetchall()
            
            tasks = []
            for r in rows:
                d = dict(r)
                if d['created_at']:
                    d['created_at_fmt'] = d['created_at'].strftime("%H:%M")
                tasks.append(d)
                
            return jsonify({
                "status": "success",
                "tasks": tasks
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
