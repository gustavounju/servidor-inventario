import unittest
from flask import Flask
from blueprints.bp_api import bp_api

class TestHealthCheck(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app.register_blueprint(bp_api, url_prefix='/api')
        self.client = self.app.test_client()

    def test_health_check_endpoint(self):
        """Verifica que /api/health responda con un JSON válido y status success o error."""
        res = self.client.get('/api/health')
        self.assertIn(res.status_code, [200, 503])
        data = res.get_json()
        self.assertIsNotNone(data)
        self.assertIn(data.get("status"), ["success", "error"])

if __name__ == '__main__':
    unittest.main()
