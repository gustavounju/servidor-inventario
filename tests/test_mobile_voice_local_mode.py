from flask import Flask

from blueprints.bp_mobile import bp_mobile
from voice_processor import process_voice_command


def test_voice_processor_uses_local_text_mode(monkeypatch):
    monkeypatch.setenv("ENABLE_LOCAL_VOICE", "true")
    result = process_voice_command(text_command="Ya arregle la impresora de mesa de entradas, lo pidio Laura")

    assert result["mode"] == "local"
    assert result["is_done"] is True
    assert "Laura" in result["solicitante"]


def test_voice_processor_audio_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("ENABLE_LOCAL_AUDIO_UPLOAD", raising=False)
    result = process_voice_command(audio_path="dummy.wav")

    assert result["mode"] == "disabled"
    assert "deshabilitada" in result["error"]


def test_voice_upload_endpoint_returns_503_when_audio_mode_is_disabled(monkeypatch):
    monkeypatch.delenv("ENABLE_LOCAL_AUDIO_UPLOAD", raising=False)
    app = Flask(__name__)
    app.secret_key = "test_key"
    app.register_blueprint(bp_mobile)

    with app.test_client() as client:
        response = client.post("/api/mobile/voice-upload")

    assert response.status_code == 503
