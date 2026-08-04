import datetime
import logging
import random
from flask import Blueprint, jsonify, request, render_template
from database.db_core import get_db_connection

bp_stock = Blueprint('stock', __name__)

def check_stock_permission():
    from utils.auth import current_user, has_permission
    user = current_user()
    if not user:
        return False
    return (
        bool(user.get("is_superuser"))
        or (user.get("role") or "").strip().lower() in ["administrador", "funcionario"]
        or has_permission("can_manage_stock", user)
        or has_permission("manage_stock", user)
        or has_permission("funcionario", user)
    )

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
                        NULLIF(NULLIF(NULLIF(TRIM(t.fuero), ''), 'Sin Fuero'), 'Desconocido'),
                        'Sin Fuero'
                    ) AS fuero,
                    u.phone
                FROM ad_users u
                LEFT JOIN (
                    SELECT DISTINCT LOWER(SUBSTRING_INDEX(last_user, '\\\\', -1)) as clean_user, fuero 
                    FROM pcs 
                    WHERE last_user IS NOT NULL AND last_user != '' AND fuero IS NOT NULL AND fuero != '' AND fuero != 'Desconocido' AND fuero != 'Sin Fuero'
                ) p ON (LOWER(u.username) = p.clean_user OR LOWER(u.real_name) LIKE CONCAT('%%', p.clean_user, '%%'))
                LEFT JOIN (
                    SELECT DISTINCT LOWER(SUBSTRING_INDEX(solicitante, '\\\\', -1)) as clean_sol, fuero
                    FROM tasks
                    WHERE solicitante IS NOT NULL AND solicitante != '' AND fuero IS NOT NULL AND fuero != '' AND fuero != 'Desconocido' AND fuero != 'Sin Fuero'
                ) t ON (LOWER(u.username) = t.clean_sol OR LOWER(u.real_name) LIKE CONCAT('%%', t.clean_sol, '%%'))
            """
            if query:
                sql += " WHERE LOWER(u.username) LIKE %s OR LOWER(u.real_name) LIKE %s OR LOWER(u.fuero) LIKE %s OR LOWER(p.fuero) LIKE %s OR LOWER(t.fuero) LIKE %s"
                sql += " ORDER BY u.real_name ASC LIMIT 30"
                rows = conn.execute(sql, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%")).fetchall()
            else:
                sql += " ORDER BY u.real_name ASC LIMIT 30"
                rows = conn.execute(sql).fetchall()

        return jsonify([dict(r) for r in rows])
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _ensure_stock_catalog_seeded(conn):
    try:
        defaults = [
            ('supplier', 'NOVA'), ('supplier', 'BGH'), ('supplier', 'Banghó'),
            ('supplier', 'EXO'), ('supplier', 'HP'), ('supplier', 'Dell'),
            ('supplier', 'Lenovo'), ('supplier', 'Kelyx'),
            ('type', 'Monitor'), ('type', 'Teclado'), ('type', 'Mouse'),
            ('type', 'CPU'), ('type', 'Procesador'), ('type', 'Motherboard'),
            ('type', 'UPS'), ('type', 'Impresora'),
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
        logging.warning("Error al inicializar el catálogo de stock: %s", e)


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


@bp_stock.route("/api/components/<path:serial_number>/patrimony", methods=["PATCH"])
def update_component_patrimony(serial_number):
    """
    PATCH /api/components/<serial>/patrimony

    Actualiza los campos patrimoniales de un activo (Fase 3).
    Solo acepta los campos patrimoniales nuevos; no toca status ni assigned_*.

    Campos editables:
      lifecycle_status : stock | en_armado | desplegado | en_reparacion | retirado | scrap
      purchase_date    : DATE (YYYY-MM-DD) — fecha de compra
      warranty_until   : DATE (YYYY-MM-DD) — vencimiento de garantia
      asset_notes      : Texto libre con observaciones del tecnico
      build_order_id   : INT — ID de la Build Order asociada (opcional)
    """
    if not check_stock_permission():
        return jsonify({"status": "error", "message": "Acceso denegado."}), 403

    try:
        from utils.auth import current_username, current_technician_identity
        tech = current_technician_identity() or current_username()
        data = request.json or {}

        VALID_LIFECYCLE = {"stock", "en_armado", "desplegado", "en_reparacion", "retirado", "scrap"}

        updates = {}
        if "lifecycle_status" in data:
            ls = (data["lifecycle_status"] or "").strip().lower()
            if ls not in VALID_LIFECYCLE:
                return jsonify({
                    "status": "error",
                    "message": f"lifecycle_status inválido. Valores: {', '.join(sorted(VALID_LIFECYCLE))}"
                }), 400
            updates["lifecycle_status"] = ls

        if "purchase_date" in data:
            pd_val = data["purchase_date"]
            updates["purchase_date"] = pd_val if pd_val else None

        if "warranty_until" in data:
            wu_val = data["warranty_until"]
            updates["warranty_until"] = wu_val if wu_val else None

        if "asset_notes" in data:
            updates["asset_notes"] = (data["asset_notes"] or "").strip() or None

        if "build_order_id" in data:
            bo_id = data["build_order_id"]
            updates["build_order_id"] = int(bo_id) if bo_id else None

        if not updates:
            return jsonify({"status": "error", "message": "No se enviaron campos a actualizar."}), 400

        set_clauses = ", ".join(f"{col} = %s" for col in updates)
        values = list(updates.values()) + [serial_number]

        with get_db_connection() as conn:
            comp = conn.execute(
                "SELECT id, component_type, brand_model FROM components WHERE serial_number = %s",
                (serial_number,)
            ).fetchone()
            if not comp:
                return jsonify({"status": "error", "message": "Componente no encontrado."}), 404

            conn.execute(
                f"UPDATE components SET {set_clauses} WHERE serial_number = %s",
                values
            )

            # Registrar en audit_logs
            changes_str = ", ".join(f"{k}={v}" for k, v in updates.items())
            conn.execute(
                """
                INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    serial_number,
                    "PATRIMONY_UPDATE",
                    comp.get("component_type", ""),
                    changes_str,
                    tech, "GESTION_STOCK", request.remote_addr
                )
            )

        return jsonify({"status": "success", "serial_number": serial_number, "updated": updates})
    except Exception as e:
        logging.error("Error en update_component_patrimony(%s): %s", serial_number, e)
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_stock.route("/stock")
def stock_view():
    try:
        with get_db_connection() as conn:
            pcs_rows = conn.execute(
                "SELECT pc_name, last_user, fuero FROM pcs WHERE is_active = 1 ORDER BY pc_name ASC"
            ).fetchall()
            pcs = [dict(r) for r in pcs_rows]

            ad_rows = conn.execute(
                """
                SELECT username, COALESCE(NULLIF(TRIM(real_name), ''), username) as real_name, fuero
                FROM ad_users
                ORDER BY real_name ASC
                """
            ).fetchall()
            ad_users = [dict(r) for r in ad_rows]

            stock_comps_rows = conn.execute(
                """
                SELECT serial_number, component_type, brand_model, supplier, is_autogenerated_id
                FROM components
                WHERE (status = 'Stock' OR status IS NULL)
                  AND (assigned_pc IS NULL OR assigned_pc = '')
                  AND (assigned_user IS NULL OR assigned_user = '')
                ORDER BY component_type ASC, brand_model ASC
                """
            ).fetchall()
            stock_components = []
            for r in stock_comps_rows:
                item = dict(r)
                sn = item.get('serial_number') or ''
                if item.get('is_autogenerated_id') or sn.upper().startswith('INT-'):
                    item['is_autogenerated_id'] = 1
                else:
                    item['is_autogenerated_id'] = 0
                stock_components.append(item)

            try:
                net_printers_rows = conn.execute(
                    """
                    SELECT serial_number, ip_address, brand_model, fuero
                    FROM network_printers
                    WHERE serial_number IS NOT NULL AND TRIM(serial_number) != ''
                    """
                ).fetchall()
                existing_serials = {c["serial_number"] for c in stock_components if c.get("serial_number")}
                for np in net_printers_rows:
                    sn = np["serial_number"].strip()
                    if sn and sn not in existing_serials:
                        stock_components.append({
                            "serial_number": sn,
                            "component_type": "Impresora (Red)",
                            "brand_model": f"{np.get('brand_model') or 'Impresora'} [IP: {np.get('ip_address') or 'N/A'}]",
                            "supplier": np.get("fuero") or "Infraestructura",
                            "is_autogenerated_id": 0
                        })
            except Exception:
                pass
            try:
                fueros_rows = conn.execute(
                    """
                    SELECT DISTINCT fuero_label as fuero FROM fuero_mappings WHERE is_active = 1
                    UNION
                    SELECT DISTINCT fuero FROM pcs WHERE fuero IS NOT NULL AND fuero != '' AND fuero != 'Desconocido' AND fuero != 'Sin Fuero'
                    ORDER BY fuero ASC
                    """
                ).fetchall()
                fueros = [r['fuero'] for r in fueros_rows if r.get('fuero')]
            except Exception:
                fueros = []
    except Exception:
        pcs = []
        ad_users = []
        stock_components = []
        fueros = []

    return render_template("stock.html", pcs=pcs, ad_users=ad_users, stock_components=stock_components, stock_fueros=fueros)


