import pytest

from utils.crypto import get_required_flask_secret_key


def test_required_flask_secret_key_accepts_configured_env(monkeypatch):
    monkeypatch.setenv("FLASK_SECRET_KEY", "clave-real-de-prueba")
    monkeypatch.delenv("SECRET_KEY", raising=False)

    assert get_required_flask_secret_key() == "clave-real-de-prueba"


def test_required_flask_secret_key_accepts_legacy_secret_key_env(monkeypatch):
    monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)
    monkeypatch.setenv("SECRET_KEY", "clave-legacy-de-prueba")

    assert get_required_flask_secret_key() == "clave-legacy-de-prueba"


def test_required_flask_secret_key_fails_when_env_is_missing(monkeypatch):
    monkeypatch.delenv("FLASK_SECRET_KEY", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(RuntimeError, match="FLASK_SECRET_KEY"):
        get_required_flask_secret_key()
