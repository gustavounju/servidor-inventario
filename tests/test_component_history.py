import unittest
from unittest.mock import MagicMock, patch
from flask import Flask
from blueprints.bp_stock import bp_stock


class ComponentHistoryTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__, template_folder="../templates")
        self.app.secret_key = "test_key"
        self.app.register_blueprint(bp_stock)
        self.client = self.app.test_client()

    @patch("utils.auth.is_authenticated")
    def test_get_history_unauthorized(self, mock_is_auth):
        mock_is_auth.return_value = False
        response = self.client.get("/api/components/INT-RAM-1234/history")
        self.assertEqual(response.status_code, 401)
        self.assertIn("No autenticado", response.get_json()["message"])

    @patch("utils.auth.is_authenticated")
    @patch("blueprints.bp_stock.get_db_connection")
    def test_get_history_empty_serial(self, mock_get_db, mock_is_auth):
        mock_is_auth.return_value = True
        response = self.client.get("/api/components/%20/history")
        self.assertEqual(response.status_code, 400)
        self.assertIn("Serial no válido", response.get_json()["message"])

    @patch("utils.auth.is_authenticated")
    @patch("blueprints.bp_stock.get_db_connection")
    def test_get_history_success(self, mock_get_db, mock_is_auth):
        mock_is_auth.return_value = True
        mock_conn = MagicMock()
        mock_get_db.return_value.__enter__.return_value = mock_conn
        
        import datetime
        mock_timestamp = datetime.datetime(2026, 8, 4, 10, 30)
        
        mock_conn.execute.return_value.fetchall.return_value = [
            {
                "pc_name": "PC-TEST",
                "field": "Memoria RAM Asignado",
                "old_value": "Stock",
                "new_value": "Crucial 8GB (SN: 1234)",
                "user_name": "tecnico1",
                "action_type": "GESTION_INFRAESTRUCTURA",
                "timestamp": mock_timestamp
            }
        ]

        response = self.client.get("/api/components/1234/history")
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(len(data["history"]), 1)
        self.assertEqual(data["history"][0]["pc_name"], "PC-TEST")
        self.assertEqual(data["history"][0]["timestamp"], "2026-08-04 10:30")


if __name__ == "__main__":
    unittest.main()
