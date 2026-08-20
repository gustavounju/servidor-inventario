from pathlib import Path


TECHNICIANS_TEMPLATE = (
    Path(__file__).resolve().parents[1] / "templates" / "tecnicos.html"
)


def test_mobile_technicians_defaults_to_clear_classic_theme():
    template = TECHNICIANS_TEMPLATE.read_text(encoding="utf-8")

    assert "--bg: #f5f7fb" in template
    assert "localStorage.getItem('techTheme') || 'default'" in template


def test_mobile_notifications_use_local_classic_bell():
    template = TECHNICIANS_TEMPLATE.read_text(encoding="utf-8")

    assert "function playClassicBell" in template
    assert "playClassicBell();" in template
    assert "waka.wav" not in template


def test_mobile_text_fields_explain_keyboard_dictation_fallback():
    template = TECHNICIANS_TEMPLATE.read_text(encoding="utf-8")

    assert "Podés usar el micrófono del teclado" in template
