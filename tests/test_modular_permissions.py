import pytest
from utils.auth import has_permission

def test_superuser_always_has_permission():
    user = {
        "username": "admin_test",
        "role": "tecnico",
        "is_superuser": True,
        "permissions": {
            "dashboard": False,
            "mobile": False
        }
    }
    assert has_permission("dashboard", user=user) is True
    assert has_permission("mobile", user=user) is True
    assert has_permission("infrastructure", user=user) is True

def test_role_preset_fallback():
    # 'tecnico' defaults: mobile=True, dashboard=False
    user = {
        "username": "tech_test",
        "role": "tecnico",
        "is_superuser": False,
        "permissions": {}
    }
    assert has_permission("mobile", user=user) is True
    assert has_permission("dashboard", user=user) is False

def test_user_permission_override_true():
    # 'operador' default: dashboard=False
    # but override dashboard=True
    user = {
        "username": "op_test",
        "role": "operador",
        "is_superuser": False,
        "permissions": {
            "dashboard": True
        }
    }
    assert has_permission("dashboard", user=user) is True
    # 'operador' default: operadores=True, and no override
    assert has_permission("operadores", user=user) is True

def test_user_permission_override_false():
    # 'administrador' default: reports=True
    # but override reports=False
    user = {
        "username": "admin_test",
        "role": "administrador",
        "is_superuser": False,
        "permissions": {
            "reports": False
        }
    }
    assert has_permission("reports", user=user) is False
    # 'administrador' default: dashboard=True
    assert has_permission("dashboard", user=user) is True

def test_empty_user():
    from servidor import app
    with app.test_request_context():
        assert has_permission("dashboard", user=None) is False

def test_required_permission_for_endpoint():
    from utils.auth import required_permission_for_endpoint
    assert required_permission_for_endpoint("maps.index") == "infrastructure"
    assert required_permission_for_endpoint("setup.view_efemerides") == "reports"
    assert required_permission_for_endpoint("dashboard.view_cementerio") == "reports"
    assert required_permission_for_endpoint("infrastructure.index") == "infrastructure"

def test_mobile_user_redirection():
    from utils.auth import auth_guard
    from flask import session
    from servidor import app
    
    with app.test_request_context(
        path="/",
        headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1"}
    ):
        import time
        session["auth_user"] = {
            "id": 1,
            "username": "usuario1",
            "role": "tecnico",
            "is_superuser": False,
            "permissions": {
                "dashboard": True,
                "mobile": True
            }
        }
        session["last_auth_refresh"] = time.time()
        res = auth_guard()
        assert res is not None
        assert res.status_code == 302
        assert "/tecnicos" in res.headers["Location"]
