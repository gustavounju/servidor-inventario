import unittest
from unittest.mock import MagicMock, patch
from flask import Flask
from blueprints.bp_stock import bp_stock


class StockReportFilterTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__, template_folder="../templates")
        self.app.secret_key = "test_key"
        self.app.register_blueprint(bp_stock)
        self.client = self.app.test_client()

    @patch("blueprints.bp_stock.get_db_connection")
    def test_stock_report_pdf_ignores_todos_filters(self, mock_get_db):
        mock_conn = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchall.return_value = []

        response = self.client.get("/stock/report/pdf?component_type=todos&remito=todos&oc=todos&assigned_pc=todos&status=todos&fuero=todos")
        self.assertEqual(response.status_code, 200)

        # Inspect the SQL executed
        args, _ = mock_conn.execute.call_args
        sql = args[0]
        params = args[1] if len(args) > 1 else []

        self.assertNotIn("c.invoice_number LIKE", sql)
        self.assertNotIn("c.oc_number LIKE", sql)
        self.assertNotIn("c.assigned_pc LIKE", sql)
        self.assertEqual(params, [])

    @patch("blueprints.bp_stock.get_db_connection")
    def test_stock_report_pdf_applies_specific_filters(self, mock_get_db):
        mock_conn = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value.fetchall.return_value = []

        response = self.client.get("/stock/report/pdf?remito=REM-001&oc=OC-100&assigned_pc=PC-TEST")
        self.assertEqual(response.status_code, 200)

        args, _ = mock_conn.execute.call_args
        sql = args[0]
        params = args[1]

        self.assertIn("c.invoice_number LIKE", sql)
        self.assertIn("c.oc_number LIKE", sql)
        self.assertIn("c.assigned_pc LIKE", sql)
        self.assertIn("%REM-001%", params)
        self.assertIn("%OC-100%", params)
        self.assertIn("%PC-TEST%", params)


if __name__ == "__main__":
    unittest.main()
