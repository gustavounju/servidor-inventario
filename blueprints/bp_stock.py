import datetime
import random
from flask import Blueprint, jsonify, request, render_template
from database.db_core import get_db_connection

bp_stock = Blueprint('stock', __name__)

def generate_internal_serial(component_type):
    type_map = {
        'TECLADO': 'TEC',
        'MOUSE': 'MOU',
        'MONITOR': 'MON',
        'DISCO': 'DSK',
        'MEMORIA': 'RAM',
        'FUENTE': 'FNT',
        'GABINETE': 'GAB',
        'UPS': 'UPS',
        'IMPRESORA': 'IMP',
    }
    ctype_upper = (component_type or "OTR").strip().upper()
    code = type_map.get(ctype_upper, ctype_upper[:3])
    date_str = datetime.datetime.now().strftime("%Y%m%d")
    rand_seq = f"{random.randint(1000, 9999)}"
    return f"INT-{code}-{date_str}-{rand_seq}"

@bp_stock.route("/api/ad_users/search", methods=["GET"])
def search_ad_users():
    query = request.args.get("q", "").strip()
    try:
        with get_db_connection() as conn:
            if query:
                rows = conn.execute(
                    """
                    SELECT username, real_name, fuero, phone
                    FROM ad_users
                    WHERE LOWER(username) LIKE %s OR LOWER(real_name) LIKE %s OR LOWER(fuero) LIKE %s
                    ORDER BY real_name ASC LIMIT 30
                    """,
                    (f"%{query.lower()}%", f"%{query.lower()}%", f"%{query.lower()}%")
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT username, real_name, fuero, phone FROM ad_users ORDER BY real_name ASC LIMIT 30"
                ).fetchall()
        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

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
        data = request.json or {}
        serial = (data.get("serial_number") or "").strip()
        ctype = (data.get("component_type") or "").strip()
        model = (data.get("brand_model") or "").strip()
        supplier = (data.get("supplier_name") or data.get("supplier") or "").strip()
        invoice = (data.get("remito_number") or data.get("invoice_number") or "").strip()
        oc_num = (data.get("oc_number") or "").strip()
        assigned_user = (data.get("assigned_user") or "").strip()
        assigned_fuero = (data.get("assigned_fuero") or "").strip()
        quantity = int(data.get("quantity", 1))

        if not ctype:
            return jsonify({"status": "error", "message": "Falta indicar el tipo de componente"}), 400

        with get_db_connection() as conn:
            # Si se dio usuario pero no fuero, resolverlo desde AD
            if assigned_user and not assigned_fuero:
                ad_row = conn.execute(
                    "SELECT fuero FROM ad_users WHERE LOWER(username) = %s OR LOWER(real_name) = %s LIMIT 1",
                    (assigned_user.lower(), assigned_user.lower())
                ).fetchone()
                if ad_row and ad_row.get("fuero"):
                    assigned_fuero = ad_row["fuero"]

            status = 'Asignado' if (assigned_user or assigned_fuero) else 'Stock'
            added_serials = []

            for _ in range(max(1, quantity)):
                curr_serial = serial
                is_auto = 0
                if not curr_serial or quantity > 1:
                    curr_serial = generate_internal_serial(ctype)
                    is_auto = 1

                if ctype.upper() in ('UPS', 'EQUIPO UPS'):
                    conn.execute(
                        "INSERT INTO ups_inventory (code, model, supplier, invoice_number) VALUES (%s, %s, %s, %s)",
                        (curr_serial, model, supplier, invoice)
                    )
                else:
                    conn.execute(
                        """
                        INSERT INTO components (
                            serial_number, component_type, brand_model, status,
                            supplier, invoice_number, oc_number, assigned_user, assigned_fuero, is_autogenerated_id
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (curr_serial, ctype, model, status, supplier, invoice, oc_num, assigned_user or None, assigned_fuero or None, is_auto)
                    )
                added_serials.append(curr_serial)

            from utils.auth import current_technician_identity
            tech = current_technician_identity()
            if tech:
                from datetime import datetime
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                desc = f"Alta de Stock: {len(added_serials)}x {ctype} {model} (Remito: {invoice or 'N/A'}, Proveedor: {supplier or 'N/A'})"
                conn.execute(
                    "INSERT INTO tasks (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to, fuero) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    ('Stock (Ingreso)', desc, tech, 'Hecha', now_str, tech, now_str, 'Hardware', tech, assigned_fuero or None)
                )
            conn.commit()
        return jsonify({"status": "success", "serials": added_serials})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_stock.route("/api/components/assign", methods=["POST"])
def assign_component():
    try:
        data = request.json or {}
        serial = (data.get("serial_number") or "").strip()
        pc_name = (data.get("pc_name") or "").strip()
        assigned_user = (data.get("assigned_user") or "").strip()
        assigned_fuero = (data.get("assigned_fuero") or "").strip()

        if not serial:
            return jsonify({"status": "error", "message": "Falta serial del componente"}), 400

        with get_db_connection() as conn:
            # Resolver fuero de AD si hay usuario y no fuero
            if assigned_user and not assigned_fuero:
                ad_row = conn.execute(
                    "SELECT fuero FROM ad_users WHERE LOWER(username) = %s OR LOWER(real_name) = %s LIMIT 1",
                    (assigned_user.lower(), assigned_user.lower())
                ).fetchone()
                if ad_row and ad_row.get("fuero"):
                    assigned_fuero = ad_row["fuero"]

            comp = conn.execute("SELECT * FROM components WHERE serial_number = %s", (serial,)).fetchone()
            if not comp:
                ups = conn.execute("SELECT * FROM ups_inventory WHERE code = %s", (serial,)).fetchone()
                if not ups:
                    return jsonify({"status": "error", "message": "Componente no existe"}), 404
                else:
                    conn.execute("UPDATE ups_inventory SET assigned_pc = %s WHERE code = %s", (pc_name or None, serial))
                    detalles = f"UPS {ups['model']} (S/N: {serial})"
                    from utils.auth import current_username, current_technician_identity
                    tech = current_technician_identity()
                    target_dest = pc_name or assigned_user or assigned_fuero or "Desconocido"
                    conn.execute(
                        "INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (target_dest, 'UPS Asignada', 'Stock', detalles, current_username() or tech, "GESTION_STOCK", request.remote_addr)
                    )
                    conn.commit()
                    return jsonify({"status": "success", "resolved_fuero": assigned_fuero})

            new_status = 'Installed' if pc_name else 'Asignado'
            conn.execute(
                """
                UPDATE components
                SET status = %s, assigned_pc = %s, assigned_user = %s, assigned_fuero = %s
                WHERE serial_number = %s
                """,
                (new_status, pc_name or None, assigned_user or None, assigned_fuero or None, serial)
            )

            detalles = f"{comp['component_type']} {comp['brand_model']} (S/N: {serial}) -> Usuario: {assigned_user or 'N/A'}, Fuero: {assigned_fuero or 'N/A'}, PC: {pc_name or 'N/A'}"
            from utils.auth import current_username, current_technician_identity
            tech = current_technician_identity()
            target_dest = pc_name or assigned_user or assigned_fuero or "Desconocido"
            conn.execute(
                "INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (target_dest, 'COMPONENT_ASSIGN', comp.get('status') or 'Stock', detalles, current_username() or tech, "GESTION_STOCK", request.remote_addr)
            )

            if tech:
                from datetime import datetime
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                desc = f"Asignó componente ({comp['component_type']} {comp['brand_model']}) a {assigned_user or pc_name or 'Fuero'} ({assigned_fuero or ''})"
                conn.execute(
                    "INSERT INTO tasks (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to, fuero) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (pc_name or target_dest, desc, tech, 'Hecha', now_str, tech, now_str, 'Hardware', tech, assigned_fuero or None)
                )

            conn.commit()

        return jsonify({"status": "success", "resolved_fuero": assigned_fuero})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
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

