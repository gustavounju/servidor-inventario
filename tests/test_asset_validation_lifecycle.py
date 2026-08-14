import json

from services.asset_validation import (
    compute_validation_status,
    resolve_build_order_action,
    resolve_effective_validation_status,
)


class _Result:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row


class _ValidationConnection:
    def __init__(self, assigned_component, pc_data, build_order_item=None):
        self.assigned_component = assigned_component
        self.pc_data = pc_data
        self.build_order_item = build_order_item

    def execute(self, query, params=None):
        normalized = " ".join(str(query).split())
        if "FROM components" in normalized:
            return _Result(self.assigned_component)
        if "FROM build_order_items" in normalized:
            return _Result(self.build_order_item)
        if "FROM pcs" in normalized:
            return _Result(self.pc_data)
        raise AssertionError(f"Consulta no esperada: {normalized}")


def test_repeated_report_keeps_validated_twin_validated():
    telemetry = {
        "Sistema": {"Procesador": "Intel Core i5-10400", "RAM (GB)": 16},
        "Motherboard_Model": "ASUS PRIME H510M",
    }
    conn = _ValidationConnection(
        assigned_component={
            "id": 8,
            "component_type": "Procesador",
            "brand_model": "Intel Core i5-10400",
            "serial_number": "CPU-008",
        },
        pc_data={
            "processor": "Intel Core i5-10400",
            "motherboard_model": "ASUS PRIME H510M",
            "ram_gb": 16,
            "disk_models": "Kingston 480GB",
            "last_report": "2026-08-14 12:00:00",
            "telemetry_snapshot": json.dumps(telemetry),
            "full_json_data": None,
            "validation_status": "validado",
        },
    )

    assert compute_validation_status("PC-VALIDADA", conn) == "validado"


def test_unexpected_validation_error_does_not_erase_existing_valid_state():
    class _FailingConnection:
        def execute(self, query, params=None):
            normalized = " ".join(str(query).split())
            if "FROM pcs" in normalized:
                return _Result({"validation_status": "validado"})
            raise RuntimeError("fallo transitorio")

    assert compute_validation_status("PC-VALIDADA", _FailingConnection()) == "validado"


def test_build_order_action_only_creates_when_there_is_no_twin():
    assert resolve_build_order_action(
        "sin_gemelo", linked_bo=None, has_discrepancies=True, has_official_components=False
    ) == "create"
    assert resolve_build_order_action(
        "sin_gemelo", linked_bo=None, has_discrepancies=True, has_official_components=True
    ) == "history"
    assert resolve_build_order_action("validado", linked_bo=None, has_discrepancies=False) == "history"
    assert resolve_build_order_action("discrepancia", linked_bo=None, has_discrepancies=True) == "history"


def test_build_order_action_reuses_existing_order_only_for_real_changes():
    linked_bo = {"id": 12, "code": "BO-2026-0012"}

    assert resolve_build_order_action("validado", linked_bo, has_discrepancies=False) == "history"
    assert resolve_build_order_action("discrepancia", linked_bo, has_discrepancies=True) == "update"


def test_stale_without_twin_status_is_derived_from_existing_patrimony():
    assert resolve_effective_validation_status(
        "sin_gemelo", has_official_components=True, has_discrepancies=False
    ) == "validado"
    assert resolve_effective_validation_status(
        "sin_gemelo", has_official_components=True, has_discrepancies=True
    ) == "discrepancia"
    assert resolve_effective_validation_status(
        "sin_gemelo", has_official_components=False, has_discrepancies=True
    ) == "sin_gemelo"