@bp_stock.route("/build_orders")
def build_orders_view():
    """Vista de gestión de Órdenes de Armado (Build Orders) — Fase 5."""
    try:
        with get_db_connection() as conn:
            # Lista de PCs activas
            pcs_rows = conn.execute(
                "SELECT pc_name, last_user, fuero FROM pcs WHERE is_active = 1 ORDER BY pc_name ASC"
            ).fetchall()
            pcs = [dict(r) for r in pcs_rows]

            # Usuarios de AD
            ad_rows = conn.execute(
                """
                SELECT username, COALESCE(NULLIF(TRIM(real_name), ''), username) as real_name, fuero
                FROM ad_users
                ORDER BY real_name ASC
                """
            ).fetchall()
            ad_users = [dict(r) for r in ad_rows]

            # Componentes en stock disponibles para agregar
            stock_comps_rows = conn.execute(
                """
                SELECT serial_number, component_type, brand_model, supplier, lifecycle_status
                FROM components
                WHERE (status = 'Stock' OR status IS NULL OR lifecycle_status = 'stock')
                  AND (assigned_pc IS NULL OR assigned_pc = '')
                  AND (assigned_user IS NULL OR assigned_user = '')
                ORDER BY component_type ASC, brand_model ASC
                """
            ).fetchall()
            stock_components = [dict(r) for r in stock_comps_rows]

            # Órdenes de Armado existentes con sus ítems
            bo_rows = conn.execute(
                """
                SELECT bo.id, bo.code, bo.status, bo.oc_number, bo.invoice_number,
                       bo.target_fuero, bo.target_user, bo.target_pc_name, bo.notes,
                       bo.created_by, bo.completed_at, bo.created_at
                FROM build_orders bo
                ORDER BY bo.created_at DESC
                """
            ).fetchall()
            
            build_orders_list = []
            for bo in bo_rows:
                item_dict = dict(bo)
                if item_dict.get("created_at") and hasattr(item_dict["created_at"], "strftime"):
                    item_dict["created_at"] = item_dict["created_at"].strftime("%Y-%m-%d %H:%M")
                if item_dict.get("completed_at") and hasattr(item_dict["completed_at"], "strftime"):
                    item_dict["completed_at"] = item_dict["completed_at"].strftime("%Y-%m-%d %H:%M")

                # Obtener ítems de esta BO
                items_rows = conn.execute(
                    """
                    SELECT id, serial_number, asset_type, brand_model, pc_name, scanned_at, scanned_by
                    FROM build_order_items
                    WHERE build_order_id = %s
                    ORDER BY scanned_at ASC
                    """,
                    (bo["id"],)
                ).fetchall()
                items_list = [dict(i) for i in items_rows]
                item_dict["items"] = items_list
                item_dict["order_items"] = items_list
                build_orders_list.append(item_dict)

            # Fueros
            fueros_rows = conn.execute(
                """
                SELECT DISTINCT fuero_label as fuero FROM fuero_mappings WHERE is_active = 1
                UNION
                SELECT DISTINCT fuero FROM pcs WHERE fuero IS NOT NULL AND fuero != '' AND fuero != 'Desconocido' AND fuero != 'Sin Fuero'
                ORDER BY fuero ASC
                """
            ).fetchall()
            fueros = [r['fuero'] for r in fueros_rows if r.get('fuero')]

            # Remitos y OCs disponibles
            remitos_rows = conn.execute(
                "SELECT DISTINCT invoice_number FROM components WHERE invoice_number IS NOT NULL AND invoice_number != '' ORDER BY invoice_number ASC"
            ).fetchall()
            remitos = [r['invoice_number'] for r in remitos_rows]

            ocs_rows = conn.execute(
                "SELECT DISTINCT oc_number FROM components WHERE oc_number IS NOT NULL AND oc_number != '' ORDER BY oc_number ASC"
            ).fetchall()
            ocs = [r['oc_number'] for r in ocs_rows]

    except Exception as exc:
        logging.error("Error en build_orders_view: %s", exc)
        pcs, ad_users, stock_components, build_orders_list, fueros, remitos, ocs = [], [], [], [], [], [], []

    return render_template(
        "build_orders.html",
        pcs=pcs,
        ad_users=ad_users,
        stock_components=stock_components,
        build_orders=build_orders_list,
        fueros=fueros,
        remitos=remitos,
        ocs=ocs
    )


