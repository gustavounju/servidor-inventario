from flask import Blueprint, jsonify, request, render_template
from database.db_core import get_db_connection

bp_stock = Blueprint('stock', __name__)

@bp_stock.route("/api/components/<string:serial_number>", methods=["GET"])
def get_component(serial_number):
    try:
        with get_db_connection() as conn:
            comp = conn.execute("SELECT * FROM components WHERE serial_number = ?", (serial_number,)).fetchone()
            if comp:
                return jsonify({"status": "found", "data": dict(comp)})
            else:
                return jsonify({"status": "not_found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_stock.route("/stock")
def stock_view():
    return render_template("stock.html")

@bp_stock.route("/api/components/list")
def list_components():
    try:
        with get_db_connection() as conn:
            comps = [dict(r) for r in conn.execute("SELECT * FROM components ORDER BY created_at DESC").fetchall()]
        return jsonify(comps)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp_stock.route("/api/components/add", methods=["POST"])
def add_component():
    try:
        data = request.json
        serial = data.get("serial_number")
        ctype = data.get("component_type")
        model = data.get("brand_model")
        
        if not serial or not ctype:
            return jsonify({"status": "error", "message": "Faltan datos"}), 400
            
        with get_db_connection() as conn:
            conn.execute("INSERT INTO components (serial_number, component_type, brand_model, status) VALUES (?, ?, ?, 'Stock')", (serial, ctype, model))
            conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_stock.route("/api/components/assign", methods=["POST"])
def assign_component():
    try:
        data = request.json
        serial = data.get("serial_number")
        pc_name = data.get("pc_name")
        
        if not serial or not pc_name: return jsonify({"status": "error", "message": "Faltan datos"}), 400
            
        with get_db_connection() as conn:
            comp = conn.execute("SELECT * FROM components WHERE serial_number = ?", (serial,)).fetchone()
            if not comp: return jsonify({"status": "error", "message": "Componente no existe"}), 404
            
            conn.execute("UPDATE components SET status = 'Installed', assigned_pc = ? WHERE serial_number = ?", (pc_name, serial))
            detalles = f"{comp['component_type']} {comp['brand_model']} (S/N: {serial})"
            conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (?, 'COMPONENT_ASSIGN', 'Stock', ?)", (pc_name, detalles))
            conn.commit()
            
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_stock.route("/api/components/return", methods=["POST"])
def return_component():
    try:
        data = request.json
        serial = data.get("serial_number")
        if not serial: return jsonify({"status": "error", "message": "Falta serial"}), 400
            
        with get_db_connection() as conn:
            comp = conn.execute("SELECT * FROM components WHERE serial_number = ?", (serial,)).fetchone()
            if not comp: return jsonify({"status": "error", "message": "Componente no existe"}), 404
            
            old_pc = comp["assigned_pc"] or "Unknown"
            conn.execute("UPDATE components SET status = 'Stock', assigned_pc = NULL WHERE serial_number = ?", (serial,))
            
            if old_pc != "Unknown":
                detalles = f"{comp['component_type']} {comp['brand_model']} (S/N: {serial})"
                conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (?, 'COMPONENT_RETURN', ?, 'Stock')", (old_pc, detalles))
            conn.commit()
            
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
