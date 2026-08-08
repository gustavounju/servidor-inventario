import unittest
from flask import Flask
from utils.api_responses import success_response, error_response

class TestApiContracts(unittest.TestCase):

    def setUp(self):
        self.app = Flask(__name__)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def test_success_response_structure(self):
        """Verifica la estructura normalizada de success_response."""
        response, status = success_response(data={"item": 123}, message="OK", status_code=200)
        self.assertEqual(status, 200)
        json_data = response.get_json()
        self.assertEqual(json_data.get("status"), "success")
        self.assertEqual(json_data.get("data"), {"item": 123})
        self.assertEqual(json_data.get("message"), "OK")

    def test_error_response_structure(self):
        """Verifica la estructura normalizada de error_response."""
        response, status = error_response(code="VALIDATION_ERROR", message="Campo invalido", details={"field": "name"}, status_code=422)
        self.assertEqual(status, 422)
        json_data = response.get_json()
        self.assertEqual(json_data.get("status"), "error")
        err = json_data.get("error", {})
        self.assertEqual(err.get("code"), "VALIDATION_ERROR")
        self.assertEqual(err.get("message"), "Campo invalido")
        self.assertEqual(err.get("details"), {"field": "name"})

if __name__ == '__main__':
    unittest.main()
