import os
import hmac
import logging
from functools import wraps
from flask import Blueprint, request, jsonify, current_app

from database.db_core import get_db_connection
from utils.extensions import limiter
from utils.auth import require_api_scope, SCOPE_EXTERNAL_READ_PO, SCOPE_EXTERNAL_READ_REMITOS

bp_external_api = Blueprint('external_api', __name__, url_prefix='/api/external')

logger = logging.getLogger(__name__)


@bp_external_api.route('/purchase-orders/<oc_number>', methods=['GET'])
@require_api_scope(SCOPE_EXTERNAL_READ_PO)
@limiter.limit("60 per minute")
def get_purchase_order(oc_number):
    """
    Consulta los detalles de una Orden de Compra por su número.
    Retorna los remitos asociados, productos agrupados, cantidades y números de serie.
    """
    clean_oc = (oc_number or "").strip()
    if not clean_oc:
        return jsonify({"status": "error", "message": "El número de orden de compra es obligatorio"}), 400

    try:
        with get_db_connection() as conn:
            query = """
                SELECT id, serial_number, component_type, brand_model, status,
                       supplier, invoice_number, oc_number, created_at
                FROM components
                WHERE LOWER(TRIM(oc_number)) = LOWER(TRIM(%s))
                ORDER BY created_at ASC, id ASC
            """
            rows = conn.execute(query, (clean_oc,)).fetchall()

        if not rows:
            return jsonify({
                "status": "error",
                "message": f"Orden de compra '{clean_oc}' no encontrada en el inventario"
            }), 404

        # Agrupar por remito (invoice_number)
        remitos_map = {}
        total_items = len(rows)
        canonical_oc = rows[0]["oc_number"] or clean_oc

        for row in rows:
            inv = (row["invoice_number"] or "SIN_REMITO").strip()
            if inv not in remitos_map:
                remitos_map[inv] = {
                    "invoice_number": inv if inv != "SIN_REMITO" else None,
                    "supplier": row["supplier"] or "No especificado",
                    "received_at": row["created_at"].strftime("%Y-%m-%d") if row["created_at"] else None,
                    "items_map": {}
                }

            item_key = (
                (row["component_type"] or "Desconocido").strip(),
                (row["brand_model"] or "Sin modelo").strip()
            )

            remito_entry = remitos_map[inv]
            if item_key not in remito_entry["items_map"]:
                remito_entry["items_map"][item_key] = {
                    "component_type": item_key[0],
                    "brand_model": item_key[1],
                    "quantity": 0,
                    "serials": []
                }

            prod_entry = remito_entry["items_map"][item_key]
            prod_entry["quantity"] += 1
            if row["serial_number"]:
                prod_entry["serials"].append(row["serial_number"])

        # Estructurar respuesta final
        remitos_list = []
        for inv_key, rdata in remitos_map.items():
            remitos_list.append({
                "invoice_number": rdata["invoice_number"],
                "supplier": rdata["supplier"],
                "received_at": rdata["received_at"],
                "items": list(rdata["items_map"].values())
            })

        logger.info(f"API Contable: Consulta exitosa de OC '{canonical_oc}' ({total_items} ítems)")

        return jsonify({
            "status": "success",
            "oc_number": canonical_oc,
            "total_items": total_items,
            "total_remitos": len(remitos_list),
            "remitos": remitos_list
        }), 200

    except Exception as e:
        logger.error(f"API Contable Error en get_purchase_order('{clean_oc}'): {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Error interno del servidor al consultar la Orden de Compra"}), 500


