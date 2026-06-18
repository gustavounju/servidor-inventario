import pytest
import os
import sys

# Asegurar que el directorio raíz está en el path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from servidor import app as flask_app

@pytest.fixture
def app():
    # Forzar modo testing
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "LOGIN_DISABLED": True  # Deshabilitar login para endpoints públicos por ahora
    })
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