@bp_stock.route("/api/components/stock_available", methods=["GET"])
def get_available_stock_components():
    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT serial_number, component_type, brand_model, supplier, is_autogenerated_id
                FROM components
                WHERE (status = 'Stock' OR status IS NULL)
                  AND (assigned_pc IS NULL OR assigned_pc = '')
                  AND (assigned_user IS NULL OR assigned_user = '')
                ORDER BY component_type ASC, brand_model ASC
                """
            ).fetchall()
            comps = []
            for r in rows:
                item = dict(r)
                sn = item.get('serial_number') or ''
                if item.get('is_autogenerated_id') or sn.upper().startswith('INT-'):
                    item['is_autogenerated_id'] = 1
                else:
                    item['is_autogenerated_id'] = 0
                comps.append(item)

            try:
                net_printers_rows = conn.execute(
                    """
                    SELECT serial_number, ip_address, brand_model, fuero
                    FROM network_printers
                    WHERE serial_number IS NOT NULL AND TRIM(serial_number) != ''
                    """
                ).fetchall()
                existing_serials = {c["serial_number"] for c in comps if c.get("serial_number")}
                for np in net_printers_rows:
                    sn = np["serial_number"].strip()
                    if sn and sn not in existing_serials:
                        comps.append({
                            "serial_number": sn,
                            "component_type": "Impresora (Red)",
                            "brand_model": f"{np.get('brand_model') or 'Impresora'} [IP: {np.get('ip_address') or 'N/A'}]",
                            "supplier": np.get("fuero") or "Infraestructura",
                            "is_autogenerated_id": 0
                        })
            except Exception: pass
        return jsonify({"status": "success", "components": comps})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_stock.route("/api/components/list")
def list_components():
    try:
        with get_db_connection() as conn:
            rows = conn.execute("SELECT * FROM components ORDER BY created_at DESC").fetchall()
            comps = []
            for r in rows:
                item = dict(r)
                sn = item.get('serial_number') or ''
                if item.get('is_autogenerated_id') or sn.upper().startswith('INT-'):
                    item['is_autogenerated_id'] = 1
                else:
                    item['is_autogenerated_id'] = 0
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
        if not check_stock_permission():
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
        supplier = (data.get("supplier_name") or data.get("supplier") or "").strip() or "STOCK INTERNO / TALLER"
        invoice = (data.get("remito_number") or data.get("invoice_number") or "").strip() or "SIN REMITO"
        oc_num = (data.get("oc_number") or "").strip()
        assigned_user = (data.get("assigned_user") or "").strip()
        assigned_fuero = (data.get("assigned_fuero") or "").strip()
        quantity = min(500, max(1, int(data.get("quantity", 1))))

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
                elif curr_serial.upper().startswith("INT-"):
                    is_auto = 1

                try:
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
                except Exception as insert_err:
                    err_str = str(insert_err).lower()
                    if "duplicate" in err_str or "1062" in err_str:
                        return jsonify({"status": "error", "message": f"El número de serie '{curr_serial}' ya existe registrado en el inventario."}), 400
                    raise insert_err

                added_serials.append(curr_serial)

            if ctype: conn.execute("INSERT IGNORE INTO stock_catalogs (category, item_value) VALUES ('type', %s)", (ctype,))
            if model: conn.execute("INSERT IGNORE INTO stock_catalogs (category, item_value) VALUES ('model', %s)", (model,))
            if supplier: conn.execute("INSERT IGNORE INTO stock_catalogs (category, item_value) VALUES ('supplier', %s)", (supplier,))

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

        return jsonify({"status": "success", "serials": added_serials})
    except Exception as e:
        logging.error(f"Error en add_component: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Ocurrió un error al procesar el alta de componentes."}), 500

@bp_stock.route("/api/components/add_batch", methods=["POST"])
def add_components_batch():
    try:
        if not check_stock_permission():
            return jsonify({"status": "error", "message": "Acceso denegado: Solo los usuarios con el permiso 'Gestión Stock' pueden cargar nuevos remitos."}), 403

        data = request.json or {}
        supplier = (data.get("supplier_name") or data.get("supplier") or "").strip() or "STOCK INTERNO / TALLER"
        invoice = (data.get("remito_number") or data.get("invoice_number") or "").strip() or "SIN REMITO"
        oc_num = (data.get("oc_number") or "").strip()
        assigned_user = (data.get("assigned_user") or "").strip()
        assigned_fuero = (data.get("assigned_fuero") or "").strip()
        items = data.get("items") or []

        if not isinstance(items, list) or len(items) == 0:
            return jsonify({"status": "error", "message": "No se recibieron componentes para ingresar al stock."}), 400

        with get_db_connection() as conn:
            if assigned_user and not assigned_fuero:
                ad_row = conn.execute(
                    "SELECT fuero FROM ad_users WHERE LOWER(username) = %s OR LOWER(real_name) = %s LIMIT 1",
                    (assigned_user.lower(), assigned_user.lower())
                ).fetchone()
                if ad_row and ad_row.get("fuero"):
                    assigned_fuero = ad_row["fuero"]

            status = 'Asignado' if (assigned_user or assigned_fuero) else 'Stock'

            provided_serials = [item.get("serial_number", "").strip() for item in items if item.get("serial_number", "").strip()]
            if len(provided_serials) != len(set(provided_serials)):
                return jsonify({"status": "error", "message": "Existen N° de Serie / Códigos de Barras duplicados en la lista enviada."}), 400

            for s in provided_serials:
                existing = conn.execute("SELECT id FROM components WHERE serial_number = %s", (s,)).fetchone()
                if existing:
                    return jsonify({"status": "error", "message": f"El código de barras / N° de serie '{s}' ya está registrado en el inventario."}), 400

            added_serials = []
            for item in items:
                ctype = (item.get("component_type") or "").strip()
                model = (item.get("brand_model") or "").strip()
                curr_serial = (item.get("serial_number") or "").strip()

                if not ctype:
                    continue

                is_auto = 0
                if not curr_serial:
                    while True:
                        curr_serial = generate_internal_serial(ctype)
                        chk = conn.execute("SELECT id FROM components WHERE serial_number = %s", (curr_serial,)).fetchone()
                        if not chk and curr_serial not in added_serials:
                            break
                    is_auto = 1
                elif curr_serial.upper().startswith("INT-"):
                    is_auto = 1

                try:
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
                except Exception as insert_err:
                    err_str = str(insert_err).lower()
                    if "duplicate" in err_str or "1062" in err_str:
                        return jsonify({"status": "error", "message": f"El número de serie '{curr_serial}' ya existe en el inventario."}), 400
                    raise insert_err

                added_serials.append(curr_serial)

                if ctype: conn.execute("INSERT IGNORE INTO stock_catalogs (category, item_value) VALUES ('type', %s)", (ctype,))
                if model: conn.execute("INSERT IGNORE INTO stock_catalogs (category, item_value) VALUES ('model', %s)", (model,))
            if supplier: conn.execute("INSERT IGNORE INTO stock_catalogs (category, item_value) VALUES ('supplier', %s)", (supplier,))

            from utils.auth import current_technician_identity
            tech = current_technician_identity()
            if tech:
                from datetime import datetime
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                desc = f"Alta de Puesto / Lote: {len(added_serials)} componentes (Remito: {invoice or 'N/A'}, Proveedor: {supplier or 'N/A'})"
                conn.execute(
                    "INSERT INTO tasks (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to, fuero) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (None, desc, tech, 'Hecha', now_str, tech, now_str, 'Hardware', tech, assigned_fuero or None)
                )

        return jsonify({"status": "success", "count": len(added_serials), "serials": added_serials})
    except Exception as e:
        logging.error(f"Error en add_components_batch: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Ocurrió un error al procesar la recepción del lote de componentes."}), 500

@bp_stock.route("/api/components/retire", methods=["POST"])
def retire_component():
    try:
        if not check_stock_permission():
            return jsonify({"status": "error", "message": "Acceso denegado: Se requiere permiso de Gestión Stock."}), 403

        from utils.auth import current_username, current_technician_identity
        tech = current_technician_identity()
        user_name = current_username() or tech

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
                    detalles = f"UPS {ups['model']} (S/N: {serial}) -> Motivo: {reason}"
                    conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                                 (old_pc or 'Stock', 'UPS Retirada', detalles, 'Retirado', user_name, "BAJA_COMPONENTE", request.remote_addr))
                    return jsonify({"status": "success"})
                    
            old_status = comp.get("status") or "Stock"
            old_pc = comp.get("assigned_pc")
            conn.execute(
                "UPDATE components SET status = 'Retirado', assigned_pc = NULL, assigned_user = NULL, assigned_fuero = NULL WHERE serial_number = %s",
                (serial,)
            )
            detalles = f"{comp['component_type']} {comp['brand_model']} (S/N: {serial}) -> Motivo: {reason}"
            conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                         (old_pc or 'Stock', 'COMPONENT_RETIRED', old_status, detalles, user_name, "BAJA_COMPONENTE", request.remote_addr))
            
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

        return jsonify({"status": "success"})
    except Exception as e:
        logging.error(f"Error en retire_component: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Ocurrió un error al dar de baja el componente."}), 500

@bp_stock.route("/api/components/retire_bulk", methods=["POST"])
def retire_components_bulk():
    try:
        if not check_stock_permission():
            return jsonify({"status": "error", "message": "Acceso denegado: Se requiere permiso de Gestión Stock."}), 403

        from utils.auth import current_username, current_technician_identity
        tech = current_technician_identity()
        user_name = current_username() or tech

        data = request.json or {}
        serials = data.get("serials", [])
        reason = (data.get("reason") or "Baja en bloque / Retirado de servicio").strip()
        if not serials or not isinstance(serials, list):
            return jsonify({"status": "error", "message": "Seleccione al menos un componente para dar de baja."}), 400

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
                                 (old_pc or 'Stock', 'COMPONENT_RETIRED', old_status, detalles, user_name, "BAJA_COMPONENTE", request.remote_addr))
            
            if tech and retired_count > 0:
                from datetime import datetime
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                desc = f"Baja de componentes en bloque: {retired_count} ítem(s) retirados"
                conn.execute(
                    "INSERT INTO tasks (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (None, desc, tech, 'Hecha', now_str, tech, now_str, 'Hardware', tech)
                )

        return jsonify({"status": "success", "count": retired_count})
    except Exception as e:
        logging.error(f"Error en retire_components_bulk: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Ocurrió un error al dar de baja los componentes en bloque."}), 500

@bp_stock.route("/api/components/restore_stock", methods=["POST"])
def restore_component():
    try:
        if not check_stock_permission():
            return jsonify({"status": "error", "message": "Acceso denegado: Se requiere permiso de Gestión Stock."}), 403

        from utils.auth import current_username, current_technician_identity
        tech = current_technician_identity()
        user_name = current_username() or tech

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

            detalles = f"{comp['component_type']} {comp['brand_model']} (S/N: {serial}) -> Reactivado a Stock"
            conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                         ('Stock', 'COMPONENT_RESTORED', 'Retirado', detalles, user_name, "REACTIVACION_STOCK", request.remote_addr))

        return jsonify({"status": "success"})
    except Exception as e:
        logging.error(f"Error en restore_component: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Ocurrió un error al reactivar el componente a stock."}), 500

@bp_stock.route("/api/components/assign", methods=["POST"])
def assign_component():
    try:
        if not check_stock_permission():
            return jsonify({"status": "error", "message": "Acceso denegado: Se requiere permiso de Gestión Stock."}), 403

        from utils.auth import current_username, current_technician_identity
        tech = current_technician_identity()
        user_name = current_username() or tech

        data = request.json or {}
        serial = (data.get("serial_number") or "").strip()
        pc_name = (data.get("pc_name") or "").strip()
        assigned_user = (data.get("assigned_user") or "").strip()
        assigned_fuero = (data.get("assigned_fuero") or "").strip()

        if not serial:
            return jsonify({"status": "error", "message": "Falta serial del componente"}), 400

        with get_db_connection() as conn:
            # Resolver o guardar fuero en AD si hay usuario
            if assigned_user:
                if assigned_fuero:
                    conn.execute(
                        "UPDATE ad_users SET fuero = %s WHERE LOWER(username) = %s OR LOWER(real_name) = %s",
                        (assigned_fuero, assigned_user.lower(), assigned_user.lower())
                    )
                else:
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
                    target_dest = pc_name or assigned_user or assigned_fuero or "Desconocido"
                    conn.execute(
                        "INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (target_dest, 'UPS Asignada', 'Stock', detalles, user_name, "GESTION_STOCK", request.remote_addr)
                    )
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
            target_dest = pc_name or assigned_user or assigned_fuero or "Desconocido"
            conn.execute(
                "INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (target_dest, 'COMPONENT_ASSIGN', comp.get('status') or 'Stock', detalles, user_name, "GESTION_STOCK", request.remote_addr)
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

@bp_stock.route("/api/components/assign_bundle", methods=["POST"])
def assign_component_bundle():
    try:
        if not check_stock_permission():
            return jsonify({"status": "error", "message": "Acceso denegado: Se requiere permiso de Gestión Stock."}), 403

        data = request.json or {}
        serials = data.get("serials") or []
        pc_name = (data.get("pc_name") or "").strip()
        assigned_user = (data.get("assigned_user") or "").strip()
        assigned_fuero = (data.get("assigned_fuero") or "").strip()
        is_stock_kit = bool(data.get("is_stock_kit"))
        kit_name = (data.get("kit_name") or "").strip()

        if isinstance(serials, str):
            serials = [serials]

        clean_serials = [s.strip() for s in serials if s and s.strip()]
        if not clean_serials:
            return jsonify({"status": "error", "message": "Seleccioná o escaneá al menos un componente."}), 400

        with get_db_connection() as conn:
            from utils.auth import current_username, current_technician_identity
            tech = current_technician_identity()
            current_usr = current_username() or tech

            # Si es armado de Kit para Stock (no crea fila en pcs)
            if is_stock_kit or (kit_name and not pc_name and not assigned_user):
                final_kit_name = kit_name or pc_name or f"KIT-STOCK-{datetime.datetime.now().strftime('%m%d%H%M')}"
                assigned_count = 0
                for serial in clean_serials:
                    comp = conn.execute("SELECT * FROM components WHERE serial_number = %s", (serial,)).fetchone()
                    if comp:
                        conn.execute(
                            """
                            UPDATE components
                            SET status = 'Stock (Combo)', kit_name = %s, assigned_pc = NULL, assigned_user = NULL, assigned_fuero = NULL
                            WHERE serial_number = %s
                            """,
                            (final_kit_name, serial)
                        )
                        assigned_count += 1
                        detalles = f"Agregado a Kit '{final_kit_name}' (S/N: {serial})"
                        conn.execute(
                            "INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                            ("Stock", 'STOCK_KIT_CREATE', comp.get('status') or 'Stock', detalles, current_usr, "GESTION_STOCK", request.remote_addr)
                        )

                conn.commit()
                return jsonify({
                    "status": "success",
                    "is_stock_kit": True,
                    "kit_name": final_kit_name,
                    "count": assigned_count,
                    "message": f"Kit '{final_kit_name}' guardado exitosamente en Stock."
                })

            # Asignación / Despliegue directo a PC o Usuario de red
            # Auto-resolver usuario y fuero de AD
            if assigned_user:
                ad_row = conn.execute(
                    """
                    SELECT username, real_name, fuero FROM ad_users 
                    WHERE LOWER(username) = %s 
                       OR LOWER(real_name) = %s 
                       OR %s LIKE CONCAT('%%(', LOWER(username), ')%%')
                       OR %s LIKE CONCAT(LOWER(real_name), '%%')
                    LIMIT 1
                    """,
                    (assigned_user.lower(), assigned_user.lower(), assigned_user.lower(), assigned_user.lower())
                ).fetchone()
                if ad_row:
                    if not assigned_fuero and ad_row.get("fuero"):
                        assigned_fuero = ad_row["fuero"]
                    if ad_row.get("real_name"):
                        assigned_user = ad_row["real_name"]

            # Si se especificó una PC y no existe en pcs, registrarla como equipo activo en el inventario
            if pc_name and pc_name != 'PC Generica':
                chk_pc = conn.execute("SELECT pc_name FROM pcs WHERE pc_name = %s", (pc_name,)).fetchone()
                if not chk_pc:
                    conn.execute(
                        """
                        INSERT INTO pcs (pc_name, last_user, fuero, is_active, os_name)
                        VALUES (%s, %s, %s, 1, 'Equipo registrado desde Armado / Asignación de Stock')
                        """,
                        (pc_name, assigned_user or None, assigned_fuero or 'Stock')
                    )

            target_dest = pc_name or assigned_user or assigned_fuero or "Desconocido"

            assigned_count = 0
            assigned_types = []

            for serial in clean_serials:
                comp = conn.execute("SELECT * FROM components WHERE serial_number = %s", (serial,)).fetchone()
                if comp:
                    new_status = 'Installed' if pc_name else 'Asignado'
                    conn.execute(
                        """
                        UPDATE components
                        SET status = %s, assigned_pc = %s, assigned_user = %s, assigned_fuero = %s, kit_name = NULL
                        WHERE serial_number = %s
                        """,
                        (new_status, pc_name or None, assigned_user or None, assigned_fuero or None, serial)
                    )
                    detalles = f"{comp['component_type']} {comp['brand_model']} (S/N: {serial}) -> {target_dest}"
                    conn.execute(
                        "INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (target_dest, 'BUNDLE_ASSIGN', comp.get('status') or 'Stock', detalles, current_usr, "GESTION_STOCK", request.remote_addr)
                    )
                    assigned_count += 1
                    assigned_types.append(comp['component_type'])
                else:
                    ups = conn.execute("SELECT * FROM ups_inventory WHERE code = %s", (serial,)).fetchone()
                    if ups:
                        conn.execute("UPDATE ups_inventory SET assigned_pc = %s WHERE code = %s", (pc_name or None, serial))
                        detalles = f"UPS {ups['model']} (S/N: {serial}) -> {target_dest}"
                    assigned_types.append("UPS")

            if tech and assigned_count > 0:
                from datetime import datetime
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                types_str = ", ".join(set(assigned_types))
                desc = f"Asignó {assigned_count} componente(s) [{types_str}] a {target_dest}"
                
                valid_task_pc = pc_name or None
                if not valid_task_pc and assigned_user:
                    user_pc = conn.execute(
                        """
                        SELECT pc_name, fuero FROM pcs 
                        WHERE (LOWER(last_user) LIKE %s OR LOWER(last_user) LIKE %s)
                          AND is_active = 1 
                          AND pc_name NOT IN ('PC Generica', 'Infraestructura', 'PC-Generica')
                        ORDER BY updated_at DESC LIMIT 1
                        """,
                        (f"%{assigned_user.lower()}%", f"%\\{assigned_user.lower()}")
                    ).fetchone()
                    if user_pc:
                        valid_task_pc = user_pc["pc_name"]
                        if not assigned_fuero and user_pc.get("fuero"):
                            assigned_fuero = user_pc["fuero"]

                conn.execute(
                    "INSERT INTO tasks (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to, fuero) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (valid_task_pc or "PC Generica", desc, assigned_user or tech, 'Hecha', now_str, tech, now_str, 'Hardware', tech, assigned_fuero or None)
                )

            conn.commit()

        return jsonify({"status": "success", "count": assigned_count, "resolved_fuero": assigned_fuero})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp_stock.route("/api/stock/kits", methods=["GET"])
def get_stock_kits():
    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, serial_number, component_type, brand_model, status, kit_name, supplier, created_at
                FROM components
                WHERE kit_name IS NOT NULL AND TRIM(kit_name) != '' AND status LIKE 'Stock%'
                ORDER BY kit_name ASC, component_type ASC
                """
            ).fetchall()

            kits = {}
            for r in rows:
                kname = r["kit_name"]
                if kname not in kits:
                    created_str = r["created_at"].strftime("%Y-%m-%d %H:%M") if r.get("created_at") and hasattr(r["created_at"], "strftime") else str(r.get("created_at") or "")
                    kits[kname] = {
                        "kit_name": kname,
                        "created_at": created_str,
                        "components": []
                    }
                item = dict(r)
                if item.get("created_at") and hasattr(item["created_at"], "strftime"):
                    item["created_at"] = item["created_at"].strftime("%Y-%m-%d %H:%M")
                kits[kname]["components"].append(item)

            return jsonify({
                "status": "success",
                "kits": list(kits.values())
            })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp_stock.route("/api/stock/kits/update", methods=["POST"])
