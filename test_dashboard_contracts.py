import unittest

from services.dashboard_contract import normalize_alerta, sanitize_sort_column, sanitize_sort_direction


class DashboardContractTests(unittest.TestCase):
    def test_normalize_alerta_keeps_canonical_value(self):
        self.assertEqual(normalize_alerta("sin_impresora_inventario"), "sin_impresora_inventario")

    def test_normalize_alerta_maps_legacy_aliases(self):
        self.assertEqual(normalize_alerta("sinimp"), "sin_impresora_alerta")
        self.assertEqual(normalize_alerta("sin_impresora"), "sin_impresora_inventario")

    def test_sanitize_sort_column_falls_back_to_pc_name(self):
        self.assertEqual(sanitize_sort_column("no_existe"), "p.pc_name")

    def test_sanitize_sort_direction(self):
        self.assertEqual(sanitize_sort_direction("desc"), "DESC")
        self.assertEqual(sanitize_sort_direction("asc"), "ASC")
        self.assertEqual(sanitize_sort_direction("cualquier cosa"), "ASC")


if __name__ == "__main__":
    unittest.main()
