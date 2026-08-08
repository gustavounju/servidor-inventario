import pytest
import os
from unittest.mock import patch
from servidor import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    with app.test_client() as client:
        yield client

def test_submit_inventory_rejects_missing_or_default_token(client):
    """Verifica que /submit_inventory rechace solicitudes sin token o con el valor por defecto."""
    with patch.dict(os.environ, {}, clear=True):
        # Petición sin token
        res_no_token = client.post('/submit_inventory', json={"PC_Nombre": "TEST-PC"})
        assert res_no_token.status_code == 401
        
        # Petición con el antiguo token por defecto super-secret-token
        res_default_token = client.post(
            '/submit_inventory',
            headers={"Authorization": "Bearer super-secret-token"},
            json={"PC_Nombre": "TEST-PC"}
        )
        assert res_default_token.status_code == 401

def test_submit_inventory_accepts_valid_configured_token(client):
    """Verifica que /submit_inventory acepte el token configurado en API_TOKEN."""
    with patch.dict(os.environ, {"API_TOKEN": "valid-token-123456"}):
        res = client.post(
            '/submit_inventory',
            headers={"Authorization": "Bearer valid-token-123456"},
            json={"PC_Nombre": "NON_EXISTENT_TEST_PC_99"}
        )
        # Debe responder 200 o procesar la ingesta
        assert res.status_code in (200, 400)
        assert res.status_code != 401

def test_ldap_escape_filter_chars():
    """Verifica que el escape de filtros LDAP funcione correctamente."""
    from ldap3.utils.conv import escape_filter_chars
    
    input_user = "admin)(sAMAccountName=*"
    escaped = escape_filter_chars(input_user)
    
    assert "(" not in escaped or "\\28" in escaped
    assert ")" not in escaped or "\\29" in escaped
    assert "*" not in escaped or "\\2a" in escaped
    assert escaped != input_user

def test_vault_delete_file_rejects_get(client):
    """Verifica que la ruta /recursos_internos/delete no acepte peticiones GET (405 Method Not Allowed)."""
    res = client.get('/recursos_internos/delete/test_file.txt')
    assert res.status_code == 405

def test_is_vault_authorized_logic():
    """Verifica la lógica de autorización de Vault para superusuarios y administradores."""
    from utils.auth import current_user
    from blueprints.bp_vault import is_vault_authorized

    admin_user = {"username": "admin_test", "role": "administrador", "is_superuser": True}
    with patch("blueprints.bp_vault.current_user", return_value=admin_user):
        assert is_vault_authorized("admin_test") is True

    normal_user = {"username": "user_test", "role": "tecnico", "is_superuser": False, "permissions": {}}
    with patch("blueprints.bp_vault.current_user", return_value=normal_user):
        assert is_vault_authorized("user_test") is False