def update_stock_kit():
    """Suma nuevos componentes del stock o retira componentes de un kit armado en depósito."""
    try:
        if not check_stock_permission():
            return jsonify({"status": "error", "message": "Acceso denegado: Se requiere permiso de Gestión Stock."}), 403

        data = request.json or {}
        kit_name = (data.get("kit_name") or "").strip()
        add_serials = data.get("add_serials") or []
        remove_serials = data.get("remove_serials") or []

        if not kit_name:
            return jsonify({"status": "error", "message": "Nombre de Kit requerido."}), 400

        from utils.auth import current_username, current_technician_identity
        current_usr = current_username() or current_technician_identity()

        added_count = 0
        removed_count = 0

        with get_db_connection() as conn:
            # 1. Sumar nuevos componentes al kit
            for serial in add_serials:
                serial_clean = str(serial).strip()
                if not serial_clean:
                    continue
                comp = conn.execute("SELECT * FROM components WHERE serial_number = %s", (serial_clean,)).fetchone()
                if comp:
                    conn.execute(
                        """
                        UPDATE components
                        SET status = 'Stock (Combo)', kit_name = %s, assigned_pc = NULL, assigned_user = NULL, assigned_fuero = NULL
                        WHERE serial_number = %s
                        """,
                        (kit_name, serial_clean)
                    )
                    added_count += 1
                    detalles = f"Componente {comp['component_type']} (S/N: {serial_clean}) sumado al Kit '{kit_name}'"
                    conn.execute(
                        "INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        ("Stock", 'KIT_ADD_COMP', comp.get('status') or 'Stock', detalles, current_usr, "GESTION_STOCK", request.remote_addr)
                    )

            # 2. Retirar/Desvincular componentes del kit
            for serial in remove_serials:
                serial_clean = str(serial).strip()
                if not serial_clean:
                    continue
                comp = conn.execute("SELECT * FROM components WHERE serial_number = %s AND kit_name = %s", (serial_clean, kit_name)).fetchone()
                if comp:
                    conn.execute(
                        """
                        UPDATE components
                        SET status = 'Stock', kit_name = NULL
                        WHERE serial_number = %s AND kit_name = %s
                        """,
                        (serial_clean, kit_name)
                    )
                    removed_count += 1
                    detalles = f"Componente {comp['component_type']} (S/N: {serial_clean}) desvinculado del Kit '{kit_name}'"
                    conn.execute(
                        "INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        ("Stock", 'KIT_REMOVE_COMP', kit_name, detalles, current_usr, "GESTION_STOCK", request.remote_addr)
                    )

            conn.commit()

        return jsonify({
            "status": "success",
            "message": f"Kit '{kit_name}' actualizado: {added_count} pieza(s) sumada(s), {removed_count} retirada(s).",
            "added_count": added_count,
            "removed_count": removed_count
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp_stock.route("/api/stock/kits/deploy", methods=["POST"])
def deploy_stock_kit():
    try:
        if not check_stock_permission():
            return jsonify({"status": "error", "message": "Acceso denegado: Se requiere permiso de Gestión Stock."}), 403

        data = request.json or {}
        kit_name = (data.get("kit_name") or "").strip()
        pc_name = (data.get("pc_name") or "").strip()
        assigned_user = (data.get("assigned_user") or "").strip()
        assigned_fuero = (data.get("assigned_fuero") or "").strip()

        if not kit_name:
            return jsonify({"status": "error", "message": "Nombre de Kit requerido."}), 400

        if not pc_name and not assigned_user and not assigned_fuero:
            return jsonify({"status": "error", "message": "Ingresá un nombre de PC o un Usuario/Fuero de destino."}), 400

        with get_db_connection() as conn:
            # Resolver usuario y fuero de AD
            if assigned_user:
                ad_row = conn.execute(
                    """
                    SELECT username, real_name, fuero FROM ad_users 
                    WHERE LOWER(username) = %s OR LOWER(real_name) = %s 
                    LIMIT 1
                    """,
                    (assigned_user.lower(), assigned_user.lower())
                ).fetchone()
                if ad_row:
                    if not assigned_fuero and ad_row.get("fuero"):
                        assigned_fuero = ad_row["fuero"]
                    if ad_row.get("real_name"):
                        assigned_user = ad_row["real_name"]

            # Si se especificó una PC y no existe en pcs, registrarla como equipo activo en el inventario
            if pc_name and pc_name != 'PC Generica':
                chk_pc = conn.execute("SELECT pc_name FROM pcs WHERE pc_name = %s", (pc_name,)).fetchone()
                if not chk_pc:
                    conn.execute(
                        """
                        INSERT INTO pcs (pc_name, last_user, fuero, is_active, os_name)
                        VALUES (%s, %s, %s, 1, 'Equipo desplegado desde Kit de Stock')
                        """,
                        (pc_name, assigned_user or None, assigned_fuero or 'Stock')
                    )

            from utils.auth import current_username, current_technician_identity
            tech = current_technician_identity()
            current_usr = current_username() or tech
            target_dest = pc_name or assigned_user or assigned_fuero or "Desconocido"

            new_status = 'Installed' if pc_name else 'Asignado'

            conn.execute(
                """
                UPDATE components
                SET status = %s, assigned_pc = %s, assigned_user = %s, assigned_fuero = %s, kit_name = NULL
                WHERE kit_name = %s
                """,
                (new_status, pc_name or None, assigned_user or None, assigned_fuero or None, kit_name)
            )

            detalles = f"Kit '{kit_name}' desplegado -> {target_dest}"
            conn.execute(
                "INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (target_dest, 'KIT_DEPLOY', f"Kit {kit_name}", detalles, current_usr, "GESTION_STOCK", request.remote_addr)
            )

        return jsonify({"status": "success", "message": f"Kit '{kit_name}' desplegado exitosamente a {target_dest}."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp_stock.route("/api/stock/kits/disassemble", methods=["POST"])
def disassemble_stock_kit():
    try:
        if not check_stock_permission():
            return jsonify({"status": "error", "message": "Acceso denegado: Se requiere permiso de Gestión Stock."}), 403

        data = request.json or {}
        kit_name = (data.get("kit_name") or "").strip()

        if not kit_name:
            return jsonify({"status": "error", "message": "Nombre de Kit requerido."}), 400

        with get_db_connection() as conn:
            conn.execute(
                """
                UPDATE components
                SET status = 'Stock', kit_name = NULL
                WHERE kit_name = %s
                """,
                (kit_name,)
            )

            from utils.auth import current_username, current_technician_identity
            current_usr = current_username() or current_technician_identity()
            conn.execute(
                "INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                ("Stock", 'KIT_DISASSEMBLE', f"Kit {kit_name}", f"Kit '{kit_name}' desarmado (piezas devueltas a Stock)", current_usr, "GESTION_STOCK", request.remote_addr)
            )

        return jsonify({"status": "success", "message": f"Kit '{kit_name}' desarmado y piezas devueltas al stock."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp_stock.route("/stock/kit/<kit_name>/qr_label", methods=["GET"])
def kit_qr_label_view(kit_name):
    """Renderiza la plantilla de impresión de sticker QR para un Kit en Depósito."""
    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, serial_number, component_type, brand_model, status, kit_name, supplier, created_at, assigned_pc, assigned_user, assigned_fuero, oc_number, invoice_number
                FROM components
                WHERE kit_name = %s AND status LIKE %s
                ORDER BY component_type ASC
                """,
                (kit_name, "Stock%")
            ).fetchall()
            
            if not rows:
                from flask import abort
                abort(404)
            
            components = [dict(r) for r in rows]
            
            def match_comp(types_list):
                return [c for c in components if any(k in (c.get("component_type") or "").upper() for k in types_list)]

            cpu_comps = match_comp(["CPU", "GABINETE", "GAB"])
            processor_comps = match_comp(["MICRO", "PROCESADOR", "PROC"])
            motherboard_comps = match_comp(["MOTHER", "PLACA", "MOBO"])
            ram_comps = match_comp(["MEMORIA", "RAM"])
            disk_comps = match_comp(["DISCO", "SSD", "HDD", "NVME", "ALMACENAMIENTO"])
            power_comps = match_comp(["FUENTE", "POWER", "FNT"])
            monitor_comps = match_comp(["MONITOR", "MON"])
            keyboard_comps = match_comp(["TECLADO", "TEC"])
            mouse_comps = match_comp(["MOUSE", "MOU"])

            used_ids = {c['id'] for group in [cpu_comps, processor_comps, motherboard_comps, ram_comps, disk_comps, power_comps, monitor_comps, keyboard_comps, mouse_comps] for c in group}
            other_comps = [c for c in components if c['id'] not in used_ids]
            
            scheme = request.headers.get("X-Forwarded-Proto", request.scheme)
            server_host = request.host
            qr_url = f"{scheme}://{server_host}/stock/kit/{kit_name}"
            
            oc_list = sorted(list({c["oc_number"].strip() for c in components if c.get("oc_number") and c["oc_number"].strip()}))
            invoice_list = sorted(list({c["invoice_number"].strip() for c in components if c.get("invoice_number") and c["invoice_number"].strip()}))
            assigned_user = next((c["assigned_user"].strip() for c in components if c.get("assigned_user") and c["assigned_user"].strip()), None)
            assigned_fuero = next((c["assigned_fuero"].strip() for c in components if c.get("assigned_fuero") and c["assigned_fuero"].strip()), None)
            assigned_pc = next((c["assigned_pc"].strip() for c in components if c.get("assigned_pc") and c["assigned_pc"].strip()), None)

            return render_template(
                "kit_qr_label.html",
                kit_name=kit_name,
                components=components,
                cpu_comp=cpu_comps[0] if cpu_comps else None,
                processor_comp=processor_comps[0] if processor_comps else None,
                motherboard_comp=motherboard_comps[0] if motherboard_comps else None,
                ram_comps=ram_comps,
                ram_comp=ram_comps[0] if ram_comps else None,
                disk_comps=disk_comps,
                disk_comp=disk_comps[0] if disk_comps else None,
                power_comp=power_comps[0] if power_comps else None,
                monitor_comps=monitor_comps,
                monitor_comp=monitor_comps[0] if monitor_comps else None,
                keyboard_comp=keyboard_comps[0] if keyboard_comps else None,
                mouse_comp=mouse_comps[0] if mouse_comps else None,
                other_comps=other_comps,
                qr_url=qr_url,
                server_host=server_host,
                oc_list=oc_list,
                invoice_list=invoice_list,
                assigned_user=assigned_user,
                assigned_fuero=assigned_fuero,
                assigned_pc=assigned_pc
            )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@bp_stock.route("/stock/kit/<kit_name>", methods=["GET"])
def view_stock_kit_detail(kit_name):
    """Ficha móvil en vivo cuando un técnico escanea el QR del kit en la estantería del depósito."""
    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, serial_number, component_type, brand_model, status, kit_name, supplier, created_at, assigned_pc, assigned_user, assigned_fuero, oc_number, invoice_number
                FROM components
                WHERE kit_name = %s
                ORDER BY component_type ASC
                """,
                (kit_name,)
            ).fetchall()
            
            # Si el kit fue desplegado a una PC, redirigir a esa PC
            if not rows:
                chk_pc = conn.execute("SELECT pc_name FROM pcs WHERE pc_name = %s", (kit_name,)).fetchone()
                if chk_pc:
                    from flask import redirect, url_for
                    return redirect(url_for("dashboard.pc_detail", pc_name=kit_name))
                
                return render_template("kit_detail_view.html", kit_name=kit_name, components=[], created_at=None, oc_list=[], invoice_list=[], assigned_user=None, assigned_fuero=None, assigned_pc=None)

            components = [dict(r) for r in rows]
            created_str = components[0]["created_at"].strftime("%Y-%m-%d %H:%M") if components[0].get("created_at") and hasattr(components[0]["created_at"], "strftime") else str(components[0].get("created_at") or "")

            oc_list = sorted(list({c["oc_number"].strip() for c in components if c.get("oc_number") and c["oc_number"].strip()}))
            invoice_list = sorted(list({c["invoice_number"].strip() for c in components if c.get("invoice_number") and c["invoice_number"].strip()}))
            assigned_user = next((c["assigned_user"].strip() for c in components if c.get("assigned_user") and c["assigned_user"].strip()), None)
            assigned_fuero = next((c["assigned_fuero"].strip() for c in components if c.get("assigned_fuero") and c["assigned_fuero"].strip()), None)
            assigned_pc = next((c["assigned_pc"].strip() for c in components if c.get("assigned_pc") and c["assigned_pc"].strip()), None)

            return render_template(
                "kit_detail_view.html",
                kit_name=kit_name,
                components=components,
                created_at=created_str,
                oc_list=oc_list,
                invoice_list=invoice_list,
                assigned_user=assigned_user,
                assigned_fuero=assigned_fuero,
                assigned_pc=assigned_pc
            )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@bp_stock.route("/api/components/swap_failing_component", methods=["POST"])
def swap_failing_component():
    try:
        if not check_stock_permission():
            return jsonify({"status": "error", "message": "Acceso denegado: Se requiere permiso de Gestión Stock."}), 403

        data = request.json or {}
        old_serial = (data.get("old_serial") or "").strip()
        new_serial = (data.get("new_serial") or "").strip()
        retire_reason = (data.get("retire_reason") or "Falla técnica - Scrap").strip()
        pc_name = (data.get("pc_name") or "").strip()

        if not old_serial:
            return jsonify({"status": "error", "message": "Falta especificar el componente averiado."}), 400

        with get_db_connection() as conn:
            from utils.auth import current_username, current_technician_identity
            tech = current_technician_identity()
            current_usr = current_username() or tech

            old_comp = conn.execute("SELECT * FROM components WHERE serial_number = %s", (old_serial,)).fetchone()
            if not old_comp:
                return jsonify({"status": "error", "message": f"Componente {old_serial} no encontrado."}), 404

            target_pc = pc_name or old_comp.get("assigned_pc") or "Desconocido"
            user_target = old_comp.get("assigned_user") or ""
            fuero_target = old_comp.get("assigned_fuero") or ""

            # 1. Dar de baja el componente averiado (Scrap)
            conn.execute(
                """
                UPDATE components
                SET status = 'Retirado', assigned_pc = NULL, updated_at = NOW()
                WHERE serial_number = %s
                """,
                (old_serial,)
            )

            detalles_baja = f"Retirado por falla: {old_comp['component_type']} {old_comp['brand_model']} (S/N: {old_serial}). Motivo: {retire_reason}"
            conn.execute(
                "INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (target_pc, 'REEMPLAZO_FALLA_BAJA', f"Installed ({old_comp['component_type']})", detalles_baja, current_usr, "GESTION_STOCK", request.remote_addr)
            )

            # 2. Asignar el nuevo componente repuesto (si se especificó)
            new_comp_desc = ""
            if new_serial:
                new_comp = conn.execute("SELECT * FROM components WHERE serial_number = %s", (new_serial,)).fetchone()
                if not new_comp:
                    return jsonify({"status": "error", "message": f"El nuevo componente repuesto (S/N: {new_serial}) no se encuentra en el stock."}), 404

                new_status = 'Installed' if target_pc and target_pc != 'Desconocido' else 'Asignado'
                conn.execute(
                    """
                    UPDATE components
                    SET status = %s, assigned_pc = %s, assigned_user = %s, assigned_fuero = %s
                    WHERE serial_number = %s
                    """,
                    (new_status, target_pc if target_pc != 'Desconocido' else None, user_target, fuero_target, new_serial)
                )

                detalles_alta = f"Repuesto instalado por falla: {new_comp['component_type']} {new_comp['brand_model']} (S/N: {new_serial})"
                conn.execute(
                    "INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (target_pc, 'REEMPLAZO_FALLA_ALTA', 'Stock', detalles_alta, current_usr, "GESTION_STOCK", request.remote_addr)
                )
                new_comp_desc = f" -> Instalado repuesto {new_comp['brand_model']} (S/N: {new_serial})"

            # 3. Registrar tarea técnica realizada
            if tech:
                from datetime import datetime
                now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                desc = f"Reemplazo por Falla: Se retiró {old_comp['component_type']} (S/N: {old_serial}) [{retire_reason}]{new_comp_desc}"
                
                valid_task_pc = target_pc if target_pc and target_pc != 'Desconocido' else None
                if not valid_task_pc and user_target:
                    user_pc = conn.execute(
                        """
                        SELECT pc_name, fuero FROM pcs 
                        WHERE (LOWER(last_user) LIKE %s OR LOWER(last_user) LIKE %s)
                          AND is_active = 1 
                          AND pc_name NOT IN ('PC Generica', 'Infraestructura', 'PC-Generica')
                        ORDER BY updated_at DESC LIMIT 1
                        """,
                        (f"%{user_target.lower()}%", f"%\\{user_target.lower()}")
                    ).fetchone()
                    if user_pc:
                        valid_task_pc = user_pc["pc_name"]
                        if not fuero_target and user_pc.get("fuero"):
                            fuero_target = user_pc["fuero"]

                conn.execute(
                    "INSERT INTO tasks (pc_name, descripcion, solicitante, estado, created_at, completed_by, completed_at, categoria, assigned_to, fuero) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (valid_task_pc or "PC Generica", desc, user_target or tech, 'Hecha', now_str, tech, now_str, 'Hardware', tech, fuero_target or None)
                )

        return jsonify({"status": "success", "message": "Sustitución por falla registrada con éxito."})
    except Exception as e:
        logging.error(f"Error en swap_failing_component: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Ocurrió un error al registrar el reemplazo por falla."}), 500

@bp_stock.route("/api/components/return", methods=["POST"])
def return_component():
    try:
        if not check_stock_permission():
            return jsonify({"status": "error", "message": "Acceso denegado: Se requiere permiso de Gestión Stock."}), 403

        from utils.auth import current_username, current_technician_identity
        tech = current_technician_identity()
        user_name = current_username() or tech

        data = request.json or {}
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
                    
                    detalles = f"UPS {ups['model']} (S/N: {serial})"
                    conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                                 (old_pc if old_pc != "Unknown" else 'Stock', 'UPS Desasignada', detalles, 'Stock', user_name, "GESTION_INFRAESTRUCTURA", request.remote_addr))
                        
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
                    return jsonify({"status": "success"})
                    
            old_pc = comp["assigned_pc"] or "Unknown"
            conn.execute("UPDATE components SET status = 'Stock', assigned_pc = NULL WHERE serial_number = %s", (serial,))
            
            detalles = f"{comp['component_type']} {comp['brand_model']} (S/N: {serial})"
            conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                         (old_pc if old_pc != "Unknown" else 'Stock', 'COMPONENT_RETURN', detalles, 'Stock', user_name, "GESTION_STOCK", request.remote_addr))
                
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

        return jsonify({"status": "success"})
    except Exception as e:
        logging.error(f"Error en return_component: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Ocurrió un error al procesar la devolución a stock."}), 500

@bp_stock.route("/api/components/delete", methods=["POST"])
def delete_component():
    try:
        if not check_stock_permission():
            return jsonify({"status": "error", "message": "Acceso denegado: Se requiere permiso de Gestión Stock para eliminar componentes."}), 403

        from utils.auth import current_username, current_technician_identity
        user_name = current_username() or current_technician_identity()

        data = request.json or {}
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
                    old_pc = ups["assigned_pc"] or "Stock"
                    # Also unassign battery if any
                    if ups.get('assigned_battery_id'):
                        conn.execute("UPDATE components SET status = 'Stock' WHERE id = %s", (ups['assigned_battery_id'],))
                    conn.execute("DELETE FROM ups_inventory WHERE code = %s", (serial,))
                    
                    detalles = f"UPS {ups['model']} (S/N: {serial})"
                    conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                                 (old_pc, 'UPS Eliminada', detalles, 'DELETED', user_name, "BORRADO_PERMANENTE", request.remote_addr))
                    return jsonify({"status": "success"})
                    
            old_pc = comp["assigned_pc"] or "Stock"
            conn.execute("DELETE FROM components WHERE serial_number = %s", (serial,))
            
            detalles = f"{comp['component_type']} {comp['brand_model']} (S/N: {serial})"
            conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                         (old_pc, 'COMPONENT_DELETED', detalles, 'DELETED', user_name, "BORRADO_PERMANENTE", request.remote_addr))
                
        return jsonify({"status": "success"})
    except Exception as e:
        logging.error(f"Error en delete_component: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Ocurrió un error interno al eliminar el componente."}), 500


