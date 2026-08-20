from pathlib import Path


TECHNICIANS_TEMPLATE = (
    Path(__file__).resolve().parents[1] / "templates" / "tecnicos.html"
)


def test_mobile_technicians_defaults_to_dark_command_center_theme():
    template = TECHNICIANS_TEMPLATE.read_text(encoding="utf-8")

    assert "--bg: #f5f7fb" in template
    assert "localStorage.getItem('techTheme') || 'dark'" in template
    assert 'class="home-voice-button"' in template
    assert 'id="homeMineCount"' in template
    assert 'id="homeFreeCount"' in template


def test_mobile_notifications_use_local_classic_bell():
    template = TECHNICIANS_TEMPLATE.read_text(encoding="utf-8")

    assert "function playClassicBell" in template
    assert "playClassicBell();" in template
    assert "waka.wav" not in template


def test_mobile_text_fields_explain_keyboard_dictation_fallback():
    template = TECHNICIANS_TEMPLATE.read_text(encoding="utf-8")

    assert "Podés usar el micrófono del teclado" in template


def test_mobile_has_integrated_dictation_controls_for_task_text():
    template = TECHNICIANS_TEMPLATE.read_text(encoding="utf-8")

    assert "window.SpeechRecognition || window.webkitSpeechRecognition" in template
    for target_id in ("mDesc", "mSolucion", "mobileNewTaskAction", "completeDesc", "completeSolucion"):
        assert f"startInlineDictation('{target_id}', this)" in template


def test_https_proxy_is_ready_for_internal_mobile_dictation():
    nginx = (
        TECHNICIANS_TEMPLATE.parents[1]
        / "deployment"
        / "nginx_inventario.conf"
    ).read_text(encoding="utf-8")

    assert "listen 5000 ssl;" in nginx
    assert "ssl_certificate /opt/inventario/cert.pem;" in nginx
    assert "ssl_certificate_key /opt/inventario/key.pem;" in nginx


def test_mobile_web_push_contract_is_present():
    template = TECHNICIANS_TEMPLATE.read_text(encoding="utf-8")
    service_worker = (
        TECHNICIANS_TEMPLATE.parents[1] / "static" / "sw.js"
    ).read_text(encoding="utf-8")
    push_service = (
        TECHNICIANS_TEMPLATE.parents[1] / "services" / "push_notifications.py"
    ).read_text(encoding="utf-8")
    migration = (
        TECHNICIANS_TEMPLATE.parents[1]
        / "database"
        / "migrations"
        / "002_web_push_subscriptions.sql"
    ).read_text(encoding="utf-8")

    assert "pushManager.subscribe" in template
    assert "/api/mobile/push/subscribe" in template
    assert "self.addEventListener('push'" in service_worker
    assert "showNotification" in service_worker
    assert "web_push_subscriptions" in push_service
    assert "VAPID_PRIVATE_KEY" in push_service
    assert "CREATE TABLE IF NOT EXISTS web_push_subscriptions" in migration
