import pytest
from utils.auth import PUBLIC_ENDPOINTS, is_public_endpoint

def test_rack_endpoints_are_public():
    """Verifica que los endpoints requeridos por el visor público estén en la lista blanca."""
    assert "api.api_get_racks_status" in PUBLIC_ENDPOINTS
    assert "infrastructure.rack_audits_history" in PUBLIC_ENDPOINTS
    assert "tasks.visor" in PUBLIC_ENDPOINTS


def test_pwa_assets_are_public():
    """El service worker debe servirse sin redirecciones para que el navegador lo registre."""
    assert "serve_sw" in PUBLIC_ENDPOINTS
    assert "serve_manifest" in PUBLIC_ENDPOINTS
