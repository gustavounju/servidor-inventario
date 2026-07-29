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
    query = request.args.get("q", "").strip().lower()
    try:
        with get_db_connection() as conn:
            sql = """
                SELECT 
                    u.username,
                    COALESCE(NULLIF(TRIM(u.real_name), ''), u.username) AS real_name,
                    COALESCE(
                        NULLIF(NULLIF(NULLIF(TRIM(u.fuero), ''), 'Sin Fuero'), 'Desconocido'),
                        NULLIF(NULLIF(NULLIF(TRIM(p.fuero), ''), 'Sin Fuero'), 'Desconocido'),
                        'Sin Fuero'
                    ) AS fuero,
                    u.phone
                FROM ad_users u
                LEFT JOIN (
                    SELECT DISTINCT LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) as clean_user, fuero 
                    FROM pcs 
                    WHERE last_user IS NOT NULL AND last_user != '' AND fuero IS NOT NULL AND fuero != '' AND fuero != 'Desconocido' AND fuero != 'Sin Fuero'
                ) p ON LOWER(u.username) = p.clean_user
            """
            if query:
                sql += " WHERE LOWER(u.username) LIKE %s OR LOWER(u.real_name) LIKE %s OR LOWER(u.fuero) LIKE %s OR LOWER(p.fuero) LIKE %s"
                sql += " ORDER BY u.real_name ASC LIMIT 30"
                rows = conn.execute(sql, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%")).fetchall()
            else:
                sql += " ORDER BY u.real_name ASC LIMIT 30"
                rows = conn.execute(sql).fetchall()

        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _ensure_stock_catalog_seeded(conn):
    try:
        cnt_row = conn.execute("SELECT COUNT(*) as cnt FROM stock_catalogs").fetchone()
        if not cnt_row or cnt_row['cnt'] == 0:
            defaults = [
                ('supplier', 'NOVA'), ('supplier', 'BGH'), ('supplier', 'Banghó'),
                ('supplier', 'EXO'), ('supplier', 'HP'), ('supplier', 'Dell'),
                ('supplier', 'Lenovo'), ('supplier', 'Kelyx'),
                ('type', 'Monitor'), ('type', 'Teclado'), ('type', 'Mouse'),
                ('type', 'CPU'), ('type', 'UPS'), ('type', 'Impresora'),
                ('type', 'Disco'), ('type', 'Memoria'), ('type', 'Fuente'),
                ('type', 'Gabinete'), ('type', 'Otro')
            ]
            for cat, val in defaults:
                conn.execute("INSERT IGNORE INTO stock_catalogs (category, item_value) VALUES (%s, %s)", (cat, val))

            conn.execute("""
                INSERT IGNORE INTO stock_catalogs (category, item_value)
                SELECT 'supplier', supplier FROM components WHERE supplier IS NOT NULL AND TRIM(supplier) != ''
            """)
            conn.execute("""
                INSERT IGNORE INTO stock_catalogs (category, item_value)
                SELECT 'model', brand_model FROM components WHERE brand_model IS NOT NULL AND TRIM(brand_model) != ''
            """)
            conn.execute("""
                INSERT IGNORE INTO stock_catalogs (category, item_value)
                SELECT 'type', component_type FROM components WHERE component_type IS NOT NULL AND TRIM(component_type) != ''
            """)
    except Exception as e:
        pass


@bp_stock.route("/api/stock/catalog", methods=["GET"])
def get_stock_catalog():
    try:
        with get_db_connection() as conn:
            _ensure_stock_catalog_seeded(conn)

            cat_rows = conn.execute("SELECT category, item_value FROM stock_catalogs ORDER BY item_value ASC").fetchall()
            cat_suppliers = [r['item_value'] for r in cat_rows if r['category'] == 'supplier']
            cat_models = [r['item_value'] for r in cat_rows if r['category'] == 'model']
            cat_types = [r['item_value'] for r in cat_rows if r['category'] == 'type']

            comp_suppliers = [r['supplier'] for r in conn.execute(
                "SELECT DISTINCT supplier FROM components WHERE supplier IS NOT NULL AND TRIM(supplier) != ''"
            ).fetchall() if r.get('supplier')]

            comp_models = [r['brand_model'] for r in conn.execute(
                "SELECT DISTINCT brand_model FROM components WHERE brand_model IS NOT NULL AND TRIM(brand_model) != ''"
            ).fetchall() if r.get('brand_model')]

            comp_types = [r['component_type'] for r in conn.execute(
                "SELECT DISTINCT component_type FROM components WHERE component_type IS NOT NULL AND TRIM(component_type) != ''"
            ).fetchall() if r.get('component_type')]

            suppliers = sorted(list(set(cat_suppliers + comp_suppliers)))
            models = sorted(list(set(cat_models + comp_models)))
            types = sorted(list(set(cat_types + comp_types)))

        return jsonify({
            "status": "success",
            "suppliers": suppliers,
            "models": models,
            "types": types,
            "custom_catalog": [dict(r) for r in cat_rows]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp_stock.route("/api/stock/catalog/details", methods=["GET"])
def get_stock_catalog_details():
    category = request.args.get("category", "").strip().lower()
    if category not in ['supplier', 'model', 'type']:
        return jsonify({"status": "error", "message": "Categoría no válida"}), 400

    comp_column = 'supplier' if category == 'supplier' else 'brand_model' if category == 'model' else 'component_type'

    try:
        with get_db_connection() as conn:
            _ensure_stock_catalog_seeded(conn)

            cat_rows = conn.execute("SELECT item_value FROM stock_catalogs WHERE category = %s ORDER BY item_value ASC", (category,)).fetchall()
            cat_items = [r['item_value'] for r in cat_rows]

            comp_rows = conn.execute(f"SELECT DISTINCT {comp_column} FROM components WHERE {comp_column} IS NOT NULL AND TRIM({comp_column}) != ''").fetchall()
            comp_items = [r[comp_column] for r in comp_rows if r.get(comp_column)]

            all_unique_values = sorted(list(set(cat_items + comp_items)))

            result = []
            for val in all_unique_values:
                count_row = conn.execute(f"SELECT COUNT(*) as cnt FROM components WHERE {comp_column} = %s", (val,)).fetchone()
                usage_cnt = count_row['cnt'] if count_row else 0
                result.append({
                    "value": val,
                    "usage_count": usage_cnt
                })

        return jsonify({
            "status": "success",
            "category": category,
            "items": result
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp_stock.route("/api/stock/catalog/add", methods=["POST"])
def add_stock_catalog_item():
    data = request.json or {}
    category = data.get("category", "").strip().lower()
    value = data.get("value", "").strip()
    if not category or not value:
        return jsonify({"status": "error", "message": "Categoría y valor requeridos"}), 400
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO stock_catalogs (category, item_value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE item_value = VALUES(item_value)",
                (category, value)
            )
        return jsonify({"status": "success", "message": f"'{value}' añadido al catálogo."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp_stock.route("/api/stock/catalog/update", methods=["POST"])
def update_stock_catalog_item():
    data = request.json or {}
    category = data.get("category", "").strip().lower()
    old_value = data.get("old_value", "").strip()
    new_value = data.get("new_value", "").strip()

    if not category or not old_value or not new_value:
        return jsonify({"status": "error", "message": "Datos incompletos"}), 400

    comp_column = 'supplier' if category == 'supplier' else 'brand_model' if category == 'model' else 'component_type'

    try:
        with get_db_connection() as conn:
            conn.execute("UPDATE stock_catalogs SET item_value = %s WHERE category = %s AND item_value = %s", (new_value, category, old_value))
            conn.execute("INSERT INTO stock_catalogs (category, item_value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE item_value = VALUES(item_value)", (category, new_value))
            conn.execute(f"UPDATE components SET {comp_column} = %s WHERE {comp_column} = %s", (new_value, old_value))

        return jsonify({"status": "success", "message": f"'{old_value}' fue renombrado a '{new_value}'."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp_stock.route("/api/stock/catalog/delete", methods=["POST"])
def delete_stock_catalog_item():
    data = request.json or {}
    category = data.get("category", "").strip().lower()
    value = data.get("value", "").strip()
    if not category or not value:
        return jsonify({"status": "error", "message": "Datos incompletos"}), 400

    comp_column = 'supplier' if category == 'supplier' else 'brand_model' if category == 'model' else 'component_type'

    try:
        with get_db_connection() as conn:
            count_row = conn.execute(f"SELECT COUNT(*) as cnt FROM components WHERE {comp_column} = %s", (value,)).fetchone()
            usage_cnt = count_row['cnt'] if count_row else 0

            if usage_cnt > 0:
                return jsonify({
                    "status": "error",
                    "message": f"No se puede eliminar '{value}' porque está en uso por {usage_cnt} componente(s) en inventario."
                }), 400

            conn.execute("DELETE FROM stock_catalogs WHERE category = %s AND item_value = %s", (category, value))

        return jsonify({"status": "success", "message": f"'{value}' eliminado del catálogo."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

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
        from utils.auth import current_user, has_permission
        user = current_user()
        if not (user.get("is_superuser") or user.get("role") in ["administrador", "funcionario"] or has_permission("funcionario") or has_permission("can_manage_stock")):
            return jsonify({"status": "error", "message": "Acceso denegado: Solo los usuarios con el permiso 'Gestión Stock' pueden cargar nuevos remitos."}), 403

        data = request.json or {}
        single_serial = (data.get("serial_number") or "").strip()
        serials_input = data.get("serials") or data.get("serial_numbers") or []

        if isinstance(serials_input, str):
            serials_input = [s.strip() for s in serials_input.replace(',', '\n').split('\n') if s.strip()]
        elif not isinstance(serials_input, list):
            serials_input = []

        if not serials_input and single_serial:
            serials_input = [single_serial]

        ctype = (data.get("component_type") or "").strip()
        model = (data.get("brand_model") or "").strip()
        supplier = (data.get("supplier_name") or data.get("supplier") or "").strip()
        invoice = (data.get("remito_number") or data.get("invoice_number") or "").strip()
        oc_num = (data.get("oc_number") or "").strip()
        assigned_user = (data.get("assigned_user") or "").strip()
        assigned_fuero = (data.get("assigned_fuero") or "").strip()
        quantity = max(1, int(data.get("quantity", 1)))

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

            # Filtrar y validar códigos de serie recibidos (limitado a la cantidad indicada)
            provided_serials = [s.strip() for s in serials_input[:quantity] if s and s.strip()]

            # Verificar duplicados dentro del mismo envío
            if len(provided_serials) != len(set(provided_serials)):
                return jsonify({"status": "error", "message": "Existen códigos de barras / N° de serie duplicados en la lista ingresada."}), 400

            # Verificar duplicados contra la base de datos
            for s in provided_serials:
                existing = conn.execute("SELECT id FROM components WHERE serial_number = %s", (s,)).fetchone()
                if existing:
                    return jsonify({"status": "error", "message": f"El código de barras / N° de Serie '{s}' ya existe registrado en la base de datos."}), 400

            for i in range(quantity):
                curr_serial = provided_serials[i] if i < len(provided_serials) else ""
                is_auto = 0
                if not curr_serial:
                    while True:
                        curr_serial = generate_internal_serial(ctype)
                        chk = conn.execute("SELECT id FROM components WHERE serial_number = %s", (curr_serial,)).fetchone()
                        if not chk and curr_serial not in added_serials:
                            break
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
                    (None, desc, tech, 'Hecha', now_str, tech, now_str, 'Hardware', tech, assigned_fuero or None)
                )
            conn.commit()
        return jsonify({"status": "success", "serials": added_serials})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_stock.route("/api/components/retire", methods=["POST"])
def retire_component():
    try:
        data = request.json or {}
        serial = data.get("serial_number")
        reason = (data.get("reason") or "Baja / Retirado de servicio").strip()
        if not serial: return jsonify({"status": "error", "message": "Falta serial"}), 400
            
        with get_db_connection() as conn:
            comp = conn.execute("SELECT * FROM components WHERE serial_number = %s", (serial,)).fetchone()
            if not comp: 
                ups = conn.execute("SELECT * FROM ups_inventory WHERE code = %s", (serial,)).fetchone()
                if not ups:
                    return jsonify({"status": "error", "message": "Componente no existe"}), 404
                else:
                    old_pc = ups["assigned_pc"]
                    conn.execute("UPDATE ups_inventory SET assigned_pc = NULL WHERE code = %s", (serial,))
                    from utils.auth import current_username, current_technician_identity
                    tech = current_technician_identity()
                    detalles = f"UPS {ups['model']} (S/N: {serial}) -> Motivo: {reason}"
                    conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                                 (old_pc or 'Stock', 'UPS Retirada', detalles, 'Retirado', current_username() or tech, "BAJA_COMPONENTE", request.remote_addr))
                    conn.commit()
                    return jsonify({"status": "success"})
                    
            old_status = comp.get("status") or "Stock"
            old_pc = comp.get("assigned_pc")
            conn.execute(
                "UPDATE components SET status = 'Retirado', assigned_pc = NULL, assigned_user = NULL, assigned_fuero = NULL WHERE serial_number = %s",
                (serial,)
            )
            from utils.auth import current_username, current_technician_identity
            tech = current_technician_identity()
            detalles = f"{comp['component_type']} {comp['brand_model']} (S/N: {serial}) -> Motivo: {reason}"
            conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                         (old_pc or 'Stock', 'COMPONENT_RETIRED', old_status, detalles, current_username() or tech, "BAJA_COMPONENTE", request.remote_addr))
            
            if tech:
                from datetime import datetime
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                desc = f"Baja / Retiro de servicio: {comp['component_type']} {comp['brand_model']} (S/N: {serial})"
                valid_task_pc = None
                if old_pc and old_pc != "Unknown":
                    chk_pc = conn.execute("SELECT pc_name FROM pcs WHERE pc_name = %s", (old_pc,)).fetchone()
                    if chk_pc: valid_task_pc = chk_pc['pc_name']
                conn.execute(
                    "INSERT INTO tasks (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (valid_task_pc, desc, tech, 'Hecha', now_str, tech, now_str, 'Hardware', tech)
                )

            conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_stock.route("/api/components/retire_bulk", methods=["POST"])
def retire_components_bulk():
    try:
        data = request.json or {}
        serials = data.get("serials", [])
        reason = (data.get("reason") or "Baja en bloque / Retirado de servicio").strip()
        if not serials or not isinstance(serials, list):
            return jsonify({"status": "error", "message": "Seleccione al menos un componente para dar de baja."}), 400

        from utils.auth import current_username, current_technician_identity
        tech = current_technician_identity()
        retired_count = 0

        with get_db_connection() as conn:
            for serial in serials:
                comp = conn.execute("SELECT * FROM components WHERE serial_number = %s", (serial,)).fetchone()
                if comp:
                    old_status = comp.get("status") or "Stock"
                    old_pc = comp.get("assigned_pc")
                    conn.execute(
                        "UPDATE components SET status = 'Retirado', assigned_pc = NULL, assigned_user = NULL, assigned_fuero = NULL WHERE serial_number = %s",
                        (serial,)
                    )
                    retired_count += 1
                    detalles = f"{comp['component_type']} {comp['brand_model']} (S/N: {serial}) -> Motivo: {reason}"
                    conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                                 (old_pc or 'Stock', 'COMPONENT_RETIRED', old_status, detalles, current_username() or tech, "BAJA_COMPONENTE", request.remote_addr))
            
            if tech and retired_count > 0:
                from datetime import datetime
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                desc = f"Baja de componentes en bloque: {retired_count} ítem(s) retirados"
                conn.execute(
                    "INSERT INTO tasks (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (None, desc, tech, 'Hecha', now_str, tech, now_str, 'Hardware', tech)
                )

            conn.commit()
        return jsonify({"status": "success", "count": retired_count})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_stock.route("/api/components/restore_stock", methods=["POST"])
def restore_component():
    try:
        data = request.json or {}
        serial = data.get("serial_number")
        if not serial: return jsonify({"status": "error", "message": "Falta serial"}), 400

        with get_db_connection() as conn:
            comp = conn.execute("SELECT * FROM components WHERE serial_number = %s", (serial,)).fetchone()
            if not comp:
                return jsonify({"status": "error", "message": "Componente no existe"}), 404

            conn.execute(
                "UPDATE components SET status = 'Stock', assigned_pc = NULL, assigned_user = NULL, assigned_fuero = NULL WHERE serial_number = %s",
                (serial,)
            )

            from utils.auth import current_username, current_technician_identity
            tech = current_technician_identity()
            detalles = f"{comp['component_type']} {comp['brand_model']} (S/N: {serial}) -> Reactivado a Stock"
            conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                         ('Stock', 'COMPONENT_RESTORED', 'Retirado', detalles, current_username() or tech, "REACTIVACION_STOCK", request.remote_addr))

            conn.commit()
        return jsonify({"status": "success"})
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
                valid_task_pc = None
                if pc_name:
                    chk_pc = conn.execute("SELECT pc_name FROM pcs WHERE pc_name = %s", (pc_name,)).fetchone()
                    if chk_pc: valid_task_pc = chk_pc['pc_name']
                conn.execute(
                    "INSERT INTO tasks (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to, fuero) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (valid_task_pc, desc, tech, 'Hecha', now_str, tech, now_str, 'Hardware', tech, assigned_fuero or None)
                )

            conn.commit()

        return jsonify({"status": "success", "resolved_fuero": assigned_fuero})
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
                        valid_task_pc = None
                        if old_pc and old_pc != "Unknown":
                            chk_pc = conn.execute("SELECT pc_name FROM pcs WHERE pc_name = %s", (old_pc,)).fetchone()
                            if chk_pc: valid_task_pc = chk_pc['pc_name']
                        conn.execute(
                            "INSERT INTO tasks (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (valid_task_pc, desc, tech, 'Hecha', now_str, tech, now_str, 'Hardware', tech)
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
                valid_task_pc = None
                if old_pc and old_pc != "Unknown":
                    chk_pc = conn.execute("SELECT pc_name FROM pcs WHERE pc_name = %s", (old_pc,)).fetchone()
                    if chk_pc: valid_task_pc = chk_pc['pc_name']
                conn.execute(
                    "INSERT INTO tasks (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (valid_task_pc, desc, tech, 'Hecha', now_str, tech, now_str, 'Hardware', tech)
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


@bp_stock.route("/api/components/delete_bulk", methods=["POST"])
def delete_components_bulk():
    try:
        data = request.json or {}
        serials = data.get("serials", [])
        if not serials or not isinstance(serials, list):
            return jsonify({"status": "error", "message": "Seleccione al menos un componente para eliminar."}), 400

        from utils.auth import current_username
        deleted_count = 0
        with get_db_connection() as conn:
            for serial in serials:
                comp = conn.execute("SELECT * FROM components WHERE serial_number = %s", (serial,)).fetchone()
                if comp:
                    old_pc = comp["assigned_pc"]
                    conn.execute("DELETE FROM components WHERE serial_number = %s", (serial,))
                    deleted_count += 1
                    if old_pc is not None and old_pc != "Unknown":
                        detalles = f"{comp['component_type']} {comp['brand_model']} (S/N: {serial})"
                        conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                                     (old_pc, 'COMPONENT_DELETED', detalles, 'DELETED', current_username(), "BORRADO_PERMANENTE", request.remote_addr))
                else:
                    ups = conn.execute("SELECT * FROM ups_inventory WHERE code = %s", (serial,)).fetchone()
                    if ups:
                        if ups.get('assigned_battery_id'):
                            conn.execute("UPDATE components SET status = 'Stock' WHERE id = %s", (ups['assigned_battery_id'],))
                        conn.execute("DELETE FROM ups_inventory WHERE code = %s", (serial,))
                        deleted_count += 1

        return jsonify({"status": "success", "message": f"{deleted_count} componente(s) eliminado(s) correctamente."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# DB-backed Mobile Scan Session Storage (Gunicorn multi-worker compatible)
@bp_stock.route("/api/scan_session/create", methods=["POST"])
def create_scan_session():
    try:
        import random, json
        session_id = "".join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789", k=6))
        with get_db_connection() as conn:
            try:
                conn.execute("DELETE FROM scan_sessions WHERE created_at < NOW() - INTERVAL 1 HOUR")
            except Exception:
                pass
            conn.execute(
                "INSERT INTO scan_sessions (session_id, created_at, status, barcodes) VALUES (%s, NOW(), 'active', %s)",
                (session_id, json.dumps([]))
            )
            conn.commit()

        server_host = request.host
        mobile_url = f"http://{server_host}/mobile/live_scan?session={session_id}"
        return jsonify({
            "status": "success",
            "session_id": session_id,
            "mobile_url": mobile_url
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_stock.route("/api/scan_session/close", methods=["POST"])
def close_scan_session():
    try:
        data = request.json or {}
        session_id = (data.get("session_id") or "").strip().upper()
        if session_id:
            with get_db_connection() as conn:
                conn.execute("UPDATE scan_sessions SET status = 'closed' WHERE session_id = %s", (session_id,))
                conn.commit()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_stock.route("/api/scan_session/status/<session_id>", methods=["GET"])
def check_scan_session_status(session_id):
    try:
        session_id = session_id.strip().upper()
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT status FROM scan_sessions WHERE session_id = %s AND created_at >= NOW() - INTERVAL 1 HOUR",
                (session_id,)
            ).fetchone()
            if not row or row.get("status") == 'closed':
                return jsonify({"status": "closed"})
            return jsonify({"status": "active"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_stock.route("/api/scan_session/push", methods=["POST"])
def push_scan_session_barcode():
    try:
        import json
        data = request.json or {}
        session_id = (data.get("session_id") or "").strip().upper()
        barcode = (data.get("barcode") or "").strip()

        if not session_id:
            return jsonify({"status": "error", "message": "Sesión no especificada."}), 400

        if not barcode:
            return jsonify({"status": "error", "message": "Código vacío."}), 400

        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT barcodes, status FROM scan_sessions WHERE session_id = %s AND created_at >= NOW() - INTERVAL 1 HOUR",
                (session_id,)
            ).fetchone()

            if not row or row.get("status") == 'closed':
                return jsonify({"status": "closed", "message": "La sesión fue finalizada desde la PC."}), 404

            barcodes = json.loads(row["barcodes"] or "[]")
            barcodes.append(barcode)
            conn.execute(
                "UPDATE scan_sessions SET barcodes = %s WHERE session_id = %s",
                (json.dumps(barcodes), session_id)
            )
            conn.commit()

            return jsonify({
                "status": "success",
                "barcode": barcode,
                "total": len(barcodes)
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_stock.route("/api/scan_session/poll/<session_id>", methods=["GET"])
def poll_scan_session(session_id):
    try:
        import json
        session_id = session_id.strip().upper()
        with get_db_connection() as conn:
            row = conn.execute(
                "SELECT barcodes, status FROM scan_sessions WHERE session_id = %s AND created_at >= NOW() - INTERVAL 1 HOUR",
                (session_id,)
            ).fetchone()

            if not row or row.get("status") == 'closed':
                return jsonify({"status": "expired", "barcodes": []})

            all_barcodes = json.loads(row["barcodes"] or "[]")
            last_index = int(request.args.get("last_index", 0))
            new_barcodes = all_barcodes[last_index:]
            return jsonify({
                "status": "active",
                "new_barcodes": new_barcodes,
                "total": len(all_barcodes)
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