@bp_stock.route("/api/components/delete_bulk", methods=["POST"])
def delete_components_bulk():
    try:
        if not check_stock_permission():
            return jsonify({"status": "error", "message": "Acceso denegado: Se requiere permiso de Gestión Stock para eliminar componentes."}), 403

        from utils.auth import current_username, current_technician_identity
        user_name = current_username() or current_technician_identity()

        data = request.json or {}
        serials = data.get("serials", [])
        if not serials or not isinstance(serials, list):
            return jsonify({"status": "error", "message": "Seleccione al menos un componente para eliminar."}), 400

        deleted_count = 0
        with get_db_connection() as conn:
            for serial in serials:
                comp = conn.execute("SELECT * FROM components WHERE serial_number = %s", (serial,)).fetchone()
                if comp:
                    old_pc = comp["assigned_pc"] or "Stock"
                    conn.execute("DELETE FROM components WHERE serial_number = %s", (serial,))
                    deleted_count += 1
                    detalles = f"{comp['component_type']} {comp['brand_model']} (S/N: {serial})"
                    conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                                 (old_pc, 'COMPONENT_DELETED', detalles, 'DELETED', user_name, "BORRADO_PERMANENTE", request.remote_addr))
                else:
                    ups = conn.execute("SELECT * FROM ups_inventory WHERE code = %s", (serial,)).fetchone()
                    if ups:
                        old_pc = ups["assigned_pc"] or "Stock"
                        if ups.get('assigned_battery_id'):
                            conn.execute("UPDATE components SET status = 'Stock' WHERE id = %s", (ups['assigned_battery_id'],))
                        conn.execute("DELETE FROM ups_inventory WHERE code = %s", (serial,))
                        deleted_count += 1
                        detalles = f"UPS {ups['model']} (S/N: {serial})"
                        conn.execute("INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address) VALUES (%s, %s, %s, %s, %s, %s, %s)", 
                                     (old_pc, 'UPS Eliminada', detalles, 'DELETED', user_name, "BORRADO_PERMANENTE", request.remote_addr))

        return jsonify({"status": "success", "message": f"{deleted_count} componente(s) eliminado(s) correctamente."})
    except Exception as e:
        logging.error(f"Error en delete_components_bulk: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Ocurrió un error interno al eliminar los componentes seleccionados."}), 500


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


