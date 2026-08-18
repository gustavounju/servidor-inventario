import unittest
from types import SimpleNamespace
from unittest.mock import patch

from flask import Flask

from blueprints.bp_stock import bp_stock


class FakeResult:
    def __init__(self, rows=None, rowcount=0):
        self.rows = rows or []
        self.rowcount = rowcount

    def fetchone(self):
        return self.rows[0] if self.rows else None

    def fetchall(self):
        return list(self.rows)


class FakeBuildOrderConnection:
    def __init__(self, orders, components, items):
        self.orders = {order["id"]: dict(order) for order in orders}
        self.components = {serial: dict(component) for serial, component in components.items()}
        self.items = [dict(item) for item in items]
        self.audit_logs = []
        self.cursor = SimpleNamespace(lastrowid=None)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def execute(self, sql, params=()):
        normalized = " ".join(sql.split())

        if "FROM build_orders WHERE id = %s" in normalized:
            order = self.orders.get(params[0])
            return FakeResult([dict(order)] if order else [])

        if normalized.startswith("SELECT serial_number FROM build_order_items"):
            order_id = params[0]
            return FakeResult([
                {"serial_number": item["serial_number"]}
                for item in self.items
                if item["build_order_id"] == order_id
            ])

        if "COUNT(*) AS linked_count" in normalized and "FROM components" in normalized:
            order_id = params[0]
            count = sum(1 for component in self.components.values() if component.get("build_order_id") == order_id)
            return FakeResult([{"linked_count": count}])

        if "FROM components WHERE serial_number = %s" in normalized:
            component = self.components.get(params[0])
            return FakeResult([dict(component)] if component else [])

        if normalized.startswith("SELECT id FROM build_order_items"):
            order_id, serial = params
            match = next((item for item in self.items if item["build_order_id"] == order_id and item["serial_number"] == serial), None)
            return FakeResult([dict(match)] if match else [])

        if normalized.startswith("UPDATE components SET status = 'Stock'") and "serial_number = %s" in normalized:
            serial, order_id = params
            component = self.components.get(serial)
            if component and component.get("build_order_id") == order_id and component.get("status") == "Reservado":
                component.update({
                    "status": "Stock",
                    "assigned_pc": None,
                    "assigned_user": None,
                    "assigned_fuero": None,
                    "kit_name": None,
                    "build_order_id": None,
                })
                return FakeResult(rowcount=1)
            return FakeResult(rowcount=0)

        if normalized.startswith("UPDATE components SET status = 'Stock'") and "build_order_id = %s" in normalized:
            order_id = params[0]
            count = 0
            for component in self.components.values():
                if component.get("build_order_id") == order_id and component.get("status") == "Reservado":
                    component.update({
                        "status": "Stock",
                        "assigned_pc": None,
                        "assigned_user": None,
                        "assigned_fuero": None,
                        "kit_name": None,
                        "build_order_id": None,
                    })
                    count += 1
            return FakeResult(rowcount=count)

        if normalized.startswith("UPDATE components SET status = 'Reservado'"):
            order_id, assigned_pc, assigned_user, assigned_fuero, serial = params
            component = self.components.get(serial)
            if component:
                component.update({
                    "status": "Reservado",
                    "build_order_id": order_id,
                    "assigned_pc": assigned_pc or component.get("assigned_pc"),
                    "assigned_user": assigned_user or component.get("assigned_user"),
                    "assigned_fuero": assigned_fuero or component.get("assigned_fuero"),
                })
                return FakeResult(rowcount=1)
            return FakeResult(rowcount=0)

        if normalized.startswith("UPDATE build_orders SET status = 'cancelled'"):
            order_id = params[-1]
            self.orders[order_id]["status"] = "cancelled"
            return FakeResult(rowcount=1)

        if normalized.startswith("UPDATE build_orders SET status = 'in_progress'"):
            self.orders[params[0]]["status"] = "in_progress"
            return FakeResult(rowcount=1)

        if normalized.startswith("INSERT INTO build_order_items"):
            order_id, serial, asset_type, brand_model, pc_name, scanned_by = params
            self.items.append({
                "id": len(self.items) + 1,
                "build_order_id": order_id,
                "serial_number": serial,
                "asset_type": asset_type,
                "brand_model": brand_model,
                "pc_name": pc_name,
                "scanned_by": scanned_by,
            })
            return FakeResult(rowcount=1)

        if normalized.startswith("DELETE FROM build_order_items"):
            order_id = params[0]
            serial = params[1] if len(params) > 1 else None
            before = len(self.items)
            self.items = [
                item for item in self.items
                if not (
                    item["build_order_id"] == order_id
                    and (serial is None or item["serial_number"] == serial)
                )
            ]
            return FakeResult(rowcount=before - len(self.items))

        if normalized.startswith("DELETE FROM build_orders"):
            removed = self.orders.pop(params[0], None)
            return FakeResult(rowcount=1 if removed else 0)

        if normalized.startswith("INSERT INTO audit_logs"):
            self.audit_logs.append(params)
            return FakeResult(rowcount=1)

        if normalized.startswith("UPDATE build_orders SET"):
            order_id = params[-1]
            order = self.orders.get(order_id)
            if order:
                import re
                cols = re.findall(r"(\w+)\s*=\s*%s", normalized)
                for i, col in enumerate(cols):
                    if col != "id":
                        order[col] = params[i]
            return FakeResult(rowcount=1)

        if normalized.startswith("SELECT serial_number FROM components WHERE build_order_id = %s"):
            order_id = params[0]
            return FakeResult([
                {"serial_number": comp["serial_number"]}
                for comp in self.components.values()
                if comp.get("build_order_id") == order_id
            ])

        if normalized.startswith("UPDATE components SET assigned_pc = %s"):
            new_pc, new_user, new_fuero = params[:3]
            serials = params[3:]
            for s in serials:
                if s in self.components:
                    self.components[s].update({
                        "assigned_pc": new_pc,
                        "assigned_user": new_user,
                        "assigned_fuero": new_fuero,
                    })
            return FakeResult(rowcount=len(serials))

        raise AssertionError(f"SQL no contemplado por el fake: {normalized}")


class BuildOrderLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = "test_key"
        self.app.register_blueprint(bp_stock)
        self.client = self.app.test_client()

    def _request_with_connection(self, connection, method, path, json=None):
        with patch("blueprints.bp_stock.check_stock_permission", return_value=True), \
             patch("blueprints.bp_stock.get_db_connection", return_value=connection), \
             patch("utils.auth.current_technician_identity", return_value="TEST-TECH"):
            return self.client.open(path, method=method, json=json)

    def test_completed_order_cannot_be_deleted_and_keeps_assets_unchanged(self):
        connection = FakeBuildOrderConnection(
            orders=[{"id": 1, "code": "BO-1", "status": "completed"}],
            components={"SER-1": {"serial_number": "SER-1", "status": "Installed", "build_order_id": 1, "assigned_pc": "PC-1"}},
            items=[{"id": 1, "build_order_id": 1, "serial_number": "SER-1"}],
        )

        response = self._request_with_connection(connection, "DELETE", "/api/build_orders/1")

        self.assertEqual(response.status_code, 409)
        self.assertIn(1, connection.orders)
        self.assertEqual(connection.components["SER-1"]["status"], "Installed")
        self.assertEqual(connection.components["SER-1"]["assigned_pc"], "PC-1")

    def test_deleting_active_order_only_releases_reservations_still_owned_by_it(self):
        connection = FakeBuildOrderConnection(
            orders=[{"id": 1, "code": "BO-1", "status": "in_progress"}],
            components={
                "SER-OWN": {"serial_number": "SER-OWN", "component_type": "RAM", "brand_model": "8GB", "status": "Reservado", "build_order_id": 1, "assigned_pc": "PC-OLD"},
                "SER-MOVED": {"serial_number": "SER-MOVED", "component_type": "SSD", "brand_model": "500GB", "status": "Installed", "build_order_id": 2, "assigned_pc": "PC-CORRECTA"},
            },
            items=[
                {"id": 1, "build_order_id": 1, "serial_number": "SER-OWN"},
                {"id": 2, "build_order_id": 1, "serial_number": "SER-MOVED"},
            ],
        )

        response = self._request_with_connection(connection, "DELETE", "/api/build_orders/1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["restored_to_stock"], 1)
        self.assertEqual(connection.components["SER-OWN"]["status"], "Stock")
        self.assertIsNone(connection.components["SER-OWN"]["build_order_id"])
        self.assertEqual(connection.components["SER-MOVED"]["status"], "Installed")
        self.assertEqual(connection.components["SER-MOVED"]["build_order_id"], 2)
        self.assertEqual(connection.components["SER-MOVED"]["assigned_pc"], "PC-CORRECTA")

    def test_voiding_duplicate_completed_order_preserves_components_owned_by_correct_order(self):
        connection = FakeBuildOrderConnection(
            orders=[{"id": 1, "code": "BO-DUP", "status": "completed"}],
            components={"SER-1": {"serial_number": "SER-1", "status": "Installed", "build_order_id": 2, "assigned_pc": "PC-CORRECTA"}},
            items=[{"id": 1, "build_order_id": 1, "serial_number": "SER-1"}],
        )

        response = self._request_with_connection(connection, "POST", "/api/build_orders/1/void", json={"reason": "Orden duplicada"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["removed_relations"], 1)
        self.assertEqual(connection.orders[1]["status"], "cancelled")
        self.assertEqual(connection.items, [])
        self.assertEqual(connection.components["SER-1"]["build_order_id"], 2)
        self.assertEqual(connection.components["SER-1"]["assigned_pc"], "PC-CORRECTA")

    def test_voiding_completed_order_is_rejected_while_it_still_owns_components(self):
        connection = FakeBuildOrderConnection(
            orders=[{"id": 1, "code": "BO-1", "status": "completed"}],
            components={"SER-1": {"serial_number": "SER-1", "status": "Installed", "build_order_id": 1, "assigned_pc": "PC-1"}},
            items=[{"id": 1, "build_order_id": 1, "serial_number": "SER-1"}],
        )

        response = self._request_with_connection(connection, "POST", "/api/build_orders/1/void", json={"reason": "Duplicada"})

        self.assertEqual(response.status_code, 409)
        self.assertEqual(connection.orders[1]["status"], "completed")
        self.assertEqual(connection.components["SER-1"]["build_order_id"], 1)

    def test_component_owned_by_another_order_cannot_be_reserved_again(self):
        connection = FakeBuildOrderConnection(
            orders=[{"id": 1, "code": "BO-1", "status": "draft", "target_pc_name": "PC-1", "target_user": None, "target_fuero": None}],
            components={"SER-1": {"serial_number": "SER-1", "component_type": "RAM", "brand_model": "8GB", "status": "Reservado", "build_order_id": 2, "assigned_pc": "PC-2"}},
            items=[],
        )

        response = self._request_with_connection(connection, "POST", "/api/build_orders/1/items", json={"serial_number": "SER-1"})

        self.assertEqual(response.status_code, 409)
        self.assertEqual(connection.items, [])
        self.assertEqual(connection.components["SER-1"]["build_order_id"], 2)

    def test_removing_stale_item_does_not_return_reassigned_component_to_stock(self):
        connection = FakeBuildOrderConnection(
            orders=[{"id": 1, "code": "BO-OLD", "status": "in_progress"}],
            components={"SER-1": {"serial_number": "SER-1", "status": "Installed", "build_order_id": 2, "assigned_pc": "PC-CORRECTA"}},
            items=[{"id": 1, "build_order_id": 1, "serial_number": "SER-1"}],
        )

        response = self._request_with_connection(connection, "DELETE", "/api/build_orders/1/items/SER-1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(connection.items, [])
        self.assertEqual(connection.components["SER-1"]["status"], "Installed")
        self.assertEqual(connection.components["SER-1"]["build_order_id"], 2)
        self.assertEqual(connection.components["SER-1"]["assigned_pc"], "PC-CORRECTA")


    def test_editing_completed_order_updates_linked_components(self):
        connection = FakeBuildOrderConnection(
            orders=[{"id": 1, "code": "BO-1", "status": "completed", "target_pc_name": "PC-ERRADA", "target_user": "USER-ERRADO", "target_fuero": "FUERO-ERRADO"}],
            components={"SER-1": {"serial_number": "SER-1", "status": "Installed", "build_order_id": 1, "assigned_pc": "PC-ERRADA", "assigned_user": "USER-ERRADO", "assigned_fuero": "FUERO-ERRADO"}},
            items=[{"id": 1, "build_order_id": 1, "serial_number": "SER-1"}],
        )

        response = self._request_with_connection(
            connection,
            "PATCH",
            "/api/build_orders/1",
            json={
                "code": "BO-1",
                "target_pc_name": "PC-CORRECTA",
                "target_user": "USER-CORRECTO",
                "target_fuero": "FUERO-CORRECTO"
            }
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(connection.orders[1]["target_pc_name"], "PC-CORRECTA")
        self.assertEqual(connection.orders[1]["target_user"], "USER-CORRECTO")
        self.assertEqual(connection.orders[1]["target_fuero"], "FUERO-CORRECTO")
        self.assertEqual(connection.components["SER-1"]["assigned_pc"], "PC-CORRECTA")
        self.assertEqual(connection.components["SER-1"]["assigned_user"], "USER-CORRECTO")
        self.assertEqual(connection.components["SER-1"]["assigned_fuero"], "FUERO-CORRECTO")


if __name__ == "__main__":
    unittest.main()
