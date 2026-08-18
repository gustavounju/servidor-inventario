from unittest.mock import patch

from flask import Flask

from blueprints.bp_stock import bp_stock, build_orders_view


class _FakeResult:
    def __init__(self, rows=None):
        self.rows = rows or []

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)


class _BuildOrdersViewConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, sql, params=()):
        normalized = " ".join(str(sql).split())

        if "SELECT pc_name, last_user, fuero FROM pcs WHERE is_active = 1" in normalized:
            return _FakeResult(
                [
                    {"pc_name": "PC-VALIDADA", "last_user": "Ana Perez", "fuero": "Civil"},
                    {"pc_name": "PC-OTRA", "last_user": "Bruno Diaz", "fuero": "Penal"},
                ]
            )
        if "SELECT username, COALESCE(NULLIF(TRIM(real_name), ''), username) as real_name, fuero FROM ad_users" in normalized:
            return _FakeResult([])
        if normalized == "SELECT username, real_name FROM ad_users":
            return _FakeResult([])
        if "SELECT serial_number, component_type, brand_model, supplier, lifecycle_status, status, build_order_id FROM components" in normalized:
            return _FakeResult([])
        if "SELECT LOWER(pc_name) as pc_key, pc_name, last_user, fuero, validation_status, is_active FROM pcs" in normalized:
            return _FakeResult(
                [
                    {
                        "pc_key": "pc-validada",
                        "pc_name": "PC-VALIDADA",
                        "last_user": "Ana Perez",
                        "fuero": "Civil",
                        "validation_status": "validado",
                        "is_active": 1,
                    },
                    {
                        "pc_key": "pc-otra",
                        "pc_name": "PC-OTRA",
                        "last_user": "Bruno Diaz",
                        "fuero": "Penal",
                        "validation_status": "pendiente",
                        "is_active": 1,
                    },
                ]
            )
        if "FROM build_orders bo" in normalized:
            return _FakeResult(
                [
                    {
                        "id": 1,
                        "code": "BO-2026-001",
                        "status": "draft",
                        "oc_number": None,
                        "invoice_number": None,
                        "target_fuero": "Civil",
                        "target_user": "Ana Perez",
                        "target_pc_name": "",
                        "notes": "Sin PC concreta",
                        "created_by": "tecnico",
                        "completed_at": None,
                        "created_at": None,
                    }
                ]
            )
        if "FROM build_order_items WHERE build_order_id = %s" in normalized:
            return _FakeResult([])
        if "FROM components WHERE build_order_id = %s" in normalized:
            return _FakeResult([])
        if "SELECT DISTINCT fuero_label as fuero FROM fuero_mappings WHERE is_active = 1" in normalized:
            return _FakeResult([])
        if "SELECT DISTINCT invoice_number FROM components" in normalized:
            return _FakeResult([])
        if "SELECT DISTINCT oc_number FROM components" in normalized:
            return _FakeResult([])
        raise AssertionError(f"SQL no contemplado por el fake: {normalized}")


def test_build_orders_view_does_not_infer_validated_status_from_user_or_fuero():
    app = Flask(__name__)
    app.secret_key = "test_key"
    app.register_blueprint(bp_stock)

    with app.test_request_context("/build_orders"):
        with patch("blueprints.bp_stock.get_db_connection", return_value=_BuildOrdersViewConnection()), patch(
            "blueprints.bp_stock.render_template",
            side_effect=lambda _template, **context: context,
        ):
            context = build_orders_view()

    order = context["build_orders"][0]
    assert order["validation_status"] is None
    assert order["target_pc_name"] == ""
    assert context["validados_count"] == 0
    assert context["pendientes_count"] == 1
