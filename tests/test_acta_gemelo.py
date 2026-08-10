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
            self.assertIn("Maria Gonzalez", html)
            self.assertIn("encabezado_poder_judicial.png", html)

if __name__ == "__main__":
    unittest.main()