# ─────────────────────────────────────────────────────────────────────────────
# SISTEMA PATRIMONIAL — Build Orders (Órdenes de Armado)
# ─────────────────────────────────────────────────────────────────────────────

@bp_stock.route("/api/build_orders", methods=["GET"])
def list_build_orders():
    """Lista todas las Órdenes de Armado, con sus ítems agregados."""
    try:
        with get_db_connection() as conn:
            rows = conn.execute(
                """
                SELECT bo.id, bo.code, bo.status, bo.oc_number, bo.invoice_number,
                       bo.target_fuero, bo.target_user, bo.notes,
                       bo.created_by, bo.completed_at, bo.created_at,
                       COUNT(boi.id) AS total_items
                FROM build_orders bo
                LEFT JOIN build_order_items boi ON boi.build_order_id = bo.id
                GROUP BY bo.id
                ORDER BY bo.created_at DESC
                LIMIT 200
                """
            ).fetchall()
            result = []
            for r in rows:
                item = dict(r)
                if item.get("created_at") and hasattr(item["created_at"], "strftime"):
                    item["created_at"] = item["created_at"].strftime("%Y-%m-%d %H:%M")
                if item.get("completed_at") and hasattr(item["completed_at"], "strftime"):
                    item["completed_at"] = item["completed_at"].strftime("%Y-%m-%d %H:%M")
                result.append(item)
        return jsonify({"status": "success", "build_orders": result})
    except Exception as e:
        logging.error("Error en list_build_orders: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp_stock.route("/api/components/generate_auto_id", methods=["GET"])
def api_generate_auto_id():
    """Genera un código Auto ID único (INT-XXX-YYYYMMDD-NNNN) para componentes sin número de serie de fábrica."""
    ctype = request.args.get("component_type", "COMPONENTE")
    serial = generate_internal_serial(ctype)
    return jsonify({"status": "success", "serial_number": serial, "component_type": ctype})


@bp_stock.route("/api/build_orders", methods=["POST"])
def create_build_order():
    """Crea una nueva Orden de Armado en estado 'draft'."""
    if not check_stock_permission():
        return jsonify({"status": "error", "message": "Acceso denegado."}), 403

    try:
        from utils.auth import current_technician_identity
        tech = current_technician_identity()
        data = request.json or {}

        oc_number      = (data.get("oc_number") or "").strip() or None
        invoice_number = (data.get("invoice_number") or "").strip() or None
        target_fuero   = (data.get("target_fuero") or "").strip() or None
        target_user    = (data.get("target_user") or "").strip() or None
        target_pc_name = (data.get("target_pc_name") or "").strip() or None
        notes          = (data.get("notes") or "").strip() or None

        with get_db_connection() as conn:
            # Generar código único: BO-YYYY-NNNN
            custom_code = (data.get("code") or "").strip()
            if custom_code:
                dup = conn.execute("SELECT id FROM build_orders WHERE code = %s", (custom_code,)).fetchone()
                if dup:
                    return jsonify({"status": "error", "message": f"El código '{custom_code}' ya existe."}), 400
                code = custom_code
            else:
                year = datetime.datetime.now().strftime("%Y")
                count_row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM build_orders WHERE YEAR(created_at) = %s", (year,)
                ).fetchone()
                seq = (count_row["cnt"] if count_row else 0) + 1
                code = f"BO-{year}-{seq:04d}"
            conn.execute(
                """
                INSERT INTO build_orders
                    (code, oc_number, invoice_number, target_fuero, target_user, target_pc_name, notes, created_by, status)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'draft')
                """,
                (code, oc_number, invoice_number, target_fuero, target_user, target_pc_name, notes, tech)
            )
            new_id = conn.cursor.lastrowid

        return jsonify({"status": "success", "id": new_id, "code": code}), 201
    except Exception as e:
        logging.error("Error en create_build_order: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp_stock.route("/api/build_orders/<int:order_id>", methods=["PATCH", "DELETE"])
def manage_build_order(order_id):
    """PATCH: actualiza metadatos. DELETE: elimina la orden (y restaura stock si estaba completada)."""
    if not check_stock_permission():
        return jsonify({"status": "error", "message": "Acceso denegado."}), 403

    try:
        from utils.auth import current_technician_identity
        tech = current_technician_identity()

        # ── PATCH: editar campos ──────────────────────────────────────────
        if request.method == "PATCH":
            data = request.json or {}
            EDITABLE = {"code", "target_pc_name", "target_user", "target_fuero", "notes", "oc_number", "invoice_number"}
            updates = {k: (v.strip() or None) for k, v in data.items() if k in EDITABLE and isinstance(v, str)}
            if not updates:
                return jsonify({"status": "error", "message": "No hay campos editables."}), 400

            with get_db_connection() as conn:
                bo = conn.execute("SELECT id, code FROM build_orders WHERE id = %s", (order_id,)).fetchone()
                if not bo:
                    return jsonify({"status": "error", "message": "Orden no encontrada."}), 404

                if updates.get("code") and updates["code"] != bo["code"]:
                    dup = conn.execute("SELECT id FROM build_orders WHERE code = %s AND id != %s", (updates["code"], order_id)).fetchone()
                    if dup:
                        return jsonify({"status": "error", "message": f"El código '{updates['code']}' ya existe en otra orden."}), 400

                set_clauses = ", ".join(f"{col} = %s" for col in updates)
                values = list(updates.values()) + [order_id]
                conn.execute(f"UPDATE build_orders SET {set_clauses} WHERE id = %s", values)

                changes_str = ", ".join(f"{k}={v}" for k, v in updates.items())
                conn.execute(
                    """
                    INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    ("Stock", "BUILD_ORDER_UPDATE", bo["code"], changes_str, tech, "BUILD_ORDER", request.remote_addr)
                )

            return jsonify({"status": "success", "updated": updates})


        # ── DELETE: eliminar orden ────────────────────────────────────────
        with get_db_connection() as conn:
            bo = conn.execute(
                "SELECT id, code, status FROM build_orders WHERE id = %s", (order_id,)
            ).fetchone()
            if not bo:
                return jsonify({"status": "error", "message": "Orden no encontrada."}), 404

            restored_count = 0

            if bo["status"] == "completed":
                items = conn.execute(
                    "SELECT serial_number FROM build_order_items WHERE build_order_id = %s",
                    (order_id,)
                ).fetchall()
                for item in items:
                    serial = item["serial_number"]
                    if not serial:
                        continue
                    comp = conn.execute(
                        "SELECT component_type, brand_model FROM components WHERE serial_number = %s",
                        (serial,)
                    ).fetchone()
                    if comp:
                        conn.execute(
                            """
                            UPDATE components
                            SET status = 'Stock', assigned_pc = NULL, assigned_user = NULL,
                                assigned_fuero = NULL, kit_name = NULL
                            WHERE serial_number = %s
                            """,
                            (serial,)
                        )
                        restored_count += 1
                        conn.execute(
                            """
                            INSERT INTO audit_logs
                                (pc_name, field, old_value, new_value, user_name, action_type, ip_address)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                "Stock", "BUILD_ORDER_DISASSEMBLE", bo["code"],
                                f"{comp['component_type']} {comp['brand_model']} (S/N: {serial}) -> Stock",
                                tech, "BUILD_ORDER", request.remote_addr
                            )
                        )

            conn.execute("DELETE FROM build_order_items WHERE build_order_id = %s", (order_id,))
            conn.execute("DELETE FROM build_orders WHERE id = %s", (order_id,))
            conn.execute(
                """
                INSERT INTO audit_logs
                    (pc_name, field, old_value, new_value, user_name, action_type, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    "Stock", "BUILD_ORDER_DELETE", bo["code"],
                    f"Orden {bo['code']} eliminada (previo: {bo['status']}, restaurados: {restored_count})",
                    tech, "BUILD_ORDER", request.remote_addr
                )
            )

        return jsonify({
            "status": "success",
            "message": f"Orden {bo['code']} eliminada correctamente.",
            "restored_to_stock": restored_count
        })

    except Exception as e:
        logging.error("Error en manage_build_order(%s) [%s]: %s", order_id, request.method, e)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp_stock.route("/api/build_orders/<int:order_id>/items", methods=["POST"])
def add_build_order_item(order_id):
    """
    Agrega un componente (por serial) a una Orden de Armado activa.
    Pone el estado de la BO en 'in_progress' si estaba en 'draft'.
    """
    if not check_stock_permission():
        return jsonify({"status": "error", "message": "Acceso denegado."}), 403

    try:
        from utils.auth import current_technician_identity
        tech = current_technician_identity()
        data = request.json or {}
        serial = (data.get("serial_number") or "").strip()
        pc_name = (data.get("pc_name") or "").strip() or None

        if not serial:
            return jsonify({"status": "error", "message": "Falta serial_number."}), 400

        with get_db_connection() as conn:
            # Verificar que la BO existe y no está completada/cancelada
            bo = conn.execute(
                "SELECT id, status FROM build_orders WHERE id = %s", (order_id,)
            ).fetchone()
            if not bo:
                return jsonify({"status": "error", "message": "Orden de Armado no encontrada."}), 404
            if bo["status"] in ("completed", "cancelled"):
                return jsonify({"status": "error", "message": f"La Orden ya está en estado '{bo['status']}'."}), 400

            # Obtener datos del componente
            comp = conn.execute(
                "SELECT component_type, brand_model FROM components WHERE serial_number = %s", (serial,)
            ).fetchone()
            asset_type  = comp["component_type"] if comp else "Desconocido"
            brand_model = comp["brand_model"] if comp else None

            # Insertar ítem
            conn.execute(
                """
                INSERT INTO build_order_items
                    (build_order_id, serial_number, asset_type, brand_model, pc_name, scanned_by)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (order_id, serial, asset_type, brand_model, pc_name, tech)
            )

            # Poner la BO en in_progress si era draft
            if bo["status"] == "draft":
                conn.execute(
                    "UPDATE build_orders SET status = 'in_progress' WHERE id = %s", (order_id,)
                )

        return jsonify({"status": "success", "serial": serial, "asset_type": asset_type})
    except Exception as e:
        logging.error("Error en add_build_order_item(%s): %s", order_id, e)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp_stock.route("/api/build_orders/<int:order_id>/items/<path:serial>", methods=["DELETE"])
