import json

import pytest
from flask import Flask, jsonify

from utils.auth import (
    SCOPE_EXTERNAL_READ_PO,
    SCOPE_INVENTORY_SUBMIT,
    generate_inventory_submit_token,
    require_api_scope,
)


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.config["SECRET_KEY"] = "test-secret-key"

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
    monkeypatch.setenv("FLASK_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("INVENTARIO_API_TOKEN", "token-inventario-secreto")
    monkeypatch.setenv("CONTABLE_API_TOKEN", "token-contable-secreto")
    monkeypatch.setenv("APP_ADMIN_API_TOKEN", "token-admin-secreto")
    monkeypatch.delenv("ALLOW_LEGACY_INVENTORY_STATIC_TOKEN", raising=False)


def test_missing_token_returns_401(client):
    response = client.post("/api/test-submit")
    assert response.status_code == 401
    data = json.loads(response.data)
    assert "Unauthorized" in data["message"]


def test_invalid_token_returns_401(client):
    response = client.post("/api/test-submit", headers={"Authorization": "Bearer token-falso"})
    assert response.status_code == 401


def test_legacy_inventory_token_is_disabled_by_default(client):
    response = client.post("/api/test-submit", headers={"Authorization": "Bearer token-inventario-secreto"})
    assert response.status_code == 401


def test_legacy_inventory_token_can_be_enabled_explicitly(client, monkeypatch):
    monkeypatch.setenv("ALLOW_LEGACY_INVENTORY_STATIC_TOKEN", "true")
    response = client.post("/api/test-submit", headers={"Authorization": "Bearer token-inventario-secreto"})
    assert response.status_code == 200


def test_valid_token_without_required_scope_returns_403(client):
    response = client.post("/api/test-submit", headers={"Authorization": "Bearer token-contable-secreto"})
    assert response.status_code == 403
    data = json.loads(response.data)
    assert "Forbidden" in data["message"]
    assert "inventory:submit" in data["message"]


def test_valid_token_with_required_scope_returns_200(client):
    response = client.get("/api/test-read", headers={"Authorization": "Bearer token-contable-secreto"})
    assert response.status_code == 200


def test_ephemeral_inventory_token_returns_200(client, app):
    with app.app_context():
        token = generate_inventory_submit_token(issued_for="PC-01", issued_by="tester")
    response = client.post("/api/test-submit", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200


def test_admin_scope_bypasses_specific_scope_checks(client):
    headers = {"Authorization": "Bearer token-admin-secreto"}
    response = client.post("/api/test-submit", headers=headers)
    assert response.status_code == 200
    response = client.get("/api/test-read", headers=headers)
    assert response.status_code == 200


def test_token_not_logged(client, caplog):
    headers = {"Authorization": "Bearer token-super-secreto-que-no-debe-loguearse"}
    client.post("/api/test-submit", headers=headers)
    for record in caplog.records:
        assert "token-super-secreto-que-no-debe-loguearse" not in record.message
