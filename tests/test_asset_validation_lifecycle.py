import json

from services.asset_validation import (
    compute_validation_status,
    filter_ignore_devices,
    get_pc_validation_comparison,
    resolve_build_order_action,
    resolve_effective_validation_status,
)


class _Result:
    def __init__(self, row=None):
        self._row = row

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._row or []


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


def test_filter_ignore_devices_returns_empty_when_every_disk_is_removable():
    assert filter_ignore_devices("Generic USB SD Reader USB Device (0GB)") == ""


def test_validated_legacy_twin_uses_pc_record_when_component_rows_are_incomplete():
    telemetry = {
        "Sistema": {"Procesador": "Intel Core i5-10400", "RAM (GB)": 16},
        "Motherboard_Model": "ASUS PRIME H510M",
        "Disk_Models": "ADATA SU630 (447GB) [SN: SSD-001]",
    }
    pc = {
        "processor": "Intel Core i5-10400",
        "motherboard_model": "ASUS PRIME H510M",
        "ram_gb": 16,
        "disk_models": "ADATA SU630 (447GB) [SN: SSD-001]",
        "telemetry_snapshot": json.dumps(telemetry),
        "full_json_data": None,
    }

    class _ComparisonConnection:
        def execute(self, query, params=None):
            assert "FROM pcs" in " ".join(str(query).split())
            return _Result(pc)

    comparison = get_pc_validation_comparison(
        "SISTEMAS-105",
        _ComparisonConnection(),
        unified_components=[
            {
                "component_type": "Gabinete",
                "brand_model": "PC de escritorio",
                "serial_number": "PC-105",
            },
            {
                "component_type": "Disco Rígido / SSD",
                "brand_model": "Generic USB SD Reader USB Device (0GB)",
                "serial_number": "058F63326330",
            },
        ],
    )

    core_rows = comparison[:4]
    assert all(row["match"] for row in core_rows)
    disk_row = next(row for row in core_rows if row["component"] == "Almacenamiento (Disco)")
    assert "Generic USB" not in disk_row["registered"]
