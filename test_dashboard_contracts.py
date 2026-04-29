import unittest

from services.dashboard_contract import normalize_alerta, sanitize_sort_column, sanitize_sort_direction
from services.dashboard_overview import _build_fuero_tree, _split_fuero_path


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

    def test_build_fuero_tree_splits_location_path(self):
        tree = _build_fuero_tree([
            {"pc_name": "PC-01", "fuero": "Tribunal de Familia - sala 4 - Vocalia 07"},
            {"pc_name": "PC-02", "fuero": "Tribunal de Familia - sala 4 - Vocalia 08"},
        ])

        self.assertEqual(tree[0]["name"], "Tribunal de Familia")
        self.assertEqual(tree[0]["count"], 2)
        self.assertEqual(tree[0]["children"][0]["name"], "Sala 4")
        vocalias = tree[0]["children"][0]["children"]
        self.assertEqual([node["name"] for node in vocalias], ["Vocalia 7", "Vocalia 8"])
        self.assertEqual(vocalias[0]["pcs"][0]["pc_name"], "PC-01")

    def test_split_fuero_path_infers_unseparated_civil_secretaria(self):
        self.assertEqual(
            _split_fuero_path("Juzgado civil y Comercial Sala IV secretaria 15"),
            ["Juzgado civil y Comercial", "Sala IV", "Secretaria 15"],
        )

    def test_split_fuero_path_parses_compact_jcc_code(self):
        self.assertEqual(
            _split_fuero_path("JCC8SEC1500003"),
            ["Juzgado Civil y Comercial N°8", "Secretaria 15"],
        )

    def test_split_fuero_path_parses_compact_ccyc_code(self):
        self.assertEqual(
            _split_fuero_path("CCYCSIV1100011"),
            ["Cámara Civil y Comercial", "Sala IV", "Vocalia 11"],
        )

    def test_build_fuero_tree_uses_pc_name_when_fuero_is_generic(self):
        tree = _build_fuero_tree([
            {"pc_name": "JCC9SEC1700004", "fuero": "Juzgado Civil y Comercial"},
            {"pc_name": "CCYCSIV1100011", "fuero": "Cámara Civil y Comercial Sala IV"},
        ])

        self.assertEqual(tree[0]["name"], "Cámara Civil y Comercial")
        self.assertEqual(tree[0]["children"][0]["name"], "Sala IV")
        self.assertEqual(tree[0]["children"][0]["children"][0]["name"], "Vocalia 11")
        self.assertEqual(tree[1]["name"], "Juzgado Civil y Comercial N°9")
        self.assertEqual(tree[1]["children"][0]["name"], "Secretaria 17")
    def test_build_fuero_tree_unifies_same_jcc_with_multiple_secretarias(self):
        tree = _build_fuero_tree([
            {"pc_name": "JCC9SEC1700004", "fuero": "Juzgado Civil y Comercial"},
            {"pc_name": "JCC9SEC1800004", "fuero": "Juzgado civil y Comercial NÂ°9 Secretaria 18"},
        ])

        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]["name"], "Juzgado Civil y Comercial N°9")
        self.assertEqual([child["name"] for child in tree[0]["children"]], ["Secretaria 17", "Secretaria 18"])
    def test_build_fuero_tree_splits_tts_vocalias(self):
        tree = _build_fuero_tree([
            {"pc_name": "TTSIVVOC100002", "fuero": "Tribunal de Trabajo Sala IV"},
            {"pc_name": "TTSIVVOC110003", "fuero": "Tribunal de Trabajo Sala IV"},
        ])

        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]["name"], "Tribunal de Trabajo")
        self.assertEqual(tree[0]["children"][0]["name"], "Sala IV")
        self.assertEqual([child["name"] for child in tree[0]["children"][0]["children"]], ["Vocalia 10", "Vocalia 11"])


if __name__ == "__main__":
    unittest.main()
