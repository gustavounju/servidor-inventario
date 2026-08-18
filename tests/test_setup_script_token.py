import os
from unittest.mock import patch

from servidor import app
from blueprints.bp_setup import _get_secure_launcher_command, build_inventory_script_access_url
from utils.auth import generate_inventory_script_download_token, generate_inventory_submit_token
from utils.runtime_urls import get_public_app_base_url


def _login_as_mobile_user(client):
    with client.session_transaction() as sess:
        sess["auth_user"] = {
            "id": 1,
            "username": "tecnico",
            "display_name": "Tecnico",
            "role": "tecnico",
            "technician_name": "Tecnico",
            "permissions": {
                "mobile": True,
                "dashboard": False,
                "infrastructure": False,
                "reports": False,
                "operadores": False,
                "audit_racks": False,
                "manage_stock": False,
                "funcionario": False,
                "can_manage_stock": False,
            },
            "is_superuser": False,
            "must_change_password": False,
            "is_active": True,
            "phone": "",
            "auth_source": "local",
        }


def _read_script_response(client, query_string=None):
    response = client.get("/script", headers={"Host": "192.168.1.8:5000"}, query_string=query_string or {})
    assert response.status_code == 200
    return response.get_data(as_text=True)


def test_script_requires_authenticated_session_or_download_token():
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/script", headers={"Host": "192.168.1.8:5000"})
    assert response.status_code == 403


def test_script_uses_bearer_header_and_not_query_token():
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            submit_token = generate_inventory_submit_token(issued_for="PC-01", issued_by="tester")
            download_token = generate_inventory_script_download_token(issued_for="PC-01", issued_by="tester")
        with patch.dict(
            os.environ,
            {
                "INVENTARIO_API_TOKEN": "inventario-token-real",
                "API_TOKEN": "api-token-viejo",
                "API_KEY": "api-key-vieja",
            },
            clear=False,
        ):
            script = _read_script_response(
                client,
                query_string={
                    "download_token": download_token,
                    "submit_token": submit_token,
                },
            )

    assert "?api_key=" not in script
    assert "Headers.Add(\"Authorization\", \"Bearer " in script
    assert "inventario-token-real" not in script
    assert "api-token-viejo" not in script


def test_script_accepts_short_lived_download_token():
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            submit_token = generate_inventory_submit_token(issued_for="PC-01", issued_by="tester")
            download_token = generate_inventory_script_download_token(issued_for="PC-01", issued_by="tester")
        script = _read_script_response(
            client,
            query_string={
                "download_token": download_token,
                "submit_token": submit_token,
            },
        )

    assert "Headers.Add(\"Authorization\", \"Bearer " in script


def test_install_page_secure_command_no_longer_disables_tls_validation():
    app.config["TESTING"] = True
    with app.test_request_context("/install", base_url="https://192.168.1.8:5000"):
        body = _get_secure_launcher_command("https://192.168.1.8:5000", "http://192.168.1.8:8080")
    assert "CertificatePolicy" not in body
    assert "TrustAllCertsPolicy" not in body
    assert "download-cert" in body
    assert "Import-Certificate" in body


def test_install_page_http_mode_uses_compatibility_command_without_cert_bootstrap():
    app.config["TESTING"] = True
    with app.test_request_context("/install", base_url="http://192.168.1.8:8080"):
        body = _get_secure_launcher_command("http://192.168.1.8:8080", "http://192.168.1.8:8080")
    assert "Import-Certificate" not in body
    assert "download-cert" not in body
    assert "Hash OK en modo compatibilidad." in body
    assert "http://192.168.1.8:8080/script" in body


def test_public_app_base_url_respects_forwarded_proto_and_port():
    app.config["TESTING"] = True
    with app.test_request_context(
        "/install",
        base_url="http://127.0.0.1/",
        headers={"X-Forwarded-Proto": "http", "X-Forwarded-Host": "10.15.2.251:8080"},
    ):
        assert get_public_app_base_url() == "http://10.15.2.251:8080"


def test_build_inventory_script_access_url_embeds_short_lived_tokens():
    app.config["TESTING"] = True
    with app.test_request_context("/install", base_url="https://10.15.2.251:5000"):
        url = build_inventory_script_access_url()
    assert url.startswith("/script?")
    assert "download_token=" in url
    assert "submit_token=" in url
