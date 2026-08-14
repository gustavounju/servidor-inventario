import os
from unittest.mock import patch

from servidor import app


def _read_script_response(client):
    response = client.get("/script", headers={"Host": "192.168.1.8:5000"})
    assert response.status_code == 200
    return response.get_data(as_text=True)


def test_script_prefers_inventario_api_token():
    app.config["TESTING"] = True
    with app.test_client() as client:
        with patch.dict(
            os.environ,
            {
                "INVENTARIO_API_TOKEN": "inventario-token-real",
                "API_TOKEN": "api-token-viejo",
                "API_KEY": "api-key-vieja",
            },
            clear=True,
        ):
            script = _read_script_response(client)

    assert "inventario-token-real" in script
    assert "api-token-viejo" not in script


def test_script_falls_back_to_api_token_and_api_key():
    app.config["TESTING"] = True
    with app.test_client() as client:
        with patch.dict(os.environ, {"API_TOKEN": "api-token-activo"}, clear=True):
            script = _read_script_response(client)
            assert "api-token-activo" in script

        with patch.dict(os.environ, {"API_KEY": "api-key-activa"}, clear=True):
            script = _read_script_response(client)
            assert "api-key-activa" in script
