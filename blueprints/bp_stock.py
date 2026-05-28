from flask import Blueprint, jsonify, request, render_template
from utils.auth import current_username
from database.db_core import get_db_connection

bp_stock = Blueprint('stock', __name__)

@bp_stock.route("/api/components/<path:serial_number>", methods=["GET"])
def get_component(serial_number):
    try:
        with get_db_connection() as conn:
            comp = conn.execute("SELECT * FROM components WHERE serial_number = %s", (serial_number,)).fetchone()
            if comp:
                data = dict(comp)
                if data.get('created_at'):
                    data['created_at'] = data['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                return jsonify({"status": "found", "data": data})
            
            ups = conn.execute("SELECT * FROM ups_inventory WHERE code = %s", (serial_number,)).fetchone()
            if ups:
                data = dict(ups)
                if data.get('created_at'):
                    data['created_at'] = data['created_at'].strftime("%Y-%m-%d %H:%M:%S")
                # Format to match components schema for scanner compatibility
                data['serial_number'] = data['code']
                data['component_type'] = 'UPS'
                data['brand_model'] = data['model']
                data['status'] = 'Installed' if data.get('assigned_pc') else 'Stock'
                return jsonify({"status": "found", "data": data})
                
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
            if ctype.upper() == 'UPS' or ctype.upper() == 'EQUIPO UPS':
                # Las UPS van a su tabla específica
                conn.execute("INSERT INTO ups_inventory (code, model, supplier, invoice_number) VALUES (%s, %s, %s, %s)", (serial, model, supplier, invoice))
            else:
                conn.execute("INSERT INTO components (serial_number, component_type, brand_model, status, supplier, invoice_number) VALUES (%s, %s, %s, 'Stock', %s, %s)", (serial, ctype, model, supplier, invoice))
            
            from utils.auth import current_technician_identity
            tech = current_technician_identity()
            if tech:
                from datetime import datetime
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                desc = f"Escáner: Registró nuevo componente en Stock: {ctype} {model} (S/N: {serial})"
                conn.execute(
                    "INSERT INTO tasks (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    ('Stock (Escáner)', desc, tech, 'Hecha', now_str, tech, now_str, 'Hardware', tech)
                )
                
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
            if not comp: 
                # Check ups_inventory
                ups = conn.execute("SELECT * FROM ups_inventory WHERE code = %s", (serial,)).fetchone()
                if not ups:
                    return jsonify({"status": "error", "message": "Componente no existe"}), 404
                else:
                    # Logic for UPS assignment
                    conn.execute("UPDATE ups_inventory SET assigned_pc = %s WHERE code = %s", (pc_name, serial))
                    detalles = f"UPS {ups['model']} (S/N: {serial})"
                    from utils.auth import current_username, current_technician_identity
                    tech = current_technician_identity()
                    conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                                 (pc_name, 'UPS Asignada', 'Stock', detalles, current_username() or tech, "GESTION_INFRAESTRUCTURA", request.remote_addr))
                    if tech:
                        from datetime import datetime
                        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        desc = f"Escáner: Instaló componente (UPS {ups['model']})"
                        conn.execute(
                            "INSERT INTO tasks (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (pc_name, desc, tech, 'Hecha', now_str, tech, now_str, 'Hardware', tech)
                        )
                    conn.commit()
                    return jsonify({"status": "success"})
                    
            conn.execute("UPDATE components SET status = 'Installed', assigned_pc = %s WHERE serial_number = %s", (pc_name, serial))
            detalles = f"{comp['component_type']} {comp['brand_model']} (S/N: {serial})"
            conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                         (pc_name, 'COMPONENT_ASSIGN', 'Stock', detalles, current_username() or tech, "GESTION_STOCK", request.remote_addr))
            
            from utils.auth import current_technician_identity
            tech = current_technician_identity()
            if tech:
                from datetime import datetime
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                desc = f"Escáner: Instaló componente ({comp['component_type']} {comp['brand_model']})"
                conn.execute(
                    "INSERT INTO tasks (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (pc_name, desc, tech, 'Hecha', now_str, tech, now_str, 'Hardware', tech)
                )

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
            if not comp: 
                # Check ups_inventory
                ups = conn.execute("SELECT * FROM ups_inventory WHERE code = %s", (serial,)).fetchone()
                if not ups:
                    return jsonify({"status": "error", "message": "Componente no existe"}), 404
                else:
                    old_pc = ups["assigned_pc"] or "Unknown"
                    conn.execute("UPDATE ups_inventory SET assigned_pc = NULL WHERE code = %s", (serial,))
                    
                    from utils.auth import current_username, current_technician_identity
                    tech = current_technician_identity()
                    if old_pc != "Unknown":
                        detalles = f"UPS {ups['model']} (S/N: {serial})"
                        conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                                     (old_pc, 'UPS Desasignada', detalles, 'Stock', current_username() or tech, "GESTION_INFRAESTRUCTURA", request.remote_addr))
                        
                    if tech:
                        from datetime import datetime
                        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        desc = f"Escáner: Retiró componente y devolvió a Stock (UPS {ups['model']})"
                        conn.execute(
                            "INSERT INTO tasks (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (old_pc, desc, tech, 'Hecha', now_str, tech, now_str, 'Hardware', tech)
                        )
                    conn.commit()
                    return jsonify({"status": "success"})
                    
            old_pc = comp["assigned_pc"] or "Unknown"
            conn.execute("UPDATE components SET status = 'Stock', assigned_pc = NULL WHERE serial_number = %s", (serial,))
            
            if old_pc != "Unknown":
                detalles = f"{comp['component_type']} {comp['brand_model']} (S/N: {serial})"
                conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                             (old_pc, 'COMPONENT_RETURN', detalles, 'Stock', current_username() or tech, "GESTION_STOCK", request.remote_addr))
                
            from utils.auth import current_technician_identity
            tech = current_technician_identity()
            if tech:
                from datetime import datetime
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                desc = f"Escáner: Retiró componente y devolvió a Stock ({comp['component_type']} {comp['brand_model']})"
                conn.execute(
                    "INSERT INTO tasks (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (old_pc, desc, tech, 'Hecha', now_str, tech, now_str, 'Hardware', tech)
                )

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
            if not comp: 
                # Check ups_inventory
                ups = conn.execute("SELECT * FROM ups_inventory WHERE code = %s", (serial,)).fetchone()
                if not ups:
                    return jsonify({"status": "error", "message": "Componente no existe"}), 404
                else:
                    old_pc = ups["assigned_pc"]
                    # Also unassign battery if any
                    if ups.get('assigned_battery_id'):
                        conn.execute("UPDATE components SET status = 'Stock' WHERE id = %s", (ups['assigned_battery_id'],))
                    conn.execute("DELETE FROM ups_inventory WHERE code = %s", (serial,))
                    
                    from utils.auth import current_username
                    if old_pc is not None and old_pc != "Unknown":
                        detalles = f"UPS {ups['model']} (S/N: {serial})"
                        conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                                     (old_pc, 'UPS Eliminada', detalles, 'DELETED', current_username(), "BORRADO_PERMANENTE", request.remote_addr))
                    conn.commit()
                    return jsonify({"status": "success"})
                    
            old_pc = comp["assigned_pc"]
            conn.execute("DELETE FROM components WHERE serial_number = %s", (serial,))
            
            if old_pc is not None and old_pc != "Unknown":
                detalles = f"{comp['component_type']} {comp['brand_model']} (S/N: {serial})"
                conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                             (old_pc, 'COMPONENT_DELETED', detalles, 'DELETED', current_username(), "BORRADO_PERMANENTE", request.remote_addr))
                
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