def remove_build_order_item(order_id, serial):
    """Quita un componente individual de una Orden de Armado activa (draft/in_progress)."""
    if not check_stock_permission():
        return jsonify({"status": "error", "message": "Acceso denegado."}), 403

    try:
        from utils.auth import current_technician_identity
        tech = current_technician_identity()

        with get_db_connection() as conn:
            bo = conn.execute(
                "SELECT id, code, status FROM build_orders WHERE id = %s", (order_id,)
            ).fetchone()
            if not bo:
                return jsonify({"status": "error", "message": "Orden no encontrada."}), 404
            if bo["status"] in ("completed", "cancelled"):
                return jsonify({"status": "error", "message": f"No se puede modificar una orden '{bo['status']}'."}), 400

            deleted = conn.execute(
                "DELETE FROM build_order_items WHERE build_order_id = %s AND serial_number = %s",
                (order_id, serial)
            )
            if deleted and deleted.rowcount == 0:
                return jsonify({"status": "error", "message": "Ítem no encontrado en la orden."}), 404

            conn.execute(
                """
                INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                ("Stock", "BUILD_ORDER_ITEM_REMOVED", bo["code"], serial, tech, "BUILD_ORDER", request.remote_addr)
            )

        return jsonify({"status": "success", "removed": serial})
    except Exception as e:
        logging.error("Error en remove_build_order_item(%s, %s): %s", order_id, serial, e)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp_stock.route("/api/build_orders/<int:order_id>/complete", methods=["POST"])
def complete_build_order(order_id):
    """
    Completa una Orden de Armado:
    1. Llama a assign_bundle con los seriales de la BO.
    2. Marca la BO como 'completed'.
    3. Marca las PCs afectadas con validation_status = 'pendiente'.
    """
    if not check_stock_permission():
        return jsonify({"status": "error", "message": "Acceso denegado."}), 403

    try:
        from utils.auth import current_technician_identity
        from services.asset_validation import compute_validation_status
        tech = current_technician_identity()
        data = request.json or {}
        pc_name       = (data.get("pc_name") or "").strip() or None
        assigned_user = (data.get("assigned_user") or "").strip() or None
        assigned_fuero = (data.get("assigned_fuero") or "").strip() or None

        with get_db_connection() as conn:
            bo = conn.execute(
                "SELECT id, status, code FROM build_orders WHERE id = %s", (order_id,)
            ).fetchone()
            if not bo:
                return jsonify({"status": "error", "message": "Orden no encontrada."}), 404
            if bo["status"] == "completed":
                return jsonify({"status": "error", "message": "La Orden ya fue completada."}), 400
            if bo["status"] == "cancelled":
                return jsonify({"status": "error", "message": "La Orden fue cancelada."}), 400

            # Obtener ítems
            items = conn.execute(
                "SELECT serial_number, asset_type, brand_model FROM build_order_items WHERE build_order_id = %s",
                (order_id,)
            ).fetchall()

            if not items:
                return jsonify({"status": "error", "message": "La Orden no tiene ítems."}), 400

            serials = [i["serial_number"] for i in items if i.get("serial_number")]

            # Asignar cada componente (reutiliza la lógica de assign_bundle)
            for serial in serials:
                comp = conn.execute(
                    "SELECT * FROM components WHERE serial_number = %s", (serial,)
                ).fetchone()
                if comp:
                    new_status = "Installed" if pc_name else "Asignado"
                    conn.execute(
                        """
                        UPDATE components
                        SET status = %s, assigned_pc = %s, assigned_user = %s, assigned_fuero = %s, kit_name = NULL
                        WHERE serial_number = %s
                        """,
                        (new_status, pc_name or None, assigned_user or None, assigned_fuero or None, serial)
                    )

            # Si hay pc_name y no existe en pcs, crearla
            if pc_name and pc_name not in ("PC Generica",):
                existing = conn.execute(
                    "SELECT pc_name FROM pcs WHERE pc_name = %s", (pc_name,)
                ).fetchone()
                if not existing:
                    conn.execute(
                        """
                        INSERT INTO pcs (pc_name, last_user, fuero, is_active, os_name, validation_status)
                        VALUES (%s, %s, %s, 1, 'Equipo registrado desde Orden de Armado', 'pendiente')
                        """,
                        (pc_name, assigned_user or None, assigned_fuero or "Stock")
                    )
                else:
                    # La PC ya existe: marcar como pendiente de validación
                    conn.execute(
                        "UPDATE pcs SET validation_status = 'pendiente' WHERE pc_name = %s",
                        (pc_name,)
                    )

            # Marcar la BO como completada
            conn.execute(
                """
                UPDATE build_orders
                SET status = 'completed', completed_at = NOW()
                WHERE id = %s
                """,
                (order_id,)
            )

            # Registrar en audit_logs
            conn.execute(
                """
                INSERT INTO audit_logs (pc_name, field, old_value, new_value, user_name, action_type, ip_address)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    pc_name or "Stock",
                    "BUILD_ORDER_COMPLETE",
                    bo["code"],
                    f"{len(serials)} componentes desplegados",
                    tech, "BUILD_ORDER", request.remote_addr
                )
            )

        return jsonify({
            "status": "success",
            "deployed_serials": serials,
            "pc_name": pc_name,
            "validation_status": "pendiente"
        })
    except Exception as e:
        logging.error("Error en complete_build_order(%s): %s", order_id, e)
        return jsonify({"status": "error", "message": str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# SISTEMA PATRIMONIAL — Administración: recalcular validation_status
# ─────────────────────────────────────────────────────────────────────────────

@bp_stock.route("/api/admin/recalculate_validation", methods=["POST"])
def admin_recalculate_validation():
    """
    Endpoint de administración: recalcula el validation_status de todas las PCs activas.
    Solo accesible por superusuarios.
    Útil para la pasada inicial post-migración V49 o después de cargas masivas de activos.
    """
    from utils.auth import current_user
    user = current_user()
    if not user or not user.get("is_superuser"):
        return jsonify({"status": "error", "message": "Acceso exclusivo para administradores."}), 403

    try:
        from services.asset_validation import recalculate_all_validation_statuses
        counts = recalculate_all_validation_statuses()
        return jsonify({"status": "success", "counts": counts})
    except Exception as e:
        logging.error("Error en admin_recalculate_validation: %s", e)
        return jsonify({"status": "error", "message": str(e)}), 500
