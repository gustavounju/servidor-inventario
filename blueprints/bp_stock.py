from flask import Blueprint, jsonify, request, render_template
from database.db_core import get_db_connection

bp_stock = Blueprint('stock', __name__)

@bp_stock.route("/api/components/<string:serial_number>", methods=["GET"])
def get_component(serial_number):
    try:
        with get_db_connection() as conn:
            comp = conn.execute("SELECT * FROM components WHERE serial_number = %s", (serial_number,)).fetchone()
            if comp:
                data = dict(comp)
                if data.get('created_at'):
                    data['created_at'] = data['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                return jsonify({"status": "found", "data": data})
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
            rows = conn.execute("SELECT * FROM components ORDER BY created_at DESC").fetchall()
            comps = []
            for r in rows:
                item = dict(r)
                if item.get('created_at'):
                    item['created_at'] = item['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                comps.append(item)
        return jsonify(comps)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp_stock.route("/api/components/suppliers")
def list_suppliers():
    try:
        with get_db_connection() as conn:
            suppliers = [r['supplier'] for r in conn.execute("SELECT DISTINCT supplier FROM components WHERE supplier IS NOT NULL AND supplier != '' ORDER BY supplier").fetchall()]
        return jsonify(suppliers)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp_stock.route("/api/components/add", methods=["POST"])
def add_component():
    try:
        data = request.json
        serial = data.get("serial_number")
        ctype = data.get("component_type")
        model = data.get("brand_model")
        supplier = data.get("supplier_name", "")
        invoice = data.get("remito_number", "")
        
        if not serial or not ctype:
            return jsonify({"status": "error", "message": "Faltan datos"}), 400
            
        with get_db_connection() as conn:
            conn.execute("INSERT INTO components (serial_number, component_type, brand_model, status, supplier, invoice_number) VALUES (%s, %s, %s, 'Stock', %s, %s)", (serial, ctype, model, supplier, invoice))
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
            comp = conn.execute("SELECT * FROM components WHERE serial_number = %s", (serial,)).fetchone()
            if not comp: return jsonify({"status": "error", "message": "Componente no existe"}), 404
            
            conn.execute("UPDATE components SET status = 'Installed', assigned_pc = %s WHERE serial_number = %s", (pc_name, serial))
            detalles = f"{comp['component_type']} {comp['brand_model']} (S/N: {serial})"
            conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, 'COMPONENT_ASSIGN', 'Stock', %s)", (pc_name, detalles))
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
            comp = conn.execute("SELECT * FROM components WHERE serial_number = %s", (serial,)).fetchone()
            if not comp: return jsonify({"status": "error", "message": "Componente no existe"}), 404
            
            old_pc = comp["assigned_pc"] or "Unknown"
            conn.execute("UPDATE components SET status = 'Stock', assigned_pc = NULL WHERE serial_number = %s", (serial,))
            
            if old_pc != "Unknown":
                detalles = f"{comp['component_type']} {comp['brand_model']} (S/N: {serial})"
                conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, 'COMPONENT_RETURN', %s, 'Stock')", (old_pc, detalles))
            conn.commit()
            
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_stock.route("/api/components/delete", methods=["POST"])
def delete_component():
    try:
        data = request.json
        serial = data.get("serial_number")
        if not serial: return jsonify({"status": "error", "message": "Falta serial"}), 400
            
        with get_db_connection() as conn:
            comp = conn.execute("SELECT * FROM components WHERE serial_number = %s", (serial,)).fetchone()
            if not comp: return jsonify({"status": "error", "message": "Componente no existe"}), 404
            
            old_pc = comp["assigned_pc"]
            conn.execute("DELETE FROM components WHERE serial_number = %s", (serial,))
            
            if old_pc is not None and old_pc != "Unknown":
                detalles = f"{comp['component_type']} {comp['brand_model']} (S/N: {serial})"
                conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value) VALUES (%s, 'COMPONENT_DELETED', %s, 'DELETED')", (old_pc, detalles))
                
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

