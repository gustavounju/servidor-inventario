import os
import platform

from flask import request


def _normalize_url(url):
    return (url or "").strip().rstrip("/")


def get_public_app_base_url():
    configured = _normalize_url(os.environ.get("INVENTARIO_PUBLIC_BASE_URL", ""))
    if configured:
        return configured

    current_host = request.host.split(":")[0]
    scheme = "http" if platform.system() == "Windows" else "https"
    return f"{scheme}://{current_host}:5000"


def get_public_script_fallback_url():
    configured = _normalize_url(os.environ.get("INVENTARIO_PUBLIC_HTTP_FALLBACK_URL", ""))
    if configured:
        return configured

    current_host = request.host.split(":")[0]
    return f"http://{current_host}:8080"
