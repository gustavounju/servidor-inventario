import unittest
from unittest.mock import patch

class ActaGemeloValidadoTests(unittest.TestCase):

    def test_filter_ignore_devices_removes_usb_card_readers(self):
        from services.asset_validation import filter_ignore_devices
        raw_telemetry = (
            "Generic USB SD Reader USB Device (0GB) [SN: 058F63326330] (0GB) | "
            "Generic USB MS Reader USB Device (0GB) [SN: 058F63326331] | "
            "ADATA SU630 (447GB) [SN: 11EF07211CF000344575] | "
            "TOSHIBA DT01ACA050 (466GB) [SN: 27D009EBS]"
        )
        cleaned = filter_ignore_devices(raw_telemetry)
        self.assertNotIn("Generic USB SD Reader", cleaned)
        self.assertNotIn("Generic USB MS Reader", cleaned)
        self.assertIn("ADATA SU630", cleaned)
        self.assertIn("TOSHIBA DT01ACA050", cleaned)

    @patch("blueprints.bp_dashboard.get_pc_detail_context")
    def test_acta_gemelo_validado_requires_valid_status(self, mock_get_context):
        from flask import Flask
        from blueprints.bp_dashboard import bp_dashboard

        app = Flask(__name__, template_folder="../templates")
        app.secret_key = "test_secret"
        app.register_blueprint(bp_dashboard)

        # Mock context where validation_status is 'pendiente'
        mock_get_context.return_value = {
            "pc": {
                "pc_name": "PC-TEST",
                "validation_status": "pendiente",
                "last_user": "Juan Perez",
                "fuero": "Juzgado Civil"
            },
            "validation_comparison": []
        }

        with app.test_client() as client:
            response = client.get("/pc/PC-TEST/acta_gemelo_validado", follow_redirects=False)
            # Expect redirect 302 to pc_detail page
            self.assertEqual(response.status_code, 302)
            self.assertIn("/pc/PC-TEST", response.headers.get("Location", ""))

    @patch("blueprints.bp_dashboard.get_pc_detail_context")
    def test_acta_gemelo_validado_renders_when_valid(self, mock_get_context):
        from flask import Flask
        from blueprints.bp_dashboard import bp_dashboard

        app = Flask(__name__, template_folder="../templates")
        app.secret_key = "test_secret"
        app.register_blueprint(bp_dashboard)

        # Mock context where validation_status is 'validado'
        mock_get_context.return_value = {
            "pc": {
                "pc_name": "PC-VALIDADA",
                "validation_status": "validado",
                "last_user": "Maria Gonzalez",
                "fuero": "Juzgado de Instruccion",
                "os_name": "Windows 11 Pro",
                "processor": "Intel Core i5-12400",
                "ram_gb": 16,
                "motherboard_model": "ASUS PRIME B660M",
                "disk_models": "KINGSTON SNV2S500G"
            },
            "validation_comparison": [{"match": True}],
            "all_unified_components": [],
            "monitors_detail": []
        }

        with app.test_client() as client:
            response = client.get("/pc/PC-VALIDADA/acta_gemelo_validado")
            self.assertEqual(response.status_code, 200)
            html = response.get_data(as_text=True)
            self.assertIn("ACTA DE ENTREGA Y RECEPCIÓN DE EQUIPAMIENTO INFORMÁTICO", html)
            self.assertIn("PC-VALIDADA", html)
            self.assertIn("Gabinete (Chasis)", html)
            self.assertIn("Fuente de Poder", html)
            self.assertIn("Técnico", html)
            self.assertIn("encabezado_poder_judicial.png", html)

    @patch("blueprints.bp_tasks.get_db_connection")
    def test_homologar_telemetria_resets_alerta_duplicado(self, mock_get_db):
        from flask import Flask
        from blueprints.bp_tasks import bp_tasks
        import json

        app = Flask(__name__)
        app.secret_key = "test_secret"
        app.register_blueprint(bp_tasks)

        mock_conn = mock_get_db.return_value.__enter__.return_value
        fake_pc = {
            "telemetry_snapshot": json.dumps({
                "Sistema": {"Procesador": "Intel i7", "RAM (GB)": 16},
                "Motherboard_Model": "ASUS B550",
                "Disk_Models": "Samsung SSD 1TB"
            }),
            "processor": "Intel i3",
            "ram_gb": 8,
            "motherboard_model": "Gigabyte A320",
            "disk_models": "HDD 500GB",
            "last_user": "Juan",
            "fuero": "Civil"
        }
        
        class MockResult:
            def fetchone(self):
                return None
            def fetchall(self):
                return []

        def side_effect(query, *args, **kwargs):
            if "FROM pcs WHERE pc_name" in str(query):
                res = MockResult()
                res.fetchone = lambda: fake_pc
                return res
            return MockResult()

        mock_conn.execute.side_effect = side_effect

        with app.test_client() as client:
            res = client.post("/api/intervenciones/homologar_telemetria", json={"pc_name": "PC-DUPLICADA"})
            self.assertEqual(res.status_code, 200)
            
            # Verificar que conn.execute fue llamado actualizando alerta_nombre_duplicado = 0
            executed_queries = [str(call[0][0]) for call in mock_conn.execute.call_args_list]
            update_query = next((q for q in executed_queries if "UPDATE pcs" in q), "")
            self.assertIn("alerta_nombre_duplicado = 0", update_query)
            self.assertIn("validation_status = 'validado'", update_query)

    @patch("blueprints.bp_dashboard.get_db_connection")
    def test_create_bo_from_telemetry_saves_remito_and_oc(self, mock_get_db):
        from flask import Flask
        from blueprints.bp_dashboard import bp_dashboard

        app = Flask(__name__)
        app.secret_key = "test_secret"
        app.register_blueprint(bp_dashboard)

        mock_conn = mock_get_db.return_value.__enter__.return_value
        fake_pc = {"pc_name": "PC-TEST", "last_user": "Jose", "fuero": "Familia"}

        class MockResult:
            def fetchone(self):
                return None
            def fetchall(self):
                return []

        def side_effect(query, *args, **kwargs):
            if "FROM pcs WHERE pc_name" in str(query):
                res = MockResult()
                res.fetchone = lambda: fake_pc
                return res
            if "FROM build_orders WHERE target_pc_name" in str(query):
                res = MockResult()
                res.fetchone = lambda: None
                return res
            if "COUNT(*) as cnt FROM build_orders" in str(query):
                res = MockResult()
                res.fetchone = lambda: {"cnt": 5}
                return res
            return MockResult()

        mock_conn.execute.side_effect = side_effect

        with app.test_client() as client:
            res = client.post(
                "/pc/PC-TEST/create_bo_from_telemetry",
                data={
                    "target_user": "Jose Zambrano",
                    "target_fuero": "Tribunal de Familias",
                    "invoice_number": "REM-2026-999",
                    "oc_number": "OC-2026-777",
                    "notes": "Prueba remito y OC",
                    "comp_selected": ["0"],
                    "comp_type": ["Procesador"],
                    "comp_model": ["AMD Ryzen 3"],
                    "comp_serial": ["SN12345"]
                },
                follow_redirects=False
            )
            self.assertEqual(res.status_code, 302)

            executed_queries = [str(call[0][0]) for call in mock_conn.execute.call_args_list]
            insert_bo_query = next((q for q in executed_queries if "INSERT INTO build_orders" in q), "")
            self.assertIn("oc_number", insert_bo_query)
            self.assertIn("invoice_number", insert_bo_query)

            # Verificar que los argumentos enviados a INSERT INTO build_orders incluyen REM-2026-999 y OC-2026-777
            bo_call_args = next(call[0][1] for call in mock_conn.execute.call_args_list if "INSERT INTO build_orders" in str(call[0][0]))
            self.assertIn("OC-2026-777", bo_call_args)
            self.assertIn("REM-2026-999", bo_call_args)

if __name__ == "__main__":
    unittest.main()

