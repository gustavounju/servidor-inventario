import pytest
import os
import json
from flask import Flask, jsonify
from utils.auth import require_api_scope, SCOPE_INVENTORY_SUBMIT, SCOPE_EXTERNAL_READ_PO

# Creamos una aplicación de prueba minimalista
@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True

    # Endpoint protegido con un scope específico
    @app.route("/api/test-submit", methods=["POST"])
    @require_api_scope(SCOPE_INVENTORY_SUBMIT)
    def test_submit():
        return jsonify({"status": "success", "message": "Submit OK"}), 200

    @app.route("/api/test-read", methods=["GET"])
    @require_api_scope(SCOPE_EXTERNAL_READ_PO)
    def test_read():
        return jsonify({"status": "success", "message": "Read OK"}), 200

    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """
    Configuramos tokens válidos en el entorno antes de cada test.
    """
    # INVENTARIO_API_TOKEN por defecto tiene SCOPE_INVENTORY_SUBMIT y otros.
    monkeypatch.setenv("INVENTARIO_API_TOKEN", "token-inventario-secreto")
    # CONTABLE_API_TOKEN por defecto tiene SCOPE_EXTERNAL_READ_PO, etc. pero NO inventory:submit.
    monkeypatch.setenv("CONTABLE_API_TOKEN", "token-contable-secreto")
    
    # Custom API token for admin testing via environment variables.
    monkeypatch.setenv("ADMIN_TEST_TOKEN", "token-admin-secreto")
    monkeypatch.setenv("ADMIN_TEST_TOKEN_SCOPES", "admin:*")

def test_missing_token_returns_401(client):
    """Prueba que sin token la respuesta sea 401 Unauthorized"""
    response = client.post("/api/test-submit")
    assert response.status_code == 401
    data = json.loads(response.data)
    assert "Unauthorized" in data["message"]

def test_invalid_token_returns_401(client):
    """Prueba que con token inválido la respuesta sea 401 Unauthorized"""
    headers = {"Authorization": "Bearer token-falso"}
    response = client.post("/api/test-submit", headers=headers)
    assert response.status_code == 401

def test_valid_token_without_required_scope_returns_403(client):
    """
    Prueba que si el token es válido pero no tiene el scope necesario,
    la respuesta sea 403 Forbidden.
    """
    # El token contable NO tiene SCOPE_INVENTORY_SUBMIT
    headers = {"Authorization": "Bearer token-contable-secreto"}
    response = client.post("/api/test-submit", headers=headers)
    assert response.status_code == 403
    data = json.loads(response.data)
    assert "Forbidden" in data["message"]
    assert "inventory:submit" in data["message"]

def test_valid_token_with_required_scope_returns_200(client):
    """
    Prueba que un token válido con el scope adecuado permita acceder al endpoint.
    """
    # El token contable SÍ tiene SCOPE_EXTERNAL_READ_PO
    headers = {"Authorization": "Bearer token-contable-secreto"}
    response = client.get("/api/test-read", headers=headers)
    assert response.status_code == 200

    # El token inventario SÍ tiene SCOPE_INVENTORY_SUBMIT
    headers = {"Authorization": "Bearer token-inventario-secreto"}
    response = client.post("/api/test-submit", headers=headers)
    assert response.status_code == 200

def test_admin_scope_bypasses_specific_scope_checks(client, monkeypatch):
    """
    Prueba que un token con el scope 'admin:*' pueda acceder a cualquier endpoint protegido.
    """
    # Temporarily register this test token in the default tokens mapping inside the test
    from utils import auth
    original_scopes = auth.DEFAULT_TOKEN_SCOPES.copy()
    auth.DEFAULT_TOKEN_SCOPES["ADMIN_TEST_TOKEN"] = set() # Base empty, scopes will come from ENV
    
    try:
        headers = {"Authorization": "Bearer token-admin-secreto"}
        
        # This endpoint needs SCOPE_INVENTORY_SUBMIT, but token only has admin:*
        response = client.post("/api/test-submit", headers=headers)
        assert response.status_code == 200
        
        # This endpoint needs SCOPE_EXTERNAL_READ_PO, but token only has admin:*
        response = client.get("/api/test-read", headers=headers)
        assert response.status_code == 200
    finally:
        auth.DEFAULT_TOKEN_SCOPES = original_scopes

def test_token_not_logged(client, caplog):
    """
    Prueba que el valor del token no se imprima en los logs en caso de error.
    """
    headers = {"Authorization": "Bearer token-super-secreto-que-no-debe-loguearse"}
    client.post("/api/test-submit", headers=headers)
    
    # Comprobar que el token no aparece en texto claro en los logs capturados
    for record in caplog.records:
        assert "token-super-secreto-que-no-debe-loguearse" not in record.message