@bp_external_api.route('/purchase-orders', methods=['GET'])
@require_api_scope(SCOPE_EXTERNAL_READ_PO)
@limiter.limit("60 per minute")
def list_purchase_orders():
    """
    Listado paginado y filtrable de Órdenes de Compra.
    Parámetros opcionales:
      - since: Fecha inicio (YYYY-MM-DD)
      - until: Fecha fin (YYYY-MM-DD)
      - page: Número de página (por defecto 1)
      - per_page: Elementos por página (por defecto 50, máx 200)
    """
    since_date = request.args.get('since', '').strip()
    until_date = request.args.get('until', '').strip()
    
    try:
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(200, max(1, int(request.args.get('per_page', 50))))
    except ValueError:
        return jsonify({"status": "error", "message": "Parámetros de paginación inválidos"}), 400

    where_clauses = ["oc_number IS NOT NULL AND TRIM(oc_number) != ''"]
    params = []

    if since_date:
        where_clauses.append("DATE(created_at) >= %s")
        params.append(since_date)
    if until_date:
        where_clauses.append("DATE(created_at) <= %s")
        params.append(until_date)

    where_str = " WHERE " + " AND ".join(where_clauses)

    try:
        with get_db_connection() as conn:
            # Contar total de OCs distintas
            count_sql = f"SELECT COUNT(DISTINCT oc_number) as total FROM components {where_str}"
            total_ocs = conn.execute(count_sql, params).fetchone()["total"]

            offset = (page - 1) * per_page

            # Obtener las OCs distintas para la página actual
            ocs_sql = f"""
                SELECT oc_number, MAX(created_at) as last_received_at, COUNT(*) as total_items, COUNT(DISTINCT invoice_number) as remitos_count
                FROM components
                {where_str}
                GROUP BY oc_number
                ORDER BY last_received_at DESC
                LIMIT %s OFFSET %s
            """
            oc_rows = conn.execute(ocs_sql, params + [per_page, offset]).fetchall()

        results = []
        for oc in oc_rows:
            results.append({
                "oc_number": oc["oc_number"],
                "last_received_at": oc["last_received_at"].strftime("%Y-%m-%d") if oc["last_received_at"] else None,
                "total_items": oc["total_items"],
                "remitos_count": oc["remitos_count"]
            })

        return jsonify({
            "status": "success",
            "page": page,
            "per_page": per_page,
            "total_purchase_orders": total_ocs,
            "total_pages": (total_ocs + per_page - 1) // per_page if total_ocs > 0 else 1,
            "purchase_orders": results
        }), 200

    except Exception as e:
        logger.error(f"API Contable Error en list_purchase_orders: {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Error interno del servidor al listar Órdenes de Compra"}), 500


@bp_external_api.route('/remitos/<invoice_number>', methods=['GET'])
@require_api_scope(SCOPE_EXTERNAL_READ_REMITOS)
@limiter.limit("60 per minute")
def get_remito(invoice_number):
    """
    Consulta los detalles de un Remito específico por su número.
    """
    clean_remito = (invoice_number or "").strip()
    if not clean_remito:
        return jsonify({"status": "error", "message": "El número de remito es obligatorio"}), 400

    try:
        with get_db_connection() as conn:
            query = """
                SELECT id, serial_number, component_type, brand_model, status,
                       supplier, invoice_number, oc_number, created_at
                FROM components
                WHERE LOWER(TRIM(invoice_number)) = LOWER(TRIM(%s))
                ORDER BY created_at ASC, id ASC
            """
            rows = conn.execute(query, (clean_remito,)).fetchall()

        if not rows:
            return jsonify({
                "status": "error",
                "message": f"Remito '{clean_remito}' no encontrado en el inventario"
            }), 404

        canonical_inv = rows[0]["invoice_number"] or clean_remito
        supplier = rows[0]["supplier"] or "No especificado"
        oc_number = rows[0]["oc_number"] or None
        received_at = rows[0]["created_at"].strftime("%Y-%m-%d") if rows[0]["created_at"] else None

        items_map = {}
        for row in rows:
            item_key = (
                (row["component_type"] or "Desconocido").strip(),
                (row["brand_model"] or "Sin modelo").strip()
            )

            if item_key not in items_map:
                items_map[item_key] = {
                    "component_type": item_key[0],
                    "brand_model": item_key[1],
                    "quantity": 0,
                    "serials": []
                }

            entry = items_map[item_key]
            entry["quantity"] += 1
            if row["serial_number"]:
                entry["serials"].append(row["serial_number"])

        logger.info(f"API Contable: Consulta exitosa de Remito '{canonical_inv}' ({len(rows)} ítems)")

        return jsonify({
            "status": "success",
            "invoice_number": canonical_inv,
            "oc_number": oc_number,
            "supplier": supplier,
            "received_at": received_at,
            "total_items": len(rows),
            "items": list(items_map.values())
        }), 200

    except Exception as e:
        logger.error(f"API Contable Error en get_remito('{clean_remito}'): {e}", exc_info=True)
        return jsonify({"status": "error", "message": "Error interno del servidor al consultar el remito"}), 500
